"""
SnakrAWS URL Configuration
"""

from django.http import HttpResponse
from django.urls import re_path
from django.views.decorators.csrf import csrf_exempt

from snakraws import views

urlpatterns = [
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    #re_path(r'^shortn$', csrf_exempt(views.shortnr)),
    re_path(r'^.*', csrf_exempt(views.request_handler)),
]
