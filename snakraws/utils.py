'''
utils.py contains helper functions used throughout the codebase.
'''
from django.conf import settings

import random
import json
import mimetypes
from urllib.parse import urlparse, quote, unquote

from validator_collection import validators
from validator_collection.errors import InvalidURLError

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
    if digits_only:
        import string
        return ''.join(random.SystemRandom().choice(string.digits) for _ in range(s))
    else:
        return ''.join(random.SystemRandom().choice(settings.SHORTURL_PATH_ALPHABET) for _ in range(s))


def is_url_valid(myurl):
    test = myurl
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









