'''
utils.py contains helper functions used throughout the codebase.
'''

import re
import random
import json
import mimetypes
from urllib.parse import urlparse, quote, unquote
from string import digits
import requests

from django.conf import settings
from django.utils.translation import ugettext_lazy as _


from profanity_check import predict as PredictProfanity
from profanity_filter import ProfanityFilter

from validator_collection import validators
from validator_collection.errors import InvalidURLError

from bs4 import BeautifulSoup, Doctype as BS4Doctype


# DO NOT CHANGE THESE CONSTANTS AT ALL EVER
# See http://www.isthe.com/chongo/tech/comp/fnv/index.html for math-y details.
FNV_64_PRIME = 1099511628211
FNV1_64A_INIT = 14695981039346656037
BIGGEST_64_INT = 9223372036854775807
SMALLEST_64_INT = -9223372036854775808

BAD_THREE_LETTER_WORDS = [
    "ass",
    "fuc",
    "fuk",
    "fuq",
    "fux",
    "fck",
    "coc",
    "cok",
    "coq",
    "kox",
    "koc",
    "kok",
    "koq",
    "cac",
    "cak",
    "caq",
    "kac",
    "kak",
    "kaq",
    "dic",
    "dik",
    "diq",
    "dix",
    "dck",
    "pns",
    "psy",
    "fag",
    "fgt",
    "ngr",
    "nig",
    "cnt",
    "knt",
    "sht",
    "dsh",
    "twt",
    "bch",
    "cum",
    "clt",
    "kum",
    "klt",
    "suc",
    "suk",
    "suq",
    "sck",
    "lic",
    "lik",
    "liq",
    "lck",
    "jiz",
    "jzz",
    "gay",
    "gey",
    "gei",
    "gai",
    "vag",
    "vgn",
    "sjv",
    "fap",
    "prn",
    "lol",
    "jew",
    "joo",
    "gvr",
    "pus",
    "pis",
    "pss",
    "snm",
    "tit",
    "fku",
    "fcu",
    "fqu",
    "hor",
    "slt",
    "jap",
    "wop",
    "kik",
    "kyk",
    "kyc",
    "kyq",
    "dyk",
    "dyq",
    "dyc",
    "kkk",
    "jyz",
    "prk",
    "prc",
    "prq",
    "mic",
    "mik",
    "miq",
    "myc",
    "myk",
    "myq",
    "guc",
    "guk",
    "guq",
    "giz",
    "gzz",
    "sex",
    "sxx",
    "sxi",
    "sxe",
    "sxy",
    "xxx",
    "wac",
    "wak",
    "waq",
    "wck",
    "pot",
    "thc",
    "vaj",
    "vjn",
    "nut",
    "std",
    "lsd",
    "poo",
    "azn",
    "pcp",
    "dmn",
    "orl",
    "anl",
    "ans",
    "muf",
    "mff",
    "phk",
    "phc",
    "phq",
    "xtc",
    "tok",
    "toc",
    "toq",
    "mlf",
    "rac",
    "rak",
    "raq",
    "rck",
    "sac",
    "sak",
    "saq",
    "pms",
    "nad",
    "ndz",
    "nds",
    "wtf",
    "sol",
    "sob",
    "fob",
    "sfu",
]

def get_hash(string):
    """
    FNV1a hash algo. Generates a (signed) 64-bit FNV1a hash.
    See http://www.isthe.com/chongo/tech/comp/fnv/index.html for math-y details.
    """
    encoded_trimmed_string = string.strip().encode('utf8')
    assert isinstance(encoded_trimmed_string, bytes)
    i64 = FNV1_64A_INIT
    for byte in encoded_trimmed_string:
        i64 = i64 ^ byte
        i64 = (i64 * FNV_64_PRIME) % (2 ** 64)
    # wrap the result into the full signed BIGINT range of the underlying RDBMS
    if i64 > BIGGEST_64_INT:
        i64 = SMALLEST_64_INT + (i64 - BIGGEST_64_INT - 1)  # optimized CPU ops
    return i64


def get_keyval(jsonval, skey):
    val = "invalid"
    if isinstance(jsonval, str):
        if jsonval == "":
            val = "missing"
        else:
            try:
                val = json.loads(jsonval)
            except Exception as ex:
                pass
    if isinstance(jsonval, dict):
        val = jsonval[skey]
    return get_hash(val), val


def get_setting(setting, default=None):
    return getattr(settings, setting, default)


