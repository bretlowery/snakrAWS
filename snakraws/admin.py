from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from snakraws import settings, models

admin.site.site_header = getattr(settings, "VERBOSE_NAME", _("SnakrAWS"))
admin.site.site_title = _("%s Admin Portal") % admin.site.site_header
admin.site.index_title = _("Welcome to the %s") % admin.site.site_title

