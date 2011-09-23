from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^$', 'qa.views.index'),
    (r'^ask/?$', 'qa.views.ask'),
    (r'^question/(?P<id>\d+)/?$', 'qa.views.question'),
    (r'^admin/', include(admin.site.urls)),
)
