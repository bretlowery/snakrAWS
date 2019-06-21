'''
LongURLs.py contains the logic necessary to consume a long URL and return a short URL for it.
'''

from urllib.parse import urlparse
from urllib.request import urlopen

from django.http import Http404
from django.db import transaction as xaction
from django.forms import ValidationError
from django.core.cache import cache

from snakraws import settings
from snakraws.models import LongURLs, ShortURLs
from snakraws.shorturls import ShortURL
from snakraws.persistence import SnakrLogger
from snakraws.security import get_useragent_or_403_if_bot
from snakraws.utils import get_json, is_url_valid, is_image, get_decodedurl, get_encodedurl, \
    get_longurlhash, get_host, get_referer, is_profane, fit_text, get_message, get_shorturlhash, inspect_url, urlparts
from snakraws.ips import SnakrIP
from snakraws.proxies import Proxies


class LongURL:
    """Validates and processes the long URL in the POST request."""

    def __init__(self, request, *args, **kwargs):

        lu = kwargs.pop('lu', None)
        vp = kwargs.pop('vp', None)
        bl = kwargs.pop('bl', None)
        de = kwargs.pop('de', None)
        self.bl = bl
        self.de = de

        self.event = SnakrLogger()

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

        dlurl = get_decodedurl(lurl)

        # DISALLOWED! a Snakr short url cannot be a subsequent long url to shorten!
        if ShortURLs.objects.filter(hash=get_shorturlhash(dlurl)).exists():
            raise ValidationError(get_message("DISALLOW_DOUBLE_SHORTENING"))

        # 2019-6-21 bml BUGFIX issue where some sites don't accept encoded versions of their url and return 403s or something instead
        # this isn't a reliable check since many sites will 403 this as a bad traffic source anyway since it's coming from an AWS EC2 instance
        if lurl == dlurl:
            preencoded = False
            self.normalized_longurl = get_encodedurl(dlurl)
            httpcode = 403
            try:
                httpcode = urlopen(self.normalized_longurl).getcode()
            except:
                pass
            if httpcode != 200:
                preencoded = True
                self.normalized_longurl = lurl
        else:
            preencoded = True
            self.normalized_longurl = lurl

        self.normalized_longurl_scheme = urlparse(lurl).scheme.lower()
        self.longurl_is_preencoded = preencoded
        self.longurl = lurl
        self.meta = Meta(self.normalized_longurl, request)
        self.byline = self.meta.title if not bl else bl
        self.byline = '%s: %s' % (self.meta.site_name, self.byline) \
            if self.meta.site_name and '%s: ' % self.meta.site_name not in self.byline else self.byline
        self.meta.description = self.meta.description if not de else de
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
                          title=self.meta.title,
                          description=self.meta.description,
                          image_url=self.meta.image_url,
                          byline=self.byline,
                          site_name=self.meta.site_name,
                          meta_status=self.meta.status,
                          meta_status_msg=self.meta.status_msg,
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
            # 6. *TBD, MAYBE* Is there an associated image? If so, download it to static.
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


class Meta:

    def __init__(self, url, request=None):

        def _get_html_title(soupobj):
            val = ""
            og_title = soupobj.find("meta", property="og:title")
            if og_title:
                val = og_title.attrs["content"].strip()
            else:
                try:
                    val = soupobj.title.string.strip()
                except:
                    pass
            return val

        def _get_html_description(soupobj):
            val = ""
            og_description = soupobj.find("meta", property="og:description")
            if og_description:
                val = og_description.attrs["content"].strip()
            return val

        def _get_image_url(soupobj):
            val = ""
            og_image_url = soupobj.find("meta", property="og:image")
            if og_image_url:
                val = og_image_url.attrs["content"]
                if val:
                    if is_url_valid(val):
                        parts = urlparts(val)
                        if parts:
                            if 'http' not in parts.scheme.lower():
                                val = ""
            return val

        def _get_site_name(soupobj):
            val = ""
            og_description = soupobj.find("meta", property="og:site_name")
            if og_description:
                val = og_description.attrs["content"].strip()
            return val

        def _get_pdf_title(contentbytestream):
            import io
            from PyPDF2 import PdfFileReader
            val = ""
            try:
                with io.BytesIO(contentbytestream) as pdf:
                    pdfr = PdfFileReader(pdf)
                    pdfi = pdfr.getDocumentInfo()
                    val = str(pdfi.title).strip()
            except:
                pass
            return val

        self.status = 0
        self.status_msg = ""
        self.title = url
        self.description = ""
        self.image_url = ""
        self.site_name = ""
        proxies = cache.get('proxies')
        if not proxies:
            proxies = Proxies()  # (request)
            cache.set('proxies', proxies)
        doctype, target, soup, selected_proxy, err = inspect_url(url, request, proxies)
        if doctype and target:
            self.status = target.status_code
            self.status_msg = err
            if target.status_code == 200:
                if doctype == "html":
                    if soup:
                        self.title = _get_html_title(soup)
                        self.description = _get_html_description(soup)
                        self.image_url = _get_image_url(soup)
                        self.site_name = _get_site_name(soup)
                elif doctype == "pdf":
                    self.title = _get_pdf_title(target.content)
        if not self.title:
            self.title = url
        self.title = fit_text(self.title, "", 100)
        self.proxy = selected_proxy
        return
