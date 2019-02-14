"""
SnakrAWS URL Configuration
"""
#from django.contrib import admin
from django.urls import path

urlpatterns = [
    #path('admin/', admin.site.urls),
    path(r'', 'snakraws.views.request_handler', name="request_handler"),
    path(r'^([a-zA-Z0-9\-\_]*)/$', 'snakraws.views.request_handler', name="request_handler"),
]
