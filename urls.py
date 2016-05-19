from django.conf.urls import patterns, include, url
from bc_api.views import notifications, order_notifications, case_notifications

urlpatterns = patterns('',
                       url(r'^notifications/(?P<site_code>[A-Z0-9]+)/$', notifications, name="notifications"),
                       url(r'^notifications/order/(?P<site_code>[A-Z0-9]+)/$', order_notifications,
                           name="notifications"),
                       url(r'^notifications/case/(?P<site_code>[A-Z0-9]+)/$', case_notifications, name="notifications"),
                       )
