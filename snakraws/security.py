'''
security.py contains rudimentary bot protection and blacklist control for SnakrAWS; will enhance in the future.
'''

from django.core.cache import cache
from django.db.models.query_utils import Q

from snakraws import settings
from snakraws.utils import get_useragent, get_hash
from snakraws.models import Blacklist

def get_useragent_or_403_if_bot(request):
    #
    # at scale, this should be multithreaded/multi-processed in parallel
    # or implemented as a set of microservice lookups to a separate memcached lookup service
    #
    bot_name = None
    lc_http_useragent = get_useragent(request, True)
    botlist = cache.get('botlist')
    if not botlist:
        botlist = settings.BADBOTLIST
        cache.set('botlist', botlist)
    if botlist:
        for match in botlist:
            if match in lc_http_useragent:
                bot_name = match
                break
    return bot_name, get_useragent(request, False)


def is_blacklisted(ipobj, deviceid=None, hostname=None, referer=None, useragent=None):  # device support TBD
    blquery = Q(is_active=True)
    try:
        if ipobj.city_name_hash:
            blquery = blquery & (Q(city_id=ipobj.city_name_hash) | Q(city_id=0))
    except:
        blquery = blquery & Q(city_id=0)
        pass
    try:
        if ipobj.continent_name_hash:
            blquery = blquery & (Q(continent_id=ipobj.continent_name_hash) | Q(continent_id=0))
    except:
        blquery = blquery & Q(continent_id=0)
        pass
    try:
        if ipobj.country_name_hash:
            blquery = blquery & (Q(country_id=ipobj.country_name_hash) | Q(country_id=0))
    except:
        blquery = blquery & Q(country_id=0)
        pass
    try:
        if deviceid:
            blquery = blquery & (Q(device_id=get_hash(deviceid.strip().lower())) | Q(device_id=0))
    except:
        blquery = blquery & Q(device_id=0)
        pass
    try:
        if hostname:
            blquery = blquery & (Q(host_id=get_hash(hostname.strip().lower())) | Q(host_id=0))
    except:
        blquery = blquery & Q(host_id=0)
        pass
    try:
        if ipobj:
            blquery = blquery & (Q(ip_id=ipobj.ip_hash) | Q(ip_id=0))
    except:
        blquery = blquery & Q(ip_id=0)
        pass
    try:
        if ipobj.zip_hash:
            blquery = blquery & (Q(postalcode_id=ipobj.zip_hash) | Q(postalcode_id=0))
    except:
        blquery = blquery & Q(postalcode_id=0)
        pass
    try:
        if referer:
            blquery = blquery & (Q(referer_id=get_hash(referer.strip().lower())) | Q(referer_id=0))
    except:
        blquery = blquery & Q(referer_id=0)
        pass
    try:
        if ipobj.region_name_hash:
            blquery = blquery & (Q(region_id=ipobj.region_name_hash) | Q(region_id=0))
    except:
        blquery = blquery & Q(region_id=0)
        pass
    try:
        if useragent:
            blquery = blquery & (Q(useragent_id=get_hash(useragent.lower())) | Q(useragent_id=0))
    except:
        blquery = blquery & Q(useragent_id=0)
        pass
    if Blacklist.objects.filter(blquery).exists():
        return True
    else:
        return False
