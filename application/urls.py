from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^$', 'qa.views.index'),
    
    (r'^login$', 'qa.views.login'),
    (r'^join$', 'qa.views.join'),
    (r'^logout$', 'qa.views.logout'),
    (r'^error$', 'qa.views.error'),
    
    (r'^ask/?$', 'qa.views.ask'),
    (r'^ask_question$', 'qa.views.ask_question'),
    
    (r'^question/(?P<id>\d+)/?$', 'qa.views.question_view'),
    (r'^admin/', include(admin.site.urls)),
)
