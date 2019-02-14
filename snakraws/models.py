'''
models.py contains the persistence logic for Snakr.
'''
from django.db import models
from django.db import transaction as xaction, IntegrityError
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _

from ipaddress import IPv6Interface, IPv4Interface, IPv6Address, IPv4Address, ip_interface

import settings
from snakraws.utils import get_hash

TABLE_PREFIX = 'snakraws'

EVENT_TYPE = (
    ('U', _('Uncategorized')),
    ('B', _('Blacklisted')),
    ('D', _('Debug')),
    ('E', _('Error')),
    ('I', _('Information')),
    ('L', _('200 New Long URL Submitted')),
    ('R', _('200 Existing Long URL Resubmitted')),
    ('S', _('301 Short URL Redirect')),
    ('W', _('Warning')),
    ('X', _('Exception')),
)

DEFAULT_EVENT_TYPE = 'U'

HTTP_STATUS_CODE = (
    (200, _('OK (200)')),
    (301, _('Redirect (301/302)')),
    (400, _('Bad Request (400)')),
    (403, _('Forbidden (403)')),
    (404, _('Not Found (404)')),
    (422, _('Unprocessable Entity (422)')),
    (500, _('Server Exception (500)')),
    (0,   _('No response')),
    (-1,  _('N/A')),
)


DEFAULT_HTTP_STATUS_CODE = 403

URL_STATUS_CODE = (
    ('A', _('Active (301)')),
    ('B', _('Blacklisted (403)')),
    ('I', _('Inactive (404)')),
)

DEFAULT_URL_ID = get_hash('unknown')
UNSPECIFIED_URL_ID = get_hash('unspecified')

_USE_EXISTS = getattr(settings, 'USE_IF_DIM_EXISTS', False)


