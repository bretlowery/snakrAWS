import re

from django import forms
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from snakraws import settings
from snakraws.models import LongURLs
from snakraws.utils import get_message

from snakraws.fields import SnakrReCaptchaField


class ShortForm(forms.ModelForm):
    longurl = forms.URLField(
            max_length=1024,
            required=True,
            label=_('Long URL to shorten         :')
    )
    vanityurl = forms.CharField(
            max_length=40,
            required=False,
            label=_('Vanity path to apply, if any:')
    )
    captcha = SnakrReCaptchaField()

    class Meta:
        model = LongURLs
        fields = ('longurl',)

    def clean_longurl(self):
        lu = self.cleaned_data['longurl'].strip()
        return lu

    def clean_vanityurl(self):
        vu = self.cleaned_data['vanityurl'].strip()
        if len(vu) > 0:
            min_len = getattr(settings, "SHORTURL_PATH_SIZE", 6)
            if len(vu) < min_len or not re.match(r'[\w-]*$', vu):
                msg = get_message("VANITY_PATH_INVALID")
                raise ValidationError(msg % (vu, min_len))
        return vu