def get_encodedurl(myurl):
    """Returns an encoded version of the passed URL."""
    return quote(myurl).replace('%3A//', '://')


def get_decodedurl(myurl):
    """Returns an decoded version of the passed URL."""
    return unquote(myurl)


def get_longurlhash(myurl):
    """Returns a FNV1a hash of the quoted version of the passed URL."""
    x = get_hash(quote(myurl))
    return x


def get_shorturlhash(myurl):
    """Returns a FNV1a hash of the UNquoted version of the passed URL."""
    x = get_hash(unquote(myurl))
    return x


def get_shortpathcandidate(**kwargs):
    digits_only = kwargs.pop("digits_only", False)
    s = get_setting('SHORTURL_PATH_SIZE')
    while True:
        if digits_only:
            shortpath = ''.join(random.SystemRandom().choice(digits) for _ in range(s))
        else:
            shortpath = ''.join(random.SystemRandom().choice(settings.SHORTURL_PATH_ALPHABET) for _ in range(s))
        if is_shortpath_valid(shortpath):
            break
    return shortpath


def get_wsgirequest_headers(request):
    headers = {}
    if request:
        regex = re.compile('^HTTP_')
        headers = dict((regex.sub('', header).replace("_", "-"), value)
                       for (header, value) in request.META.items()
                       if header.startswith('HTTP_') and header != 'HTTP_HOST')
    return headers


def fetch_doctype(targetdoc):
    dt = None

    def __mt(x):
        return {
            'text/html': 'html',
            'application/pdf': 'pdf',
            'text/plain': 'text',
            }.get(x.split(";")[0], None)

    if 'content-type' in targetdoc.headers:
        dt = __mt(targetdoc.headers['content-type'])
    return dt


def get_target_meta(url, request=None):

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

    title = url
    description = ""
    image_url = ""
    site_name = ""
    doctype, target, soup = inspect_url(url, request)
    if doctype and target:
        if target.status_code == 200:
            if doctype == "html":
                if soup:
                    title = _get_html_title(soup)
                    description = _get_html_description(soup)
                    image_url = _get_image_url(soup)
                    site_name = _get_site_name(soup)
            elif doctype == "pdf":
                title = _get_pdf_title(target.content)
    if not title:
        title = url
    title = fit_text(title, "", 100)
    return title, description, image_url, site_name


def is_shortpath_valid(shortpath):
    test = shortpath.lower().strip()
    reserved_paths = getattr(settings, "RESERVED_PATHS", "home")
    if test in reserved_paths:
        return False
    if is_profane(test):
        return False
    return True


def is_url_valid(test):
    is_valid = False
    try:
        # 2-21-2019 bml workaround for current bug in validator-collection v1.3.2 (reported as issue #28)
        # where http(s)://localhost:port-number.... is flagged as invalid
        if not (getattr(settings, "SITE_MODE", "prod") == "dev" and '://localhost:' in test):
            test = validators.url(test, allow_special_ips=True)
        if test:
            is_valid = True
    except InvalidURLError:
        pass
    return is_valid


def urlparts(url="http://www.dummyurl.com"):
    return urlparse(url)


def get_json(request, key):
    try:
        json_data = json.loads(request.body)
    except:
        json_data = None
        pass
    try:
        if json_data:
            if json_data[key]:
                return json_data[key]
    except:
        pass
    return None


def is_image(url):
    try:
        if mimetypes.guess_type(url)[0].split('/')[0] == 'image':
            return True
    except:
        pass
    return False


def true_or_false(value):
    def switch(x):
        return {
            str(value)[0:1].upper() in ['T','Y','1']: True,
            str(value).upper() in ['TRUE','YES']: True,
        }.get(x, False)
    return switch(value)


def get_useragent(request, normalize=True):
    rtn = request.META.get('HTTP_USER_AGENT', 'unknown')
    return rtn.lower() if normalize else rtn


def get_host(request, normalize=True):
    rtn = request.META.get('HTTP_HOST', 'unknown')
    return rtn.lower() if normalize else rtn


def get_referer(request, normalize=True):
    rtn = request.META.get('HTTP_REFERER', 'unknown')
    return rtn.lower() if normalize else rtn


def get_meta(request, normalize=True):
    return get_host(request, normalize), get_useragent(request, normalize), get_referer(request, normalize)


def get_shortening_postback():
    return '^%s/?$' % getattr(settings, 'SHORTENING_POSTBACK', 'shorten')


