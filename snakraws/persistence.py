'''
Centralized persistence and logging for Snakr. Wraps the Django core logging system and adds JSON logging support.
'''

import logging
import datetime

from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.http import Http404, HttpResponseServerError
from django.core.exceptions import ObjectDoesNotExist

from pythonjsonlogger import jsonlogger

from snakraws import settings
from snakraws.models import EVENT_TYPE, DEFAULT_EVENT_TYPE, DEFAULT_HTTP_STATUS_CODE, \
    DimContinent, DimReferer, DimRegion, DimPostalCode, DimIP, DimHost, DimDevice, DimCountry, DimUserAgent, DimCity, FactEvent, \
    LongURLs, ShortURLs
from snakraws.utils import get_meta, get_hash
from snakraws.ips import SnakrIP
from snakraws.security import is_blacklisted


class SnakrLogger(Exception):

    def __init__(self, *args, **kwargs):
        #
        # initialize python-json-logger
        # see: https://github.com/madzak/python-json-logger
        #
        self.logger = logging.getLogger(settings.VERBOSE_NAME)
        if settings.VERBOSE_LOGGING:
            self.__logHandler = logging.StreamHandler()
            self.__formatter = jsonlogger.JsonFormatter()
            self.__logHandler.setFormatter(self.__formatter)
            self.logger.addHandler(self.__logHandler)
        self.last_ip_address = 'N/A'
        self.last_dtnow = 'N/A'
        self.last_http_user_agent = 'N/A'
        return

    def log(self, **kwargs):
        #
        # get parameters
        #
        if not settings.ENABLE_LOGGING:
            return
        #
        # get parameters
        #
        request = kwargs.pop('request', None)
        msgkey = kwargs.pop('messagekey', None)
        msg = kwargs.pop('message', None)
        value = str(kwargs.pop('value', None))
        event_type = kwargs.pop('event_type', DEFAULT_EVENT_TYPE)
        longurl = kwargs.pop('longurl', None)
        shorturl = kwargs.pop('shorturl', None)
        verbose = kwargs.pop('verbose', False)
        status_code = kwargs.pop('status_code', DEFAULT_HTTP_STATUS_CODE)
        dt = datetime.datetime.now()
        dtnow = kwargs.pop('dt', dt.isoformat())
        ipobj = kwargs.pop('ipobj', None)
        #
        if event_type == 'I':
            status_code = 0
        if status_code == 200 or status_code == 0:
            event_type = 'I'
        if settings.VERBOSE_LOGGING or (status_code >= 400 and status_code != 404):
            verbose = True
        if not msg:
            if msgkey:
                msgkey = msgkey.strip().upper()
                try:
                    msg = settings.CANONICAL_MESSAGES[msgkey]
                    if not msg:
                        msg = settings.MESSAGE_OF_LAST_RESORT
                except:
                    msg = settings.MESSAGE_OF_LAST_RESORT
                    pass
            else:
                msg = settings.MESSAGE_OF_LAST_RESORT
        if value is not None and value != 'None':
            if msg:
                try:
                    msg = msg % value
                except:
                    msg = value
                    pass
            else:
                msg = value

        dupe_message = False
        hostname = None
        useragent = None
        referer = None
        if request:
            hostname, useragent, referer = get_meta(request, False)
            if not ipobj:
                ipobj = SnakrIP(request, geolocate=True)
            if ipobj.ip == self.last_ip_address:
                if useragent == self.last_http_user_agent:
                    if dtnow == self.last_dtnow:
                        dupe_message = True

        if not dupe_message:

            jsondata = {
                'dtstamp':       dtnow
            }

            if settings.ENABLE_ANALYTICS and request:
                db_id, event_type, msg, status_code, shorturl, longurl = self._log_event(
                        request,
                        dt,
                        event_type,
                        status_code,
                        msg,
                        shorturl,
                        longurl,
                        ipobj,
                        hostname,
                        useragent,
                        referer
                )
                jsondata['event'] = str(db_id)

            if status_code != 0:
                jsondata['http_status'] = abs(status_code)
                jsondata['event'] = EVENT_TYPE[event_type]

            if (settings.VERBOSE_LOGGING or verbose) and request:
                jsondata['lu'] = str(longurl.id)
                jsondata['su'] = str(shorturl.id)
                jsondata['ip'] = ipobj.ip.exploded
                #jsondata['lat'] = str(ipobj.
                #jsondata['long'] = str(geo_long)
                #jsondata['city'] = str(geo_city)
                #jsondata['cnty'] = str(geo_country)
                #jsondata['host'] = str(http_host)
                #jsondata['ua'] = str(http_useragent)
                #jsondata['ref'] = http_referer

            msg = "%s %s" % (dtnow, msg)

            if status_code == 0 \
                    or (status_code == 200 and settings.LOG_HTTP200) \
                    or (status_code == 301 and settings.LOG_HTTP301) \
                    or (status_code == 302 and settings.LOG_HTTP302) \
                    or (status_code == 404 and settings.LOG_HTTP404):
                self.logger.info(msg, extra=jsondata)
            elif abs(status_code) == 403 and settings.LOG_HTTP403:
                self.logger.warning(msg, extra=jsondata)
            elif status_code == 400 and settings.LOG_HTTP400:
                self.logger.warning(msg, extra=jsondata)
            else:
                self.logger.critical(msg, extra=jsondata)

            def switch(x):
                return {
                    -403: PermissionDenied,
                    200:  msg,
                    301:  msg,
                    302:  msg,
                    400:  SuspiciousOperation(msg),
                    403:  SuspiciousOperation(msg),
                    404:  Http404,
                    422:  SuspiciousOperation(msg),
                    500:  HttpResponseServerError(msg),
                }.get(x, 200)

            if status_code != 0:
                return switch(status_code)

        return

    @staticmethod
    def _log_event(request, dt, event_type, status_code, msg, shorturl, longurl, ipobj, hostname, useragent, referer):

        # dimension log_event helper function here to keep it within the scope of the transaction
        def _get_or_create_dimension(modelclass, **kwargs):
            # assume 1st kwarg is the value to use to generate the hashkey
            key = kwargs.pop("key")
            if not key:
                key = "missing"
            hash = get_hash(' '.join(str(key).split()).lower())
            exists = False
            is_mutable = True
            try:
                m = modelclass.objects.filter(hash=hash).get()
                if m:
                    exists = True
                    is_mutable = m.is_mutable
            except ObjectDoesNotExist:
                m = modelclass()
                pass
            if not exists:
                for f in m._meta.fields:
                    f = f.name
                    lf = f.lower()
                    if lf == "hash":
                        if not m.hash:
                            setattr(m, f, hash)
                    elif lf == "is_mutable":
                        if not m.is_mutable:
                            setattr(m, f, is_mutable)
                    elif lf != "id" and is_mutable:
                        for k, v in kwargs.items():
                            if k.lower() == lf:
                                setattr(m, f, v)
                                break
                m.save()
            return m

        # dimension log_event helper function here to keep it within the scope of the transaction
        def _get_or_create_geo_dimension(modelclass, strkey, unknown_value="unknown", missing_value="missing"):
            if strkey in ipobj.geodict:
                m = _get_or_create_dimension(modelclass, key=ipobj.geodict[strkey], name=ipobj.geodict[strkey])
            else:
                if ipobj.is_global:
                    value = unknown_value
                else:
                    value = missing_value
                m = _get_or_create_dimension(modelclass, key=value, name=value)
            return m


        ip = _get_or_create_dimension(DimIP, key=ipobj.ip.exploded, ip=ipobj.ip.exploded)
        #
        city = _get_or_create_geo_dimension(DimCity, "city")
        continent = _get_or_create_geo_dimension(DimContinent, "continent")
        country = _get_or_create_geo_dimension(DimCountry, "country")
        postalcode = _get_or_create_geo_dimension(DimPostalCode, "postalcode")
        region = _get_or_create_geo_dimension(DimRegion, "region")
        #
        # device support TBD
        deviceid = "unknown"
        device = _get_or_create_dimension(DimDevice, key=deviceid, deviceid=deviceid)
        #
        host = _get_or_create_dimension(DimHost, key=hostname, hostname=hostname)
        referer = _get_or_create_dimension(DimReferer, key=referer, referer=referer)
        useragent = _get_or_create_dimension(DimUserAgent, key=useragent, useragent=useragent)

        if is_blacklisted(
                city,
                continent,
                country,
                device,
                ip,
                host,
                postalcode,
                referer,
                region,
                useragent):
            event_type = 'B'
            msg = EVENT_TYPE[event_type]
            status_code = -403

        abs_status_code = abs(status_code)

        if not longurl:
            longurl = LongURLs.objects.filter(hash=get_hash("unspecified")).get()
        if not shorturl:
            shorturl = ShortURLs.objects.filter(hash=get_hash("unspecified")).get()

        fact = FactEvent(
                event_yyyymmdd=dt.strftime('%Y%m%d'),
                event_hhmiss=dt.strftime('%H%M%S'),
                event_type=event_type,
                http_status_code=abs_status_code,
                info=msg,
                longurl=longurl,
                shorturl=shorturl,
                city=city,
                continent=continent,
                country=country,
                device=device,
                host=host,
                ip=ip,
                postalcode=postalcode,
                referer=referer,
                region=region,
                useragent=useragent
        )
        fact.save()

        return fact.id, event_type, msg, status_code, shorturl, longurl
