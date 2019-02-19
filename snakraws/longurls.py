'''
LongURLs.py contains the logic necessary to consume a long URL and return a short URL for it.
'''
from urllib.parse import urlparse
# from filetransfers.api import serve_file

from django import http
from django.http import Http404
from django.db import transaction as xaction

from snakraws import settings
from snakraws.models import LongURLs, ShortURLs
from snakraws.shorturls import ShortURL
from snakraws.loggr import SnakrLogger
from snakraws.security import get_useragent_or_403_if_bot
from snakraws.utils import get_json, is_url_valid, is_image, get_decodedurl, get_encodedurl, get_longurlhash, true_or_false, get_host, get_referer
from snakraws.ips import SnakrIP

class LongURL:
    """Validates and processes the long URL in the POST request."""

    def __init__(self, request, *args, **kwargs):

        self.event = SnakrLogger()
        bot_name, self.useragent = get_useragent_or_403_if_bot(request)
        if bot_name:
            raise self.event.log(request=request, event_type='B', messagekey='ROBOT', value='Known Bot {%}' % bot_name, status_code=-403)

        try:
            self.host = get_host(request, False)
            self.referer = get_referer(request, False)
        except Exception as e:
            raise self.event.log(messagekey='REQUEST_INVALID', status_code=400, request=None, message=str(e))

        self.longurl = ""
        self.longurl_is_preencoded = False
        self.normalized_longurl = ""
        self.normalized_longurl_scheme = ""
        self.hash = 0
        self.vanity_path = ''

        self.deviceid = None # device support TBD

        self.ip = SnakrIP(request, geolocate=True)
        if self.ip.is_error:
            raise self.event.log(messagekey='IP_LOOKUP_INVALID', status_code=400, request=None, message=self.ip.errors)

        # if is_blacklisted(self.ip, self.deviceid, self.host, self.referer, self.useragent):
        #     raise self.event.log(request=request, event_type='B', messagekey='BLACKLISTED', status_code=403)

        lurl = get_json(request, 'u')
        if not lurl:
            raise self.event.log(messagekey='LONG_URL_MISSING', status_code=400)

        if not is_url_valid(lurl):
            raise self.event.log(messagekey='LONG_URL_INVALID', value=lurl, status_code=400)

        self.vanity_path = get_json(request, 'vp')

        image_url = get_json(request, 'img')
        if is_image(image_url):
            self.linked_image = image_url
        else:
            self.linked_image = None

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
        self.id = -1

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
            # 1. Create a LongURLs persistence object
            #
            if self.longurl_is_preencoded:
                originally_encoded = True
            else:
                originally_encoded = False
            dl = LongURLs(hash=self.hash,
                            longurl=self.normalized_longurl,
                            originally_encoded=originally_encoded,
                            is_active=True
                            )
            dl.save()
            #
            # 2. Generate a short url for it (with collision handling) and calc its compression ratio vs the long url
            #
            s = ShortURL(request)
            s.make_short(self.normalized_longurl_scheme, self.vanity_path)
            compression_ratio = float(len(s.shorturl)) / float(len(self.normalized_longurl))
            #
            # 3. Create a matching ShortURLs persistence object
            #
            ds = ShortURLs(hash=s.hash,
                             longurl_id=dl.id,
                             shorturl=s.shorturl,
                             compression_ratio=compression_ratio,
                             shorturl_path_size=settings.SHORTURL_PATH_SIZE,
                             is_active=True
                             )
            #
            # 4. Is there an associated image? If so, download it to static,
            #
            # if self.linked_image:
            #    ft = file
            #
            # 5. Persist everything
            #
            ds.save()
            self.event.log(request=request,
                           ipobj=self.ip,
                           event_type='L',
                           messagekey='LONG_URL_SUBMITTED',
                           value=self.normalized_longurl,
                           longurl=dl,
                           shorturl=ds,
                           status_code=200
                           )
            #
            # 6. Return the short url
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
            self.event.log(
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
        return s.shorturl
