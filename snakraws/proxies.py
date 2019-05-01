import requests
from itertools import cycle
import ipaddress
import logging

from django.conf import settings

from bs4 import BeautifulSoup


class Proxies:

    def __init__(self):  #, request):

        def _gt(c):
            return c.getText().strip().lower()

        httpproxies = []
        self.http_proxy_pool = cycle(httpproxies)
        httpsproxies = []
        self.http_proxy_pool = cycle(httpsproxies)
        plurl = 'https://free-proxy-list.net/'
        doctype, target, soup = self._inspect_url(plurl)  #, request=request)
        if soup:
            try:
                table = soup.find('table', attrs={'id': 'proxylisttable'})
                table_body = table.find('tbody') if table else None
                rows = table_body.find_all('tr') if table_body else None
                for row in rows:
                    cell = row.findChildren('td')
                    if cell[0] and cell[1] and cell[2] and cell[6]:
                        if _gt(cell[2]) == 'us':
                            ip = _gt(cell[0])
                            port = _gt(cell[1])
                            if ipaddress.ip_address(ip):
                                if isinstance(int, port):
                                    if port > 0:
                                        proxy = '%s:%s' % (ip, port)
                                        is_https = _gt(cell[6])
                                        if is_https == 'yes':
                                            httpsproxies.append(proxy)
                                        else:
                                            httpproxies.append(proxy)
            except Exception as e:
                logging.log(logging.WARNING, "ERROR parsing proxy web site: %s" % str(e))
                httpproxies = None
                httpsproxies = None
                pass

        if httpproxies:
            httpproxies = list(set(httpproxies))   # remove dupes, if any
            httpproxies.sort()
            self.http_proxy_pool = cycle(httpproxies)

        if httpsproxies:
            httpsproxies = list(set(httpsproxies))  # remove dupes, if any
            httpsproxies.sort()
            self.https_proxy_pool = cycle(httpsproxies)

        return

    @property
    def next_http_proxy(self):
        return next(self.http_proxy_pool) if self.http_proxy_pool else None

    @property
    def next_https_proxy(self):
        return next(self.https_proxy_pool) if self.https_proxy_pool else None

    @property
    def get(self):
        proxies = {}
        if self.http_proxy_pool:
            proxies.update({"http":  self.next_http_proxy})
        if self.https_proxy_pool:
            proxies.update({"https":  self.next_https_proxy})
        return proxies

    @staticmethod
    def _fetch_doctype(targetdoc):
        dt = None

        def __mt(x):
            return {
                'text/html': 'html',
                'application/pdf': 'pdf',
                'text/plain': 'text',
            }.get(x, None)

        if 'content-type' in targetdoc.headers:
            if ';' in targetdoc.headers['content-type']:
                dt = targetdoc.headers['content-type'].split(";")[0]
            else:
                dt = targetdoc.headers['content-type']
            dt = __mt(dt)
        return dt

    # @staticmethod
    # def _get_wsgirequest_headers(request):
    #     headers = {}
    #     if request:
    #         regex = re.compile('^HTTP_')
    #         headers = dict((regex.sub('', header).replace("_", "-"), value)
    #                        for (header, value) in request.META.items()
    #                        if header.startswith('HTTP_') and header != 'HTTP_HOST')
    #     return headers

    def _inspect_url(self, url):
        doctype = None
        soup = None
        target = None
        try:
            #if request:
            #    target = requests.get(url, data=None)  #, headers=self._get_wsgirequest_headers(request))
            #else:
            target = requests.get(url, data=None)
        except Exception as e:
            pass
        if target:
            if target.status_code == 200:
                doctype = self._fetch_doctype(target)
                if doctype == 'html':
                    try:
                        soup = BeautifulSoup(target.content, "html.parser")  #, from_encoding="iso-8859-1")
                    except:
                        soup = None
                        pass
        return doctype, target, soup


if __name__ == "__main__":
    if getattr(settings, "DEBUG", False):
        p = Proxies()
        print(p.get)


