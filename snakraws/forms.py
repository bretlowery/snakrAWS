import re

from django import forms
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from snakraws.models import LongURLs
from snakraws.utils import get_message


class ShortForm(forms.ModelForm):
    longurl = forms.URLField(
            max_length=1024,
            required=True,
            label=_('Long URL to shorten:')
    )
    vanityurl = forms.CharField(
            max_length=40,
            required=False,
            label=_('Vanity path to apply, if any:')
    )
    byline = forms.CharField(
            max_length=300,
            required=False,
            label=_('Custom byline to use, if any:')
    )
    description = forms.CharField(
            max_length=4096,
            required=False,
            label=_('Custom description to use, if any:')
    )
    # captcha = SnakrReCaptchaField()
    #
    # ALWAYS keep 'frauddetector' field last; put any new fields above it here
    frauddetector = forms.IntegerField(
            widget=forms.HiddenInput(),
            required=False
    )

    class Meta:
        model = LongURLs
        # ALWAYS keep 'frauddetector' last; put any new fields before it here
        fields = ('longurl', 'vanityurl', 'byline', 'description', 'frauddetector')

    def clean_longurl(self):
        lu = self.cleaned_data['longurl'].strip()
        return lu

    def clean_vanityurl(self):
        vu = self.cleaned_data['vanityurl'].strip()
        if len(vu) > 0:
            if len(vu) < 3 or not re.match(r'[\w-]*$', vu):
                msg = get_message("VANITY_PATH_INVALID")
                raise ValidationError(msg % (vu, 3))
        return vu

    def clean_byline(self):
        bl = self.cleaned_data['byline'].strip()
        return bl

    def clean_description(self):
        d = self.cleaned_data['description'].strip()
        if 0 < len(d) < 100:
            msg = get_message("DESCRIPTION_INVALID")
            raise ValidationError(msg)
        return d
