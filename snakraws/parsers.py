'''
Parser contains methods to open the resource located at the long URL target and extract metadata such as document title
for return in the JSON data with the short URL.
'''

from urllib.request import build_opener
import mimetypes

from snakraws import settings

from bs4 import BeautifulSoup, Doctype
from opengraph import OpenGraph
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument


class Parsers:

    def __init__(self):
        return

    def _robobrowser(self):
        opener = build_opener()
        # updated 2019-02-13
        opener.addheaders = [('User-agent', settings.USER_AGENT)]
        return opener

    def _open_url(self, documenturl):
        return self._robobrowser().open(documenturl).read()

    def _get_parsedHTMLcontents(self, documenturl):
        contents = self._open_url(documenturl)
        parsed_contents = BeautifulSoup(contents.decode('utf-8'), "html.parser")
        return parsed_contents

    def _get_doctype(self, document):
        parsed_contents = self._get_parsedHTMLcontents(document)
        items = [item for item in parsed_contents if isinstance(item, Doctype)]
        return items[0].string if items else None

    def get_title(self, document):
        mime_type = mimetypes.guess_type(document, strict=True)[0]
        if mime_type:

            def mt(x):
                return {
                    'text/html': self._get_html_title(document),
                    'application/pdf': self._get_pdf_title(document),
                    }.get(x, None)

            return mt(mime_type)

        else:

            doc_type = self._get_doctype(document)

            def dt(x):
                return {
                    'html': self._get_html_title(document),
                    }.get(x, None)

            return dt(doc_type)

    def _get_html_title(self, document):
        #
        # if settings.OGTITLE = True, get the OpenGraph title meta tag value and include it in the output
        #
        title = None
        target = None
        try:
            target = OpenGraph(url=document)
            if target:
                title = target.title
        except:
            pass
        if not title:
            try:
                parsed_longurl_html = self._get_parsedHTMLcontents(document)
                try:
                    title = parsed_longurl_html.title.string.unquote()
                except:
                    title = None
                    pass
            except:
                pass
        return title

    def _get_pdf_title(self, document):
        title = None
        try:
            pdfdoc = self._open_url(document)
            pdfparser = PDFParser(pdfdoc)
            pdfparseddoc = PDFDocument(pdfparser)
            title = pdfparseddoc.info["title"]
        except:
            pass
        return title
