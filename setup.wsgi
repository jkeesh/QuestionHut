import os
import sys

sys.path.append('/var/questionhut/code/')
sys.path.append('/var/questionhut/code/application/')
os.environ['DJANGO_SETTINGS_MODULE'] = 'application.settings'

print sys.path

sys.stdout = sys.stderr

print sys.path

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()