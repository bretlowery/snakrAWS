from django.template import Library
from snakraws.utils import urlparts

register = Library()


@register.filter(name="get_netloc")
def get_netloc(url):
    return urlparts(url).netloc


@register.filter(name="get_path")
def get_path(url):
    return urlparts(url).path


