'''
ShortURLs.py contains the logic necessary to take a short URL and redirect to its long URL equivalent. It also contains the logic
needed to construct a short URL when a long URL is submitted to Snakr.
'''

from urllib.parse import urlparse, urlunparse
from django.db import transaction as xaction

from snakraws import settings
from snakraws.persistence import SnakrLogger
from snakraws.security import get_useragent_or_403_if_bot
from snakraws.models import ShortURLs, LongURLs
from snakraws.utils import get_shortpathcandidate, get_shorturlhash, get_decodedurl, get_host, get_referer, is_url_valid, is_shortpath_valid


class ShortURL:
    """Validates and processes the short URL in the GET request."""

    def __init__(self, request, *args, **kwargs):
        self.event = SnakrLogger()
        bot_name, self.useragent = get_useragent_or_403_if_bot(request)
        if bot_name:
            raise self.event.log(
                    request=request,
                    event_type='B',
                    messagekey='ROBOT',
                    value='Known Bot {%}' % bot_name,
                    status_code=-403)
        try:
            self.host = get_host(request, False)
            self.referer = get_referer(request, False)
        except Exception as e:
            raise self.event.log(
                    messagekey='REQUEST_INVALID',
                    status_code=400,
                    request=None,
                    message=str(e))

        self.shorturl = None
        self.shorturl_is_preencoded = False
        self.normalized_shorturl = None
        self.normalized_shorturl_scheme = None
        self.hash = None
        self.id = -1
        return

    def make_short(self, normalized_longurl_scheme, vanity_path):
        #
        # Make a new short URL
        #
        # 1. Build the front of the short url. Match the scheme to the one used by the longurl.
        #    This is done so that a http longurl --> http shorturl, and a https long url --> https short url.
        #
        if settings.SITE_MODE == 'dev':
            normalized_longurl_scheme = normalized_longurl_scheme.replace('s', '')
        if normalized_longurl_scheme in ('https', 'ftps', 'sftp'):
            shorturl_prefix = normalized_longurl_scheme + '://' + settings.SECURE_SHORTURL_HOST + '/'
        else:
            shorturl_prefix = normalized_longurl_scheme + '://' + settings.SHORTURL_HOST + '/'
        #
        # 2. Make a short url.
        #    a. If vanity_path was passed, use it; otherwise:
        #    b. If no vanity path was passed, build a path with SHORTURL_PATH_SIZE characters from SHORTURL_PATH_ALPHABET.
        #    c. Does it exist already? If so, regenerate it and try again.
        #
        if vanity_path:
            vp = vanity_path.strip()
            if vp:
                if not is_shortpath_valid(vp):
                    shorturl_candidate = shorturl_prefix + vp
                    raise self.event.log(
                            messagekey='SHORT_PATH_INVALID',
                            value=shorturl_candidate,
                            status_code=400)
                shorturl_candidate = shorturl_prefix + vp
            else:
                shorturl_candidate = shorturl_prefix + get_shortpathcandidate()
        else:
            shorturl_candidate = shorturl_prefix + get_shortpathcandidate()
        if not is_url_valid(shorturl_candidate):
            raise self.event.log(
                    messagekey='SHORT_URL_INVALID',
                    value=shorturl_candidate,
                    status_code=400)
        shash = get_shorturlhash(shorturl_candidate)
        s = ShortURLs.objects.filter(hash=shash)
        sc = s.count()
        if sc != 0:
            raise self.event.log(
                    messagekey='VANITY_PATH_EXISTS',
                    status_code=400)
        #
        # 3. SUCCESS! Complete it and return it as a ****decoded**** url (which it is at this point)
        #
        self.shorturl = shorturl_candidate
        self.normalized_shorturl = self.shorturl
        self.normalized_shorturl_scheme = normalized_longurl_scheme
        self.hash = shash
        return self.normalized_shorturl

    @xaction.atomic
    def get_long(self, request):
        #
        # cleanse the passed short url
        #
        surl = request.build_absolute_uri()
        dsurl = get_decodedurl(surl)
        sparts = urlparse(dsurl)
        if surl == dsurl:
            preencoded = False
        else:
            preencoded = True
            l = dsurl
        self.normalized_shorturl_scheme = sparts.scheme.lower()
        self.shorturl_is_preencoded = preencoded
        self.normalized_shorturl = urlunparse(sparts)
        if self.normalized_shorturl.endswith("/"):
            self.normalized_shorturl = self.normalized_shorturl[:-1]
        self.shorturl = surl
        if self.shorturl.endswith("/"):
            self.shorturl = self.shorturl[:-1]
        #
        # If no path provided, redirect to the defined index.html
        #
        if sparts.path == '/':
            return settings.INDEX_HTML
        #
        # Was the shorturl encoded or malcoded? If so, don't trust it.
        #
        if self.shorturl != self.normalized_shorturl:
            raise self.event.log(
                    request=request,
                    messagekey='SHORT_URL_ENCODING_MISMATCH',
                    status_code=400)
        #
        # Lookup the short url
        #
        self.hash = get_shorturlhash(self.normalized_shorturl)
        s = None
        try:
            if ShortURLs.objects.filter(hash=self.hash).exists():
                s = ShortURLs.objects.get(hash=self.hash)
        except:
            pass
        if not s:
            raise self.event.log(
                    request=request,
                    event_type='U',
                    messagekey='SHORT_URL_NOT_FOUND',
                    value=self.shorturl,
                    status_code=404
            )
        if s.shorturl != self.shorturl:
            raise self.event.log(
                    request=request,
                    event_type='E',
                    messagekey='SHORT_URL_MISMATCH',
                    status_code=400)
        #
        # If the short URL is not active, 404
        #
        if not s.is_active:
            raise self.event.log(
                    request=request,
                    event_type='N',
                    messagekey='HTTP_404',
                    value=self.shorturl,
                    status_code=404)
        #
        # Lookup the matching long url by the short url's id, and decode it.
        #
        l = LongURLs.objects.get(id=s.longurl_id)
        if not l:
            raise self.event.log(request=request,
                                 messagekey='HTTP_404',
                                 value='ERROR, HTTP 404 longurl not found',
                                 longurl=l,
                                 shorturl=s,
                                 status_code=404)
        longurl = get_decodedurl(l.longurl)
        #
        # Log that a 301 request to the matching long url is about to occur
        #
        msg = self.event.log(
                request=request,
                event_type='S',
                messagekey='HTTP_301',
                value=longurl,
                longurl=l,
                shorturl=s,
                status_code=301
        )
        #
        # Return the longurl
        #
        return longurl, msg


