'''
LongURLs.py contains the logic necessary to consume a long URL and return a short URL for it.
'''
import urllib
# from filetransfers.api import serve_file

from django.http import Http404
from django.db import transaction as xaction

import settings
from snakraws.models import DimLongURL, DimShortURL
from snakraws import shorturls
from snakraws.loggr import SnakrEventLogger
from snakraws.utils import get_json, is_url_valid, is_image, get_decodedurl, get_encodedurl, get_longurlhash, true_or_false


class LongURL:
    """Validates and processes the long URL in the POST request."""

    def __init__(self, request, *args, **kwargs):
        self.longurl = ""
        self.longurl_is_preencoded = False
        self.normalized_longurl = ""
        self.normalized_longurl_scheme = ""
        self.id = 0
        self.vanity_path = ''
        self.event = SnakrEventLogger()

        lurl = ""

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

        self.normalized_longurl_scheme = urllib.parse(lurl).scheme.lower()
        self.longurl_is_preencoded = preencoded
        self.longurl = lurl
        self.id = get_longurlhash(self.normalized_longurl)

        return

    # get or make the short URL for an instance of this long URL
    @xaction.atomic
    def to_short(self, request, *args, **kwargs):
        nopersist = true_or_false(get_json(request, 'nopersist'))
        #
        # Does the long URL already exist?
        #
        try:
            l = DimLongURL.objects.get(id=self.id)
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
                originally_encoded = 'Y'
            else:
                originally_encoded = 'N'
            ldata = DimLongURL(id=self.id, longurl=self.normalized_longurl, originally_encoded=originally_encoded)
            #
            # 2. Generate a short url for it (with collision handling) and calc its compression ratio vs the long url
            #
            s = shorturls.ShortURL(request)
            s.make(self.normalized_longurl_scheme, self.vanity_path)
            compression_ratio = float(len(s.shorturl)) / float(len(self.normalized_longurl))
            #
            # 3. Create a matching ShortURLs persistence object
            #
            sdata = DimShortURL(id=s.id,
                                longurl_id=ldata.id,
                                shorturl=s.shorturl,
                                is_active=True,
                                compression_ratio=compression_ratio,
                                shorturl_path_size=settings.SHORTURL_PATH_SIZE)
            #
            # 4. Is there an associated image? If so, download it to static,
            #
            # if self.linked_image:
            #    ft = file
            #
            # 5. Persist everything
            #
            if not nopersist:
                ldata.save()
                sdata.save()
                self.event.log(request=request,
                               event_type='L',
                               messagekey='LONG_URL_SUBMITTED',
                               value=self.normalized_longurl,
                               longurl_id=self.id,
                               shorturl_id=s.id,
                               status_code=200)
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
                raise self.event.log(request=request, messagekey='HASH_COLLISION', value=self.normalized_longurl, status_code=400)
            #
            # 2. Lookup the short url. It must be active.
            #
            s = DimShortURL.objects.get(longurl_id=self.id, is_active=True)
            if not s:
                raise Http404
            #
            # 3. Log the lookup
            #
            self.event.log(request=request, event_type='R', messagekey='LONG_URL_RESUBMITTED', value=self.normalized_longurl, longurl_id=self.id, shorturl_id=s.id, status_code=200)
            #
            # 4. Return the short url
            #
        return s.shorturl
