'''
Centralized event logging for Snakr. Wraps the Django core logging system and adds JSON logging support.
'''
import logging
import datetime

from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.http import Http404, HttpResponseServerError

from pythonjsonlogger import jsonlogger

from snakraws import settings
from snakraws.models import DEFAULT_EVENT_TYPE, UNSPECIFIED_URL_ID, DEFAULT_HTTP_STATUS_CODE, HTTP_STATUS_CODE, log_event
from snakraws.utils import get_meta
from snakraws.ips import SnakrIP


class SnakrLogger(Exception):

    def __init__(self, *args, **kwargs):
        #
        # initialize python-json-logger
        # see: https://github.com/madzak/python-json-logger
        #
        self.logger = logging.getLogger(settings.VERBOSE_NAME)
        if settings.VERBOSE_LOGGING:
            #self.logger.handlers = []
            self.__logHandler = logging.StreamHandler()
            self.__formatter = jsonlogger.JsonFormatter()
            self.__logHandler.setFormatter(self.__formatter)
            self.logger.addHandler(self.__logHandler)
            #self.__last = None
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
        #if status_code not in HTTP_STATUS_CODE[0]:
        #    status_code = DEFAULT_HTTP_STATUS_CODE
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

            #
            # get client msg from the request obj
            #
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
                'dt':       dtnow,
                't':        event_type
            }

            if settings.ENABLE_ANALYTICS and request:
                db_id, status_code = log_event(dt, event_type, status_code, msg, shorturl, longurl, ipobj, hostname, useragent, referer)
                jsondata['id'] = str(db_id)

            if status_code != 0:
                jsondata['s'] = abs(status_code)

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

