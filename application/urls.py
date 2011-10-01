from django.conf.urls.defaults import *
from django.conf import settings
import os
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    (r'^$', 'qa.views.index'),
    (r'^tag/(?P<tag_title>\w+)/?$', 'qa.views.tag'),
    
    (r'^login$', 'qa.views.login'),
    (r'^join$', 'qa.views.join'),
    (r'^logout$', 'qa.views.logout'),
    (r'^error$', 'qa.views.error'),
    
    (r'^ask/?$', 'qa.views.ask'),
    (r'^ask_question$', 'qa.views.ask_question'),
    
    (r'^question/(?P<id>\d+)/?$', 'qa.views.question_view'),
    (r'^answer_question$', 'qa.views.answer_question'),
    
    (r'^ajax/vote$', 'qa.views.vote'),
    (r'^ajax/moderate$', 'qa.views.moderate_action'),
    
    (r'^moderate/?$', 'qa.views.moderate'),
    
    (r'^questions/?$', 'qa.views.questions_display'),
    (r'^sort/(?P<method>\w+)/?$', 'qa.views.sort'),
    
    (r'^admin/', include(admin.site.urls)),
)


if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': os.path.dirname(settings.PROJECT_ROOT)}),
    )