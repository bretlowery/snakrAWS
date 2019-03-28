'''
views.py contains the get and post handler logic.
'''

import json

from django.template import RequestContext
from django.shortcuts import render
from django.http import HttpResponsePermanentRedirect, Http404, HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext_lazy as _
from django.forms.forms import NON_FIELD_ERRORS
from django.contrib.auth.decorators import login_required

from snakraws import settings
from snakraws.shorturls import ShortURL
from snakraws.longurls import LongURL
from snakraws.parsers import Parsers
from snakraws.forms import ShortForm
from snakraws.utils import get_message


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
    longurl = s.get_long(request)
    #
    # if found, 302 to it; otherwise, 404
    #
    if longurl:
        if longurl[0]:
            return HttpResponsePermanentRedirect(longurl[0])
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

    #
    # Restrict new short url creation to admins
    # Outside offworlders will get a 404 on POST
    #
    # user = users.get_current_user()
    # # raise SuspiciousOperation(str(user))
    # if user:
    #     if not users.is_current_user_admin():
    #         raise Http404
    # else:
    #     raise Http404
    #
    # check for unfriendly bot first
    #
    #self._botdetector.get_useragent_or_403_if_bot(request)
    #
    # create an instance of the LongURLs object, validate the long URL, and if successful load the LongURLs instance with it
    #
    l = LongURL(request, lu=lu, vp=vp)
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
    # get document title if possible
    #
    p = Parsers()
    title = p.get_title(l.longurl)
    #
    # make response data
    #
    response_data['message'] = msg
    response_data['shorturl'] = shorturl
    response_data['title'] = title
    if title:
        ls = len(shorturl)
        lt = len(title)
        ltmax = 140 - ls - 1
        if lt > ltmax:
            socialmediapost = title[:ltmax - 3] + '... ' + shorturl
        else:
            socialmediapost = title + ' ' + shorturl
        response_data['socialmediapost'] = socialmediapost
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
    form = ShortForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            response_data = ""
            try:
                response_data = post_handler(request, form=form)
                message = response_data["message"][27:]
                shorturl = response_data["shorturl"]
            except Exception as e:
                form.add_error(NON_FIELD_ERRORS, str(e))
                pass

    title = getattr(settings, "PAGE_TITLE", settings.VERBOSE_NAME)
    heading = getattr(settings, "PAGE_HEADING", settings.VERBOSE_NAME)
    sitekey = getattr(settings, "RECAPTCHA_PUBLIC_KEY", "")
    submit_label = _("Shorten It")
    return render(
            request,
            'shorten_url.html',
            {
                'form': form,
                'title': title,
                'heading': heading,
                'submit_label': submit_label,
                'message': message,
                'shorturl': shorturl,
                'sitekey': sitekey,
                'action': 'shorten_url',
            }
    )
