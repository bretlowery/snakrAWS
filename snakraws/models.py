'''
models.py contains the persistence logic for Snakr.
'''
from django.db import models
from django.db import transaction as xaction, IntegrityError
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from ipaddress import IPv6Interface, IPv4Interface, IPv6Address, IPv4Address, ip_interface

from snakraws import settings
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
    (0, _('No response')),
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
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    name = models.CharField(
            unique=True,
            max_length=100,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcities' % TABLE_PREFIX

    def __str__(self):
        return self.city

    def __unicode__(self):
        return self.city


class DimContinent(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    name = models.CharField(
            unique=True,
            max_length=100,
            null=False)
    code = models.CharField(
            unique=True,
            max_length=2,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcountries' % TABLE_PREFIX

    def __str__(self):
        return self.country

    def __unicode__(self):
        return self.country


class DimCountry(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    name = models.CharField(
            unique=True,
            max_length=100,
            null=False)
    code = models.CharField(
            unique=True,
            max_length=2,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimcountries' % TABLE_PREFIX

    def __str__(self):
        return self.country

    def __unicode__(self):
        return self.country


class DimDevice(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    deviceid = models.CharField(
            unique=True,
            max_length=40,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimdevices' % TABLE_PREFIX

    def __str__(self):
        return self.deviceid

    def __unicode__(self):
        return self.deviceid


class DimHost(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    hostname = models.CharField(
            unique=True,
            max_length=253,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimhosts' % TABLE_PREFIX

    def __str__(self):
        return self.host

    def __unicode__(self):
        return self.host


class DimIP(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    ip = models.CharField(
            unique=True,
            max_length=39,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimips' % TABLE_PREFIX

    def __str__(self):
        return self.ip

    def __unicode__(self):
        return self.ip

    def save(self, *args, **kwargs):
        super(DimIP, self).save(*args, **kwargs)

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
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    postalcode = models.CharField(
            unique=True,
            max_length=32,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimpostalcodes' % TABLE_PREFIX

    def __str__(self):
        return self.postalcode

    def __unicode__(self):
        return self.postalcode


class DimReferer(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    referer = models.CharField(
            max_length=1024,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimreferers' % TABLE_PREFIX

    def __str__(self):
        return self.referer

    def __unicode__(self):
        return self.referer


class DimRegion(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    name = models.CharField(
            unique=True,
            max_length=100,
            null=False)
    code = models.CharField(
            unique=True,
            max_length=2,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimregions' % TABLE_PREFIX

    def __str__(self):
        return self.region

    def __unicode__(self):
        return self.region


class DimUserAgent(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    useragent = models.CharField(
            max_length=8192,
            null=False)
    is_mutable = models.BooleanField(
            default=True,
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimuseragents' % TABLE_PREFIX

    def __str__(self):
        return self.useragent

    def __unicode__(self):
        return self.useragent


class LongURLs(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    longurl = models.CharField(
            max_length=4096,
            validators=[URLValidator()],
            null=False,
            blank=False)
    originally_encoded = models.BooleanField(
            null=False)
    is_active = models.BooleanField(
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_longurls' % TABLE_PREFIX

    def __str__(self):
        return self.longurl

    def __unicode__(self):
        return self.longurl


class ShortURLs(models.Model):
    id = models.AutoField(primary_key=True)
    hash = models.BigIntegerField(
            unique=True,
            null=False)
    longurl = models.OneToOneField(
            "LongURLs",
            db_column="longurl_id",
            to_field="id",
            unique=True,
            null=False,
            on_delete=models.CASCADE)
    shorturl = models.CharField(
            max_length=40,
            validators=[URLValidator()],
            null=False,
            blank=False)
    shorturl_path_size = models.SmallIntegerField(
            null=True)
    compression_ratio = models.DecimalField(
            max_digits=10,
            decimal_places=2,
            null=True)
    is_active = models.BooleanField(
            null=False)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_shorturls' % TABLE_PREFIX

    def __str__(self):
        return self.shorturl

    def __unicode__(self):
        return self.shorturl


class FactEvent(models.Model):
    id = models.AutoField(primary_key=True)
    event_yyyymmdd = models.CharField(
            max_length=8
    )
    event_hhmiss = models.CharField(
            max_length=6
    )
    event_type = models.CharField(
            max_length=1,
            null=False,
            choices=EVENT_TYPE)
    http_status_code = models.SmallIntegerField(
            null=False,
            choices=HTTP_STATUS_CODE
    )
    info = models.CharField(
            max_length=8192,
            null=False)
    longurl = models.ForeignKey(
            'LongURLs',
            db_column="longurl_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    shorturl = models.ForeignKey(
            'ShortURLs',
            db_column="shorturl_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    city = models.ForeignKey(
            'DimCity',
            db_column="city_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    continent = models.ForeignKey(
            'DimContinent',
            db_column="continent_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    country = models.ForeignKey(
            'DimCountry',
            db_column="country_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    device = models.ForeignKey(
            'DimDevice',
            db_column="device_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    host = models.ForeignKey(
            'DimHost',
            db_column="host_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    ip = models.ForeignKey(
            'DimIP',
            db_column="ip_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    postalcode = models.ForeignKey(
            'DimPostalCode',
            db_column="postalcode_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    referer = models.ForeignKey(
            'DimReferer',
            db_column="referer_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    region = models.ForeignKey(
            'DimRegion',
            db_column="region_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
    useragent = models.ForeignKey(
            'DimUserAgent',
            db_column="useragent_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_factevents' % TABLE_PREFIX

    def __str__(self):
        return "%d" % self.id

    def __unicode__(self):
        return "%d" % self.id


class Blacklist(models.Model):
    id = models.AutoField(primary_key=True)
    created_on = models.DateTimeField(
            null=False
    )
    is_active = models.BooleanField(
            null=False
    )
    city = models.ForeignKey(
            'DimCity',
            db_column="city",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    continent = models.ForeignKey(
            'DimContinent',
            db_column="continent",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    country = models.ForeignKey(
            'DimCountry',
            db_column="country_id",
            null=True,
            on_delete=models.CASCADE)
    device = models.ForeignKey(
            'DimDevice',
            db_column="device_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    host = models.ForeignKey(
            'DimHost',
            db_column="host_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    ip = models.ForeignKey(
            'DimIP',
            db_column="ip_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    postalcode = models.ForeignKey(
            'DimPostalCode',
            db_column="postalcode_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    referer = models.ForeignKey(
            'DimReferer',
            db_column="referer_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    region = models.ForeignKey(
            'DimRegion',
            db_column="region_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)
    useragent_id = models.ForeignKey(
            'DimUserAgent',
            db_column="useragent_id",
            to_field="id",
            null=True,
            on_delete=models.CASCADE)

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_blacklist' % TABLE_PREFIX

    def __str__(self):
        return "%d" % self.id

    def __unicode__(self):
        return "%d" % self.id


@xaction.atomic
def log_event(dt, event_type, status_code, info, shorturl, longurl, ipobj, hostname, useragent, referer):
    blacklist_csv = ''

    def _bl(blacklist_csv, str):
        if blacklist_csv:
            return '%s,%s' % (blacklist_csv, str)
        else:
            return str

    # dimension log_event helper function here to keep it within the scope of the transaction
    def _get_or_create_dimension(modelclass, **kwargs):
        # assume 1st kwarg is the value to use to generate the hashkey
        key = kwargs.pop("key")
        if not key:
            key = "missing"
        hash = get_hash(' '.join(str(key).split()).lower())
        exists = False
        is_mutable = True
        try:
            m = modelclass.objects.filter(hash=hash).get()
            if m:
                exists = True
                is_mutable = m.is_mutable
        except ObjectDoesNotExist:
            m = modelclass()
            pass
        if not exists:
            for f in m._meta.fields:
                f = f.name
                lf = f.lower()
                if lf == "hash":
                    if not m.hash:
                        setattr(m, f, hash)
                elif lf == "is_mutable":
                    if not m.is_mutable:
                        setattr(m, f, is_mutable)
                elif lf != "id" and is_mutable:
                    for k, v in kwargs.items():
                        if k.lower() == lf:
                            setattr(m, f, v)
                            break
            m.save()
        return m

    # dimension log_event helper function here to keep it within the scope of the transaction
    def _get_or_create_geo_dimension(modelclass, strkey, unknown_value="unknown", missing_value="missing"):
        if strkey in ipobj.geodict:
            m = _get_or_create_dimension(modelclass, key=ipobj.geodict[strkey], name=ipobj.geodict[strkey])
        else:
            if ipobj.is_global:
                value = unknown_value
            else:
                value = missing_value
            m = _get_or_create_dimension(modelclass, key=value, name=value)
        return m

    ip          = _get_or_create_dimension(DimIP, key=ipobj.ip.exploded, ip=ipobj.ip.exploded)
    #
    city        = _get_or_create_geo_dimension(DimCity, "city")
    continent   = _get_or_create_geo_dimension(DimContinent, "continent")
    country     = _get_or_create_geo_dimension(DimCountry, "country")
    postalcode  = _get_or_create_geo_dimension(DimPostalCode, "postalcode")
    region      = _get_or_create_geo_dimension(DimRegion, "region")
        #
    # # device support TBD
    deviceid    = "unknown"
    device      = _get_or_create_dimension(DimDevice, key=deviceid, deviceid=deviceid)
    #
    host        = _get_or_create_dimension(DimHost, key=hostname, hostname=hostname)
    referer     = _get_or_create_dimension(DimReferer, key=referer, referer=referer)
    useragent   = _get_or_create_dimension(DimUserAgent, key=useragent, useragent=useragent)

    abs_status_code = abs(status_code)

    fact = FactEvent(
        event_yyyymmdd=dt.strftime('%Y%m%d'),
        event_hhmiss=dt.strftime('%H%M%S'),
        event_type=event_type,
        http_status_code=abs_status_code,
        info=info,
        longurl=longurl,
        shorturl=shorturl,
        city=city,
        continent=continent,
        country=country,
        device=device,
        host=host,
        ip=ip,
        postalcode=postalcode,
        referer=referer,
        region=region,
        useragent=useragent
    )
    fact.save()

    return fact.id, status_code
