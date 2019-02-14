'''
utils.py contains helper functions used throughout the codebase.
'''
from django.conf import settings
from django.core.validators import URLValidator

import random
from urllib.parse import urlparse, quote, unquote
import json
import mimetypes


_URL_VALIDATOR = URLValidator()

# DO NOT CHANGE THESE CONSTANTS AT ALL EVER
# See http://www.isthe.com/chongo/tech/comp/fnv/index.html for math-y details.
FNV_64_PRIME = 1099511628211
FNV1_64A_INIT = 14695981039346656037
BIGGEST_64_INT = 9223372036854775807
SMALLEST_64_INT = -9223372036854775808


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
    return quote(myurl).encode('utf8').replace('%3A//', '://')


def get_decodedurl(myurl):
    """Returns an decoded version of the passed URL."""
    return unquote(myurl.decode('utf8'))


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
    if digits_only:
        import string
        return ''.join(random.SystemRandom().choice(string.digits) for _ in range(s))
    else:
        return ''.join(random.SystemRandom().choice(settings.SHORTURL_PATH_ALPHABET) for _ in range(s))


def is_url_valid(myurl):
    rtn = True
    try:
        # workaroud for django 1.5.11 bug on %20 encoding causing urlvalidation to fail
        valid = _URL_VALIDATOR(get_decodedurl(myurl.replace("%20", "_")))
    except:
        rtn = False
        pass
    return rtn


def initurlparts():
    return urlparse('http://www.dummyurl.com')  # this is a django 1.5.11 bug workaround


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


def get_meta(request, normalize=True):
    http_host = request.META.get('HTTP_HOST', 'unknown')
    http_useragent = request.META.get('HTTP_USER_AGENT', 'unknown')
    http_referer = request.META.get('HTTP_REFERER', 'unknown')
    if normalize:
        return http_host.lower(), http_useragent.lower(), http_referer.lower()
    else:
        return http_host, http_useragent, http_referer







