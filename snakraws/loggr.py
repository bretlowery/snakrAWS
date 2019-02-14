'''
Centralized event logging for Snakr. Wraps the Django core logging system and adds JSON logging support.
'''
import logging
import datetime

from django.core.exceptions import SuspiciousOperation, PermissionDenied
from django.http import Http404, HttpResponseServerError

from pythonjsonlogger import jsonlogger

import settings
from snakraws.singleton import Singleton
from snakraws.models import DEFAULT_EVENT_TYPE, UNSPECIFIED_URL_ID, DEFAULT_HTTP_STATUS_CODE, HTTP_STATUS_CODE, save
from snakraws.utils import get_meta
from snakraws.ips import SnakrIP


class SnakrEventLogger(Exception):

    def __init__(self, *args, **kwargs):
        #
        # there can be only one
        # to minimize the duplication of messages that Django is known for
        # see Method 3 on http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
        #
        __metaclass__ = Singleton
        #
        # initialize python-json-logger
        # see: https://github.com/madzak/python-json-logger
        #
        self.logger = logging.getLogger(settings.VERBOSE_NAME)
        if settings.VERBOSE_LOGGING:
            self.logger.handlers = []
            self.__logHandler = logging.StreamHandler()
            self.__formatter = jsonlogger.JsonFormatter()
            self.__logHandler.setFormatter(self.__formatter)
            self.logger.addHandler(self.__logHandler)
            self.__last = None
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
        infokey = kwargs.pop('messagekey', None)
        info = kwargs.pop('message', None)
        value = str(kwargs.pop('value', None))
        event_type = kwargs.pop('event_type', DEFAULT_EVENT_TYPE)
        longurl_id = kwargs.pop('longurl_id', UNSPECIFIED_URL_ID)
        shorturl_id = kwargs.pop('shorturl_id', UNSPECIFIED_URL_ID)
        verbose = kwargs.pop('verbose', False)
        status_code = kwargs.pop('status_code', DEFAULT_HTTP_STATUS_CODE)
        dt = datetime.now()
        dtnow = kwargs.pop('dt', dt.isoformat())
        #
        if status_code not in HTTP_STATUS_CODE[0]:
            status_code = DEFAULT_HTTP_STATUS_CODE
        if event_type == 'I':
            status_code = -1
        if status_code == 200:
            event_type = 'I'
        if settings.DEBUG or settings.VERBOSE_LOGGING or (status_code >= 400 and status_code != 404):
            verbose = True
        if not info:
            if infokey:
                infokey = infokey.strip().upper()
                try:
                    info = settings.CANONICAL_MESSAGES[infokey]
                    if not info:
                        info = settings.MESSAGE_OF_LAST_RESORT
                except:
                    info = settings.MESSAGE_OF_LAST_RESORT
                    pass
            else:
                info = settings.MESSAGE_OF_LAST_RESORT
        if value is not None and value != 'None':
            if info:
                try:
                    info = info % value
                except:
                    info = value
                    pass
            else:
                info = value

            #
            # get client info from the request obj
            #
        dupe_message = False
        host = None
        useragent = None
        referer = None
        ipobj = None
        if request:
            host, useragent, referer = get_meta(request, False)
            ipobj = SnakrIP(request)
            if ipobj.ip == self.last_ip_address:
                if useragent == self.last_http_user_agent:
                    if dtnow == self.last_dtnow:
                        dupe_message = True

        if not dupe_message:

            jsondata = {
                'dt':       dtnow
            }

            db_id = -1
            if settings.DATABASE_LOGGING and request:
                db_id, status_code = save(dt, event_type, status_code, info, shorturl_id, longurl_id, ipobj, host, useragent, referer)
                jsondata['id'] = str(db_id)

            if (settings.VERBOSE_LOGGING or verbose) and request:
                jsondata['lu'] = str(longurl_id)
                jsondata['su'] = str(shorturl_id)
                #jsondata['ip'] = ipobj.ip
                #jsondata['lat'] = str(geo_lat)
                #jsondata['long'] = str(geo_long)
                #jsondata['city'] = str(geo_city)
                #jsondata['cnty'] = str(geo_country)
                #jsondata['host'] = str(http_host)
                #jsondata['ua'] = str(http_useragent)
                #jsondata['ref'] = http_referer

            jsondata['s'] = abs(status_code)
            jsondata['t'] = event_type

            if abs(status_code) == 403 and settings.LOG_HTTP403:
                self.logger.warning(info, extra=jsondata)
            elif (status_code <= 200 and settings.LOG_HTTP200) or (status_code == 404 and settings.LOG_HTTP404) or (status_code == 302 and settings.LOG_HTTP302):
                self.logger.info(info, extra=jsondata)
            elif status_code == 400 and settings.LOG_HTTP400:
                self.logger.warning(info, extra=jsondata)
            else:
                self.logger.critical(info, extra=jsondata)

            def switch(x):
                return {
                    -403: PermissionDenied,
                    200:  info,
                    301:  info,
                    302:  info,
                    400:  SuspiciousOperation(info),
                    403:  SuspiciousOperation(info),
                    404:  Http404,
                    422:  SuspiciousOperation(info),
                    500:  HttpResponseServerError(info),
                }.get(x, 200)

            if status_code != 0:
                return switch(status_code)

        return