def get_shortening_redirect():
    if getattr(settings, "SSL_ENABLED", False):
        return 'https://%s/%s' % (getattr(settings, 'SECURE_SHORTURL_HOST'), getattr(settings, 'SHORTENING_POSTBACK', 'shorten'))
    else:
        return 'http://%s/%s' % (getattr(settings, 'SHORTURL_HOST'), getattr(settings, 'SHORTENING_POSTBACK', 'shorten'))


def get_admin_postback():
    return '^%s/?' % getattr(settings, 'ADMIN_POSTBACK', 'admin')


def get_jet_postback():
    return '^%s/?' % getattr(settings, 'JET_POSTBACK', 'jet')


def get_jet_dashboard_postback():
    return '^%s/?' % getattr(settings, 'JET_DASHBOARD_POSTBACK', '/jet/dashboard')


def get_message(key):
    key = key.strip().upper()
    molr = getattr(settings, "MESSAGE_OF_LAST_RESORT", _("SEVERE ERROR: EXPECTED MESSAGE NOT FOUND!"))
    messages = getattr(settings, "CANONICAL_MESSAGES", "{'%s': '%s'}" % (key, molr))
    if key in messages:
        message = messages[key]
        if '%pl' in message:
            if getattr(settings, "ENABLE_LONG_URL_PROFANITY_CHECKING", False) or getattr(settings, "ENABLE_SHORT_URL_PROFANITY_CHECKING", False):
                message = message.replace("%pl", getattr(settings, "LANGUAGE_ADDENDUM", _(" or contains language flagged as inappropriate")))
            else:
                message = message.replace("%pl", "")
    else:
        message = molr
    return message


def get_all_substrings(input_string, min_length=1):
    length = len(input_string)
    if len(input_string) > min_length:
        return [input_string[i:j + 1] for i in range(length) for j in range(i+(min_length - 1), length)]
    else:
        return ""


def is_profane(url):

    if len(url) < 3:
        return False

    if getattr(settings, "ENABLE_FAST_PROFANITY_CHECKING", True):
        parts = urlparse(get_decodedurl(url))
        partslist = []
        if not (parts.path or parts.netloc):
            raise InvalidURLError("Badly formatted URL passed to is_url_profane")
        splitters = r"\.|\/|\_|\-|\~|\$|\+|\!|\*|\(|\)|\,"   # all the URL-safe characters, escaped
        if parts.netloc:
            partslist = partslist + re.split(splitters, parts.netloc)
        if parts.path:
            partslist = partslist + re.split(splitters, parts.path)
        if parts.query:
            partslist = partslist + re.split(splitters, parts.query)

        # speed optimization
        check4btlw = True
        stringlist = []
        for item in partslist:
            if len(item) > 0:
                if len(item) > 5:
                    check4btlw = False
                for substring in get_all_substrings(item, 2):
                    if len(substring) > 0:
                        stringlist.append(substring)
        partslist = list(dict.fromkeys(stringlist))  # removes dupes

        if check4btlw:
            for part in partslist:
                if part in BAD_THREE_LETTER_WORDS:
                    return True

        score = PredictProfanity(partslist)
        if score.any() == 1:
            return True

        if getattr(settings, "ENABLE_DEEP_PROFANITY_CHECKING", True):
            pf = ProfanityFilter()
            for part in partslist:
                if pf.is_profane(part):
                    return True

    return False


def fit_text(text, suffix="", maxlen=300):
    ltmax = maxlen - len(suffix) - 1
    if len(text) > ltmax:
        return text[:ltmax - 3] + '... ' + suffix
    else:
        return text + ' ' + suffix


def get_request_path(request):
    return urlparse(get_decodedurl(request.build_absolute_uri())).path


def requested_robots_txt(request):
    return get_request_path(request) == "/robots.txt"


def requested_ads_txt(request):
    return get_request_path(request) == "/ads.txt"


def requested_directive(request):
    return requested_robots_txt(request) or requested_ads_txt(request)


def requested_last(request):
    return get_request_path(request) == "/last"


def inspect_url(url, request=None):
    doctype = None
    soup = None
    target = None
    try:
        if request:
            target = requests.get(url, data=None, headers=get_wsgirequest_headers(request))
        else:
            target = requests.get(url, data=None)
    except:
        pass
    if target:
        if target.status_code == 200:
            doctype = fetch_doctype(target)
            if doctype == 'html':
                try:
                    soup = BeautifulSoup(target.content, "html.parser")
                except:
                    soup = None
                    pass
    return doctype, target, soup

