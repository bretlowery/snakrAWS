'''
models.py contains the persistence logic for Snakr.
'''

from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import ugettext_lazy as _

from ipaddress import IPv6Interface, IPv4Interface, IPv6Address, IPv4Address, ip_interface

from snakraws import settings
from snakraws.utils import get_hash


TABLE_PREFIX = 'snakraws'

EVENT_TYPE = {
    'B': _('Blacklisted'),
    'D': _('Debug'),
    'E': _('Error'),
    'I': _('Information'),
    'L': _('New Long URL Submitted'),
    'N': _('Short URL Inactive'),
    'R': _('Existing Long URL Resubmitted'),
    'S': _('Short URL Redirect'),
    'U': _('Short URL Unrecognized/Not Resolvable'),
    'W': _('Warning'),
    'X': _('Exception'),
    'Z': _('Unknown Event'),
}

DEFAULT_EVENT_TYPE = 'Z'

HTTP_STATUS_CODE = {
    200: _('OK (200)'),
    301: _('Redirect (301)'),
    302: _('Redirect (302)'),
    400: _('Bad Request (400)'),
    403: _('Forbidden (403)'),
    404: _('Not Found (404)'),
    422: _('Unprocessable Entity (422)'),
    500: _('Server Exception (500)'),
    0:   _('No response')
}

DEFAULT_HTTP_STATUS_CODE = 403

DEFAULT_URL_ID = get_hash('unknown')
UNSPECIFIED_URL_ID = get_hash('unspecified')

_USE_EXISTS = getattr(settings, 'USE_IF_DIM_EXISTS', False)


class DimGeoLocation(models.Model):
    id = models.AutoField(
            primary_key=True
    )
    hash = models.BigIntegerField(
            unique=True,
            null=False
    )
    is_mutable = models.BooleanField(
            default=True,
            null=False
    )
    providername = models.CharField(
            max_length=50,
            null=False
    )
    postalcode = models.CharField(
            unique=True,
            max_length=32,
            null=False
    )
    lat = models.DecimalField(
            max_digits=7,
            decimal_places=4,
            null=True
    )
    lng = models.DecimalField(
            max_digits=7,
            decimal_places=4,
            null=True
    )
    city = models.CharField(
            max_length=100,
            null=True
    )
    regionname = models.CharField(
            max_length=100,
            null=True
    )
    regioncode = models.CharField(
            max_length=2,
            null=True
    )
    countryname = models.CharField(
            max_length=100,
            null=True
    )
    countrycode = models.CharField(
            max_length=2,
            null=True
    )
    countyname = models.CharField(
            max_length=100,
            null=True
    )
    countyweight = models.DecimalField(
            max_digits=5,
            decimal_places=2,
            null=True
    )
    allcountyweights = models.CharField(
            max_length=100,
            null=True
    )

    class Meta:
        app_label = TABLE_PREFIX
        managed = False
        db_table = '%s_dimgeolocations' % TABLE_PREFIX

    def __str__(self):
        return '[ %d, "%s", "%s", "%s", "%s" ]' % (self.hash, self.postalcode, self.city, self.regionname, self.countryname)

    def __unicode__(self):
        return u'[ %d, "%s", "%s", "%s", "%s" ]' % (self.hash, self.postalcode, self.city, self.regionname, self.countryname)


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
            null=False
    )
    cid = models.CharField(
            max_length=40,
            null=False
    )
    http_status_code = models.SmallIntegerField(
            null=False
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
    geo = models.ForeignKey(
            'DimGeoLocation',
            db_column="geo_id",
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
    referer = models.ForeignKey(
            'DimReferer',
            db_column="referer_id",
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
    geo = models.ForeignKey(
            'DimGeoLocation',
            db_column="geo_id",
            to_field="id",
            null=False,
            on_delete=models.DO_NOTHING)
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
    referer = models.ForeignKey(
            'DimReferer',
            db_column="referer_id",
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



