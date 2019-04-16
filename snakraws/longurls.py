'''
LongURLs.py contains the logic necessary to consume a long URL and return a short URL for it.
'''

from urllib.parse import urlparse
# from filetransfers.api import serve_file

from django.http import Http404
from django.db import transaction as xaction
from django.forms import ValidationError

from snakraws import settings
from snakraws.settings import CANONICAL_MESSAGES
from snakraws.models import LongURLs, ShortURLs
from snakraws.shorturls import ShortURL
from snakraws.persistence import SnakrLogger
from snakraws.security import get_useragent_or_403_if_bot
from snakraws.utils import get_json, is_url_valid, is_image, get_decodedurl, get_encodedurl, \
    get_longurlhash, get_host, get_referer, is_profane, get_target_meta, fit_text, get_message
from snakraws.ips import SnakrIP


class LongURL:
    """Validates and processes the long URL in the POST request."""

    def __init__(self, request, *args, **kwargs):

        lu = kwargs.pop('lu', None)
        vp = kwargs.pop('vp', None)
        bl = kwargs.pop('bl', None)

        self.event = SnakrLogger()

        # get IP and technographic info from the request
        bot_name, self.useragent = get_useragent_or_403_if_bot(request)
        if bot_name:
            raise self.event.log(request=request, event_type='B', messagekey='ROBOT', value='Known Bot {%}' % bot_name, status_code=-403)

        try:
            self.host = get_host(request, False)
            self.referer = get_referer(request, False)
        except Exception as e:
            raise self.event.log(messagekey='REQUEST_INVALID', status_code=400, request=None, message=str(e))
        self.deviceid = None  # device support TBD
        self.ip = SnakrIP(request, geolocate=True)
        if self.ip.is_error:
            raise self.event.log(messagekey='IP_LOOKUP_INVALID', status_code=400, request=None, message=self.ip.errors)

        lurl = get_json(request, 'lu') or lu
        if not lurl:
            raise self.event.log(messagekey='LONG_URL_MISSING', status_code=400)

        if not is_url_valid(lurl):
            raise self.event.log(messagekey='LONG_URL_INVALID', value=lurl, status_code=400)

        self.vanity_path = get_json(request, 'vp') or vp

        if lurl == get_decodedurl(lurl):
            preencoded = False
            self.normalized_longurl = get_encodedurl(lurl)
        else:
            preencoded = True
            self.normalized_longurl = lurl

        self.normalized_longurl_scheme = urlparse(lurl).scheme.lower()
        self.longurl_is_preencoded = preencoded
        self.longurl = lurl
        self.hash = get_longurlhash(self.normalized_longurl)

        # DISALLOWED! a short url cannot be a subsequent long url to shorten!
        sh = 'http://%s' % getattr(settings, 'SHORTURL_HOST', 'localhost')
        ssh = 'https://%s' % getattr(settings, 'SECURE_SHORTURL_HOST', 'bret.guru')
        lnl = self.normalized_longurl.lower()
        if sh in lnl or ssh in lnl:
            raise ValidationError(get_message("DISALLOW_DOUBLE_SHORTENING"))

        self.id = -1
        self.title, self.description, self.image_url = get_target_meta(self.normalized_longurl, request)
        self.byline = fit_text(bl or self.description, "", 300)

        return

    # get or make_short the short URL for an instance of this long URL
    @xaction.atomic
    def get_or_make_short(self, request, *args, **kwargs):
        #
        # Does the long URL already exist?
        #
        try:
            l = LongURLs.objects.get(hash=self.hash)
        except:
            l = None
            pass
        if not l:
            #
            # NO IT DOESN'T
            #
            # 1. Does the website even exist? If not, error
            #
            # if not site_exists(self.normalized_longurl):
            #     raise self.event.log(
            #             request=request,
            #             ipobj=self.ip,
            #             event_type='E',
            #             messagekey='LONG_URL_CONTENT_MISSING',
            #             value=self.normalized_longurl,
            #             status_code=400)
            #
            # 2. IF ENABLE_LONG_URL_PROFANITY_CHECKING = True, check the target for profanity w/30-sec timeout
            #
            if getattr(settings, "ENABLE_LONG_URL_PROFANITY_CHECKING", False):
                if is_profane(self.normalized_longurl):
                    raise self.event.log(
                            request=request,
                            ipobj=self.ip,
                            event_type='E',
                            messagekey='LONG_URL_INVALID',
                            value=self.normalized_longurl,
                            status_code=400)
                # long_url_contents = None
                # try:
                #     f = urlopen(self.normalized_longurl, timeout=30)
                #     if f:
                #         long_url_contents = f.read()
                # except URLError as e:
                #     pass
                # if long_url_contents:
                #     if is_profane(long_url_contents):
                #         raise self.event.log(
                #                 request=request,
                #                 ipobj=self.ip,
                #                 event_type='E',
                #                 messagekey='LONG_URL_CONTENT_INVALID',
                #                 value=self.normalized_longurl,
                #                 status_code=400)

            #
            # 3. Create a LongURLs persistence object
            #
            if self.longurl_is_preencoded:
                originally_encoded = True
            else:
                originally_encoded = False
            dl = LongURLs(hash=self.hash,
                          longurl=self.normalized_longurl,
                          originally_encoded=originally_encoded,
                          title=self.title,
                          description=self.description,
                          image_url=self.image_url,
                          byline=self.byline,
                          is_active=True
                          )
            dl.save()
            #
            # 4. Generate a short url for it (with collision handling) and calc its compression ratio vs the long url
            #
            s = ShortURL(request)
            s.make_short(self.normalized_longurl_scheme, self.vanity_path)
            compression_ratio = float(len(s.shorturl)) / float(len(self.normalized_longurl))
            #
            # 5. Create a matching ShortURLs persistence object
            #
            ds = ShortURLs(hash=s.hash,
                           longurl_id=dl.id,
                           shorturl=s.shorturl,
                           compression_ratio=compression_ratio,
                           shorturl_path_size=settings.SHORTURL_PATH_SIZE,
                           is_active=True
                           )
            #
            # 6. Is there an associated image? If so, download it to static,
            #
            # if self.linked_image:
            #    ft = file
            #
            # 7. Persist everything
            #
            ds.save()
            msg = self.event.log(request=request,
                                 ipobj=self.ip,
                                 event_type='L',
                                 messagekey='LONG_URL_SUBMITTED',
                                 value=self.normalized_longurl,
                                 longurl=dl,
                                 shorturl=ds,
                                 status_code=200
                                 )
            #
            # 8. Return the short url
            #
        else:
            #
            # YES IT DOES
            # Return the existing short url to the caller
            #
            # 1. Check for potential collision
            #
            if l.longurl != self.normalized_longurl:
                raise self.event.log(
                        request=request,
                        ipobj=self.ip,
                        messagekey='HASH_COLLISION',
                        value=self.normalized_longurl,
                        status_code=400
                )
            #
            # 2. Lookup the short url. It must be active.
            #
            s = ShortURLs.objects.get(longurl=l, is_active=True)
            if not s:
                raise Http404
            #
            # 3. Log the lookup
            #
            msg = self.event.log(
                    request=request,
                    ipobj=self.ip,
                    event_type='R',
                    messagekey='LONG_URL_RESUBMITTED',
                    value=self.normalized_longurl,
                    longurl=l,
                    shorturl=s,
                    status_code=200)
            #
            # 4. Return the short url
            #
        return s.shorturl, msg

