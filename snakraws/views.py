'''
views.py contains the get and post handler logic.
'''

import json

from django.template import RequestContext
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.decorators import login_required

from snakraws import settings
from snakraws.shorturls import ShortURL
from snakraws.longurls import LongURL
from snakraws.forms import ShortForm
from snakraws.utils import get_message, get_json, fit_text
from snakraws.__init__ import VERSION


def homepage(request, template_name="homepage.html"):
    return render(request, template_name, RequestContext(request))


def request_handler(request):
    if request.method == "POST":
        return post_handler(request)
    elif request.method == "GET":
        return get_handler(request)
    else:
        return HttpResponseBadRequest(get_message("MALFORMED_REQUEST"))


def get_handler(request):
    #
    # create an instance of the ShortURLs object, validate the short URL,
    # and if successful load the ShortURLs instance with it
    #
    s = ShortURL(request)
    #
    # lookup the long url previously used to generate the short url
    #
    l, redirect_status_code = s.get_long(request)
    #
    # if found, redirect to it; otherwise, 404
    #
    if l:
        public_name = getattr(settings, "PUBLIC_NAME", getattr(settings, "VERBOSE_NAME", "SnakrAWS"))
        public_version = VERSION
        ga_enabled = getattr(settings, "ENABLE_GOOGLE_ANALYTICS", False)
        ga_id = getattr(settings, "GOOGLE_ANALYTICS_WEB_PROPERTY_ID", "")
        return render(
                request,
                'redirectr.html',
                {
                    'ga_enabled': ga_enabled,
                    'ga_id': ga_id,
                    'image_url': l.image_url,
                    'inpage': l.description,
                    'longurl': l.longurl,
                    'longurl_byline': l.byline,
                    'longurl_description': l.description,
                    'longurl_site_name': l.site_name,
                    'longurl_title': l.title,
                    'shorturl': s.normalized_shorturl,
                    'status_code': redirect_status_code,
                    'verbose_name': public_name,
                    'version': public_version,
                }
        )

    return Http404


def post_handler(request, **kwargs):
    lu = None
    vp = None
    form = kwargs.pop('form', None)
    if form:
        if "longurl" in form.cleaned_data:
            lu = form.cleaned_data["longurl"]
        if "vanityurl" in form.cleaned_data:
            vp = form.cleaned_data["vanityurl"]
        if "byline" in form.cleaned_data:
            bl = form.cleaned_data["byline"]
        if "description" in form.cleaned_data:
            de = form.cleaned_data["description"]
    elif getattr(settings, 'SITE_MODE', 'prod') != 'dev':
        # disabling api for security reasons until OAuth is implemented for it
        return HttpResponseForbidden(_("Invalid Request"))
    #
    # create an instance of the LongURLs object, validate the long URL, and if successful load the LongURLs instance with it
    #
    l = LongURL(request, lu=lu, vp=vp, bl=bl, de=de)
    #
    # generate the shorturl and either persist both the long and short urls if new,
    # or lookup the matching short url if it already exists (i.e. the long url was submitted a 2nd or subsequent time)
    #
    shorturl, msg = l.get_or_make_short(request)
    #
    # prepare to return the shorturl as JSON
    #
    response_data = {}
    #
    # make response data
    #
    response_data['byline'] = l.byline
    response_data['description'] = l.meta.description
    response_data['image_url'] = l.meta.image_url
    response_data['message'] = msg
    response_data['shorturl'] = shorturl
    response_data['title'] = l.meta.title
    #
    #
    #
    if form:
        return response_data
    else:
        #
        # return meta tag values as well if requested
        #
        if settings.RETURN_ALL_META:
            j = json.JSONEncoder()
            for key, value in request.META.items():
                if isinstance(key, (list, dict, str, int, float, bool, type(None))):
                    try:
                        response_data[key] = j.encode(value)
                    except:
                        response_data[key] = 'nonserializable'
        #
        # return JSON to caller
        #
        return HttpResponse(json.dumps(response_data), content_type="application/json")


def test_post_handler(request, *args, **kwargs):
    return HttpResponse("<H2>Test value: {%s}</H2>", content_type="text/html")


@login_required
def form_handler(request, *args, **kwargs):
    message = ""
    shorturl = ""
    post_title = ""
    post_description = ""
    post_image_url = ""
    post_byline = ""
    form = ShortForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            response_data = []
            try:
                response_data = post_handler(request, form=form)
                message = response_data["message"][27:]
                shorturl = response_data["shorturl"]
                post_title = response_data["title"]
                post_description = response_data["description"]
                post_image_url = response_data["image_url"]
                post_byline = response_data["byline"]
            except Exception as e:
                form.add_error(NON_FIELD_ERRORS, str(e))
                pass

    debug = getattr(settings, "DEBUG", False)
    title = getattr(settings, "PAGE_TITLE", settings.VERBOSE_NAME)
    heading = getattr(settings, "PAGE_HEADING", settings.VERBOSE_NAME)
    sitekey = getattr(settings, "RECAPTCHA_PUBLIC_KEY", "")
    submit_label = _("Shorten It")
    action = _("shorten_url")
    return render(
            request,
            'shorten_url.html',
            {
                'action': action,
                'debug': debug,
                'form': form,
                'heading': heading,
                'message': message,
                'post_byline': post_byline,
                'post_description': post_description,
                'post_image_url': post_image_url,
                'post_title': post_title,
                'shorturl': shorturl,
                'sitekey': sitekey,
                'title': title,
                'submit_label': submit_label,
            }
    )


def api_handler(request):
    if request.method == "POST":
        if get_json(request, 'lu'):
            return post_handler(request)
    return HttpResponseForbidden(_("Invalid Request"))

