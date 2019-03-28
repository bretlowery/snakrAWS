"""
SnakrAWS URL Configuration
"""

from django.contrib import admin
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django.urls import re_path, include, path
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.views import LoginView, LogoutView

from snakraws import settings, views
from snakraws.utils import get_shortening_postback, get_admin_postback, get_jet_postback, get_jet_dashboard_postback, get_shortening_redirect

title = getattr(settings, "PAGE_TITLE", settings.VERBOSE_NAME)
heading = getattr(settings, "PAGE_HEADING", settings.VERBOSE_NAME)
extra_context = {'title': title, 'heading': heading}

urlpatterns = [
    re_path(r'^ads.txt$', lambda r: HttpResponse("# no ads just snaks", content_type="text/plain")),
    re_path(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")),
    re_path(get_jet_postback(), include('jet.urls', 'jet')),
    re_path(get_jet_dashboard_postback(), include('jet.dashboard.urls', 'jet-dashboard')),
    re_path(get_admin_postback(), admin.site.urls),
    re_path(get_shortening_postback(), views.form_handler, name="form_handler"),
    re_path(r'^accounts/login/$', LoginView.as_view(template_name='login.html', extra_context=extra_context), name="login"),
    re_path(r'^accounts/logout/$', LogoutView.as_view(template_name='logout.html', extra_context=extra_context), name="logout"),
    re_path(r'^accounts/profile/$', lambda r: HttpResponsePermanentRedirect(get_shortening_redirect(), content_type="text/html")),
    re_path(r'^$', lambda r: HttpResponsePermanentRedirect(getattr(settings, "INDEX_HTML", "http://www.linkedin.com/in/bretlowery"), content_type="text/html")),
    re_path(r'^.*$', csrf_exempt(views.request_handler)),
]
