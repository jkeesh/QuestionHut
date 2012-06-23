import os
import sys

sys.path.append('/var/questionhut/code/')
##sys.path.append('/home/jkeesh/sites/questionhut.com/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'application.settings'

sys.stdout = sys.stderr

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()