from snowpenguin.django.recaptcha3 import fields

import logging
import os
import requests

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import SuspiciousOperation

from snakraws.settings import CANONICAL_MESSAGES

logger = logging.getLogger(__name__)


class SnakrReCaptchaField(fields.ReCaptchaField):

    def __init__(self, attrs=None, *args, **kwargs):
        super().__init__(attrs, *args, **kwargs)

    def clean(self, values):

        # Disable the check if we run a test unit
        if os.environ.get('RECAPTCHA_DISABLE', None) is not None:
            return values[0]

        #super(fields.ReCaptchaField, self).clean(values[0])
        response_token = values[0]

        try:
            r = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    {
                        'secret': self._private_key,
                        'response': response_token
                    },
                    timeout=5
            )
            r.raise_for_status()
        except requests.RequestException as e:
            logger.exception(e)
            raise ValidationError(
                    CANONICAL_MESSAGES["RECAPTCHA_EXCEPTION"],
                    code='connection_failed'
            )

        json_response = r.json()

        logger.debug("Response from reCaptcha server: %s", json_response)
        if bool(json_response['success']):
            if self._score_threshold is not None and self._score_threshold > json_response['score']:
                raise SuspiciousOperation(CANONICAL_MESSAGES["RECAPTCHA_LOW_SCORE"])
            return values[0]
        else:
            if 'error-codes' in json_response:
                if 'missing-input-secret' in json_response['error-codes'] or \
                        'invalid-input-secret' in json_response['error-codes']:

                    logger.exception('Invalid reCaptcha secret key detected')
                    raise ValidationError(
                            CANONICAL_MESSAGES["RECAPTCHA_EXCEPTION"],
                            code='invalid_secret',
                    )
                else:
                    raise ValidationError(
                            CANONICAL_MESSAGES["RECAPTCHA_EXPIRED"],
                            code='expired',
                    )
            else:
                logger.exception('No error-codes received from Google reCaptcha server')
                raise ValidationError(
                        CANONICAL_MESSAGES["RECAPTCHA_EXCEPTION"],
                        code='invalid_response',
                )
