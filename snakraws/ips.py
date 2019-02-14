'''
ips.py defines the SnakrIP object which encapsulates IP and IP-based geolocation information for the origins of requests handled by Snakr.
'''

from django.conf import settings

import os
import json
import requests
import ipaddress
import inspect
from urllib.parse import urlparse


class SnakrIP:

    @staticmethod
    def _resolve_ip(iplist):
        ip = None
        errors = None
        try:
            # remove the private ips from the beginning
            while len(iplist) > 0:
                checkip = ipaddress.ip_address(iplist[0])
                if checkip.is_loopback:
                    ip = iplist[0]
                    break
                elif checkip.is_private:
                    ip = iplist[0]
                    iplist.pop(0)
                # take the first ip which is not a private one (of a proxy)
                elif len(iplist) > 0:
                    ip = iplist[0]
                    break
        except Exception as e:
            errors = str(e)
            pass
        return ip, errors

    def _geolocate(self, ip):
        jsondata = {}
        jsonstr = '{}'
        is_error = False
        errors = None
        geolocation_api_url = getattr(settings, 'GEOLOCATION_API_URL', None)
        if geolocation_api_url:
            if ip.is_global or not ip.is_private:
                url = geolocation_api_url.replace('%ip%', ip.exploded)
                try:
                    # normalize the resulting format especially quotes with this hacky-looking next line
                    geolookup = requests.get(url).json()
                    provider = urlparse(geolocation_api_url).hostname
                    geolookup["provider"] = provider
                    jsonstr = json.dumps(geolookup).replace('null, ', '"unknown", ')
                except Exception as e:
                    is_error = True
                    errors = str(e)
                    pass
            else:
                try:
                    provider = urlparse(geolocation_api_url).hostname
                    if ip.is_loopback:
                        self.jsonstr = '{"ip": "%s","type": "ipv4", "is_loopback": "true", "provider": "%s"}' % (ip.exploded, provider)
                    elif ip.is_private:
                        self.jsonstr = '{"ip": "%s","type": "ipv4", "is_private": "true", "provider": "%s"}' % (ip.exploded, provider)
                    elif ip.is_link_local:
                        self.jsonstr = '{"ip": "%s","type": "ipv4", "is_link_local": "true", "provider": "%s"}' % (ip.exploded, provider)
                    elif ip.is_multicast:
                        self.jsonstr = '{"ip": "%s","type": "ipv4", "is_multicast": "true", "provider": "%s"}' % (ip.exploded, provider)
                    else:
                        self.jsonstr = '{"ip": "%s","type": "ipv4", "is_unspecified": "true", "provider": "%s"}' % (ip.exploded, provider)
                except Exception as e:
                    is_error = True
                    errors = str(e)
                    pass
            if jsonstr:
                try:
                    jsondata = json.loads(jsonstr)
                except Exception as e:
                    is_error = True
                    errors = str(e)
                    pass
        else:
            errors = "Missing settings.GEOLOCATION_API_URL"

        # expose the geo info as parent object attributes
        for k, v in jsondata.items():
            if not is_error:
                setattr(self, k, v)
            else:
                setattr(self, k, None)
        return is_error, errors

    def __init__(self, request):
        """
        get the client ip from the request META
        """
        self.errors = None
        self.ip = None
        self.ip_source = 'unknown'
        self.is_error = None
        whichip = None

        ips = getattr(settings, 'FAKE_IP', None)
        if ips:
            whichip = "FAKE_IP"
            ip_alias = True
        elif isinstance(request, str):
            ips = ipaddress.ip_address(request).exploded
            whichip = "LITERAL_IP"
            ip_alias = True

        if not ips:
            whichip = "HTTP_X_FORWARDED_FOR"
            try:
                ips = request.META.get(whichip)
            except Exception as e:
                self.errors = self.errors + "%s = %s " % (whichip, str(e))
                pass
            if not ips:
                whichip = "REMOTE_ADDR"
                try:
                    ips = request.META.get(whichip)
                except Exception as e:
                    self.errors = self.errors + "%s = %s " % (whichip, str(e))
                    pass
                if not ips:
                    whichip = "HTTP_X_REAL_IP"
                    try:
                        ips = request.META.get(whichip)
                    except Exception as e:
                        self.errors = self.errors + "%s = %s " % (whichip, str(e))
                        pass
                    if not ips:
                        whichip = "X_REAL_IP"
                        try:
                            ips = request.META.get(whichip)
                        except Exception as e:
                            self.errors = self.errors + "%s = %s " % (whichip, str(e))
                            pass

        if ips:
            trueip, self.errors = self._resolve_ip(ips.split(','))
            if not self.errors:
                self.is_error = False
            else:
                whichip = None
        elif 'PYCHARM' in os.environ and not ip_alias:
            trueip = "127.0.0.1"
            whichip = None
        else:
            trueip = None
            whichip = None
        if trueip and not self.errors:
            try:
                ip_obj = ipaddress.ip_address(trueip)
            except Exception as e:
                self.errors = str(e)
                self.is_error = True
                pass
        else:
            ip_obj = None

        # expose some ip info as object attributes
        self.ip = ip_obj
        for n, v in inspect.getmembers(ip_obj):
            if "is_" in n and "_is_" not in n:
                setattr(self, n, v)
        if not self.is_error:
            is_geo_error, geo_errors = self._geolocate(ip_obj)
            if is_geo_error:
                self.is_error = is_geo_error
                self.errors = geo_errors


if __name__ == "__main__":
    if getattr(settings, "DEBUG", False):
        should_be_public   = SnakrIP("75.76.77.78")
        should_be_private  = SnakrIP("10.1.2.3")
        should_be_loopback = SnakrIP("127.0.0.1")
        dummy_line_for_debugger_breakpoint = True

