"""
WSGI config for SnakrAWS project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/
"""


import os
from django.core.wsgi import get_wsgi_application
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

import datetime
import sys
import django

import spacy

from snakraws.persistence import SnakrLogger

event = SnakrLogger()
spacy.load('en')

dt = datetime.datetime.now()
event.log(messagekey='STARTUP', dt=dt.isoformat(), status_code=0)
event.log(messagekey='PYTHON_VERSION', value=sys.version, status_code=0)
event.log(messagekey='DJANGO_VERSION', value=django.get_version(), status_code=0)
application = get_wsgi_application()
event.log(messagekey='READY', status_code=0)
