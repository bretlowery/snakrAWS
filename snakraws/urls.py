"""
SnakrAWS URL Configuration
"""

from django.contrib import admin
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from snakraws import settings, views
from snakraws.utils import get_shortening_postback, get_admin_postback

shortening_postback = get_shortening_postback()
admin_postback = get_admin_postback()

urlpatterns = [
    re_path(r'^ads.txt$', lambda r: HttpResponse("# no ads just snaks", content_type="text/plain")),
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    re_path(admin_postback, admin.site.urls),
    re_path(shortening_postback, views.form_handler, name="form_handler"),
    re_path(r'^$', lambda r: HttpResponsePermanentRedirect(getattr(settings, "INDEX_HTML", "http://www.google.com"), content_type="text/html")),
    re_path(r'^.*$', csrf_exempt(views.request_handler)),
]