class DimCity(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the city of origin of the event, if any',
            primary_key=True,
            null=False)
    name = models.CharField(
            verbose_name='The city of origin of the event, if any.',
            max_length=100,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcities' % TABLE_PREFIX

    def __str__(self):
        return self.city

    def __unicode__(self):
        return self.city


class DimContinent(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the country of origin of the event, if any',
            primary_key=True,
            null=False)
    name = models.CharField(
            verbose_name='The continent of origin of the event, if any.',
            max_length=100,
            null=False)
    code = models.CharField(
            verbose_name='Abbreviated version',
            min_length=2,
            max_length=2,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcountries' % TABLE_PREFIX

    def __str__(self):
        return self.country

    def __unicode__(self):
        return self.country


class DimCountry(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the country of origin of the event, if any',
            primary_key=True,
            null=False)
    name = models.CharField(
            verbose_name='The country of origin of the event, if any.',
            max_length=100,
            null=False)
    code = models.CharField(
            verbose_name='Abbreviated version',
            min_length=2,
            max_length=2,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcountries' % TABLE_PREFIX

    def __str__(self):
        return self.country

    def __unicode__(self):
        return self.country


class DimDevice(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the country of origin of the event, if any',
            primary_key=True,
            null=False)
    deviceid = models.CharField(
            verbose_name='Unique device ID',
            max_length=40,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimdevices' % TABLE_PREFIX

    def __str__(self):
        return self.deviceid

    def __unicode__(self):
        return self.deviceid


class DimHost(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the HTTP_HOST value in the event, if any',
            primary_key=True,
            null=False)
    hostname = models.CharField(
            verbose_name='The HTTP_HOST value in the event, if any.',
            max_length=253,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimhosts' % TABLE_PREFIX

    def __str__(self):
        return self.host

    def __unicode__(self):
        return self.host


class DimIP(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the IPv4 or IPv6 of the event, if any',
            primary_key=True,
            null=False)
    ip = models.CharField(
            verbose_name='The IPv4 or IPv6 address of the event, if any.',
            max_length=39,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimips' % TABLE_PREFIX

    def __str__(self):
        return self.ip

    def __unicode__(self):
        return self.ip

    @property
    def is_ipv4(self):
        return isinstance(IPv4Interface, ip_interface(self.ip.encode('utf8')))

    @property
    def is_ipv6(self):
        return isinstance(IPv6Interface, ip_interface(self.ip.encode('utf8')))

    @property
    def ipv4(self):
        if self.is_ipv6:
            v4 = self.ipv6.ipv4_mapped
            if not v4:
                v4 = self.ipv6.sixtofour
        else:
            v4 = IPv4Address(self.ip.encode('utf8'))
        return v4

    @property
    def ipv6(self):
        if self.is_ipv4:
            return None
        return IPv6Address(self.ip.encode('utf8'))

    @property
    def address(self):
        if self.is_ipv6:
            return self.ipv6.ip.exploded
        else:
            return self.ipv4.ip.exploded


class DimPostalCode(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the postal code of origin of the event, if any',
            primary_key=True,
            null=False)
    postalcode = models.CharField(
            verbose_name='The postal (zip) code of origin of the event, if any.',
            max_length=32,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimpostalcodes' % TABLE_PREFIX

    def __str__(self):
        return self.postalcode

    def __unicode__(self):
        return self.postalcode


class DimReferer(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique id',
            primary_key=True,
            null=False)
    referer = models.CharField(
            verbose_name='HTTP referer, if any',
            max_length=1024,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimreferers' % TABLE_PREFIX

    def __str__(self):
        return self.referer

    def __unicode__(self):
        return self.referer


class DimRegion(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the region of origin of the event, if any',
            primary_key=True,
            null=False)
    name = models.CharField(
            verbose_name='The region of origin of the event, if any.',
            max_length=100,
            null=False)
    code = models.CharField(
            verbose_name='Abbreviated version',
            min_length=2,
            max_length=2,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimregions' % TABLE_PREFIX

    def __str__(self):
        return self.region

    def __unicode__(self):
        return self.region


class DimUserAgent(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the HTTP_USER_AGENT value in the event, if any',
            primary_key=True,
            null=False)
    useragent = models.CharField(
            verbose_name='The HTTP_USER_AGENT value in the event, if any.',
            max_length=8192,
            null=False)
    is_blacklisted = models.BooleanField(
            default=False,
            null=True)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimuseragents' % TABLE_PREFIX

    def __str__(self):
        return self.useragent

    def __unicode__(self):
        return self.useragent


class DimLongURL(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the long URL',
            primary_key=True,
            null=False)
    longurl = models.CharField(
            verbose_name='encoded, quoted version of the submitted long URL',
            max_length=4096,
            validators=[URLValidator()],
            null=False,
            blank=False)
    originally_encoded = models.BooleanField(
            verbose_name='True=the long URL was encoded when submitted; False=otherwise',
            null=False)
    is_active = models.BooleanField(
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimlongurls' % TABLE_PREFIX

    def __str__(self):
        return self.longurl

    def __unicode__(self):
        return self.longurl


class DimShortURL(models.Model):
    id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the short URL',
            primary_key=True,
            null=False)
    longurl_id = models.BigIntegerField(
            verbose_name='unique 64-bit integer binary hash value of the long URL redirected to by the short URL',
            unique=True,
            null=False)
    shorturl = models.CharField(
            verbose_name='unencoded, unquoted version of the short URL generated',
            max_length=40,
            validators=[URLValidator()],
            null=False,
            blank=False)
    shorturl_path_size = models.SmallIntegerField(
            verbose_name='value of settings.SHORTURL_PATH_SIZE when short URL was generated',
            null=True)
    compression_ratio = models.DecimalField(
            verbose_name='ratio of compression long vs short',
            max_digits=10,
            decimal_places=2,
            null=True)
    is_active = models.BooleanField(
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimshorturls' % TABLE_PREFIX

    def __str__(self):
        return self.shorturl

    def __unicode__(self):
        return self.shorturl


class FactEvent(models.Model):
    id = models.AutoField(
            verbose_name='unique 64-bit integer autoincrement; gives order of events (200s, 302s, 400s, 404s, 500s...) as they occurred',
            primary_key=True,
            null=False)
    event_yyyymmdd = models.CharField(
            verbose_name='date that the event was inserted into the table',
            min_length=8,
            max_length=8
    )
    event_hhmiss = models.CharField(
            verbose_name='time that the event was inserted into the table',
            min_length=6,
            max_length=6
    )
    event_type = models.CharField(
            verbose_name='Type of event logged. See models.FactEvents.EVENT_TYPE for enumeration details.',
            min_length=1,
            max_length=1,
            null=False,
            choices=EVENT_TYPE)
    http_status_code = models.SmallIntegerField(
            verbose_name='the HTTP status code, if any, on the event, e.g. 200, 302, 404, etc.',
            null=False,
            choices=HTTP_STATUS_CODE
    )
    info = models.CharField(
            verbose_name='Human-readable text about the event, if any.',
            max_length=8192,
            null=False)
    longurl_id = models.ForeignKey(
            'DimLongURL',
            verbose_name='unique 64-bit integer binary hash value of the long URL redirected to by the short URL associated with the event, if any',
            null=False,
            on_delete = models.DO_NOTHING)
    shorturl_id = models.ForeignKey(
            'DimShortURL',
            verbose_name='unique 64-bit integer binary hash value of the short URL associated with the event, if any',
            null=False,
            on_delete=models.DO_NOTHING)
    ip_id = models.ForeignKey(
            'DimIP',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    useragent_id = models.ForeignKey(
            'DimUserAgent',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    referer_id = models.ForeignKey(
            'DimReferer',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    host_id = models.ForeignKey(
            'DimHost',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    device_id = models.ForeignKey(
            'DimDevice',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    city_id = models.ForeignKey(
            'DimCity',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    region_id = models.ForeignKey(
            'DimRegion',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    postalcode_id = models.ForeignKey(
            'DimPostalCode',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    country_id = models.ForeignKey(
            'DimCountry',
            verbose_name='unique 64-bit integer binary hash value',
            null=False,
            on_delete=models.DO_NOTHING)
    blacklisted_csv = models.CharField(
            verbose_name='CSV list of fieldnames, if any, blacklisted at the time of the event',
            max_length=256,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_factevents' % TABLE_PREFIX

    def __str__(self):
        return "%d" % self.id

    def __unicode__(self):
        return "%d" % self.id


@xaction.atomic
def save(dt, event_type, status_code, info, shorturl_id, longurl_id, ipobj, host, useragent, referer):
    blacklist_csv = ''

    def _bl(blacklist_csv, str):
        if blacklist_csv:
            return '%s,%s' % (blacklist_csv, str)
        else:
            return str

    # dimension save helper function here to keep it within the scope of the transaction
    def _save_dimension(modelclass, **kwargs):
        values = {}
        # assume 1st kwarg is the value to use to generate the hashkey
        for k, v in kwargs:
            key = v
            break
        if not key:
            key = "missing"
        hash_key = get_hash(' '.join(str(key).split()).lower())
        for f in modelclass._meta.fields:
            fname = f.name
            lname = fname.lower()
            if lname != "id":
                value = None
                for k, v in kwargs:
                    if k.lower() == lname:
                        value = v
                        break
                if value:
                    values[fname] = value
        is_dim_blacklisted = False
        try:
            if modelclass.objects.filter(id=hash_key).exists():
                is_dim_blacklisted = modelclass.objects.filter(id=hash_key).values_list("is_blacklisted", flat=True)[0]
            else:
                modelclass.save(id=hash_key, update_fields=values)
        except IntegrityError:
            pass
        return hash_key, is_dim_blacklisted

    city_hash, bl = _save_dimension(DimCity, name=ipobj.city)
    blacklist_csv = _bl(blacklist_csv, 'city') if bl else blacklist_csv

    continent_hash, bl = _save_dimension(DimContinent, name=ipobj.continent_name, code=ipobj.continent_code)
    blacklist_csv = _bl(blacklist_csv, 'continent') if bl else blacklist_csv

    country_hash, bl = _save_dimension(DimCountry, name=ipobj.country_name, code=ipobj.country_code)
    blacklist_csv = _bl(blacklist_csv, 'country') if bl else blacklist_csv

    # device support TBD
    device = "unknown"
    device_hash = _save_dimension(DimDevice, device=device)

    host_hash, bl = _save_dimension(DimHost, host=host)
    blacklist_csv = _bl(blacklist_csv, 'host') if bl else blacklist_csv

    ip_hash, bl = _save_dimension(DimIP, ip=ipobj.ip)
    blacklist_csv = _bl(blacklist_csv, 'ip') if bl else blacklist_csv

    postalcode_hash, bl = _save_dimension(DimPostalCode, postalcode=zip)
    blacklist_csv = _bl(blacklist_csv, 'postalcode') if bl else blacklist_csv

    referer_hash, bl = _save_dimension(DimReferer, referer=referer)
    blacklist_csv = _bl(blacklist_csv, 'referer') if bl else blacklist_csv

    region_hash, bl = _save_dimension(DimRegion, name=ipobj.region_name, code=ipobj.region_code)
    blacklist_csv = _bl(blacklist_csv, 'region') if bl else blacklist_csv

    useragent_hash = _save_dimension(DimUserAgent, useragent=useragent)
    blacklist_csv = _bl(blacklist_csv, 'useragent') if bl else blacklist_csv

    if blacklist_csv:
        status_code = -403
        info = settings.CANONICAL_MESSAGES["BLACKLISTED"]
        event_type = 'B'
    abs_status_code = abs(status_code)

    event = FactEvent(
            event_yyyymmdd=dt.strftime('%Y%m%d'),
            event_hhmiss=dt.strftime('%H%M%S'),
            event_type=event_type,
            http_status_code=abs_status_code,
            info=info,
            longurl_id=longurl_id,
            shorturl_id=shorturl_id,
            city_id=city_hash,
            continent_id=continent_hash,
            country_id=country_hash,
            device_id=device_hash,
            host_id=host_hash,
            ip_id=ip_hash,
            postalcode_id=postalcode_hash,
            referer_id=referer_hash,
            useragent_id=useragent_hash,
            blacklisted_csv=blacklist_csv
    )

    event.save()
    return event.id, status_code


