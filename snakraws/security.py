'''
security.py contains rudimentary bot protection and blacklist control for SnakrAWS; will enhance in the future.
'''
from django.core.cache import cache
from django.db.models.query_utils import Q

from snakraws import settings
from snakraws.utils import get_useragent, requested_directive
from snakraws.models import Blacklist


def get_useragent_or_403_if_bot(request):
    bot_name = None
    enabled = getattr(settings, "ENABLE_BOT_DETECTION", True)
    if enabled:
        if not requested_directive(request):
            lc_http_useragent = get_useragent(request, True)
            botblacklist = cache.get('botblacklist')
            if not botblacklist:
                botblacklist = settings.BOTBLACKLIST
                cache.set('botblacklist', botblacklist)
            botwhitelist = cache.get('botwhitelist')
            if not botwhitelist:
                botwhitelist = settings.BOTWHITELIST
                cache.set('botwhitelist', botwhitelist)
            whitelisted = False
            if botwhitelist:
                for match in botwhitelist:
                    if match in lc_http_useragent:
                        whitelisted = True
                        break
            if not whitelisted:
                if botblacklist:
                    for match in botblacklist:
                        if match in lc_http_useragent:
                            bot_name = match
                            break
    return bot_name, get_useragent(request, False)


def is_blacklisted(
        dimgeolocation=None,
        dimdevice=None,
        dimip=None,
        dimhost=None,
        dimreferer=None,
        dimuseragent=None):
    blquery = Q(is_active=True)
    try:
        if dimgeolocation:
            blquery = blquery & (Q(geo_id=dimgeolocation.id) | Q(geo_id=0))
    except:
        blquery = blquery & Q(geo_id=0)
        pass
    try:
        if dimdevice:
            blquery = blquery & (Q(device_id=dimdevice.id) | Q(device_id=0))
    except:
        blquery = blquery & Q(device_id=0)
        pass
    try:
        if dimhost:
            blquery = blquery & (Q(host_id=dimhost.id) | Q(host_id=0))
    except:
        blquery = blquery & Q(host_id=0)
        pass
    try:
        if dimip:
            blquery = blquery & (Q(ip_id=dimip.id) | Q(ip_id=0))
    except:
        blquery = blquery & Q(ip_id=0)
        pass
    try:
        if dimreferer:
            blquery = blquery & (Q(referer_id=dimreferer.id) | Q(referer_id=0))
    except:
        blquery = blquery & Q(referer_id=0)
        pass
    try:
        if dimuseragent:
            blquery = blquery & (Q(useragent_id=dimuseragent.id) | Q(useragent_id=0))
    except:
        blquery = blquery & Q(useragent_id=0)
        pass
    if Blacklist.objects.filter(blquery).exists():
        return True
    else:
        return False

