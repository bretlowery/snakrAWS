"""
SnakrAWS URL Configuration
"""

from django.contrib import admin
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.urls import re_path, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic.base import RedirectView

from snakraws import settings, views
from snakraws.utils import get_shortening_postback, get_admin_postback, get_jet_postback, get_jet_dashboard_postback, get_shortening_redirect

index_html = getattr(settings, "INDEX_HTML", "http://www.linkedin.com/in/bretlowery")
title = getattr(settings, "PAGE_TITLE", settings.VERBOSE_NAME)
heading = getattr(settings, "PAGE_HEADING", settings.VERBOSE_NAME)
sitekey = getattr(settings, "RECAPTCHA_PUBLIC_KEY", "")
ga_id = getattr(settings, "GOOGLE_ANALYTICS_WEB_PROPERTY_ID", "")
login_extra_context = {'title': title, 'heading': heading, 'sitekey': sitekey, 'action': 'login', 'ga_id': ga_id}
logout_extra_context = {'title': title, 'heading': heading, 'ga_id': ga_id}
favicon_path = getattr(settings, "STATIC_URL", "/static/") + 'favicon.ico'

urlpatterns = [
    re_path(r'^favicon.ico$', RedirectView.as_view(url=favicon_path)),
    re_path(r'^$', lambda r: HttpResponsePermanentRedirect(index_html, content_type="text/html")),
    re_path(r'^ads.txt$', lambda r: HttpResponse("# no ads just snaks", content_type="text/plain")),
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    re_path(get_jet_postback(), include('jet.urls', 'jet')),
    re_path(get_jet_dashboard_postback(), include('jet.dashboard.urls', 'jet-dashboard')),
    re_path(get_admin_postback(), admin.site.urls),
    re_path(get_shortening_postback(), views.form_handler, name="form_handler"),
    re_path(r'^accounts/login/$', LoginView.as_view(template_name='login.html', extra_context=login_extra_context), name="login"),
    re_path(r'^accounts/logout/$', LogoutView.as_view(template_name='logout.html', extra_context=logout_extra_context), name="logout"),
    re_path(r'^accounts/profile/$', lambda r: HttpResponsePermanentRedirect(get_shortening_redirect(), content_type="text/html")),
    re_path(r'^api/$', csrf_exempt(views.api_handler), name="api_handler"),
    re_path(r'^api$', csrf_exempt(views.api_handler), name="api_handler"),
    re_path(r'^.*$', csrf_exempt(views.request_handler)),
]
