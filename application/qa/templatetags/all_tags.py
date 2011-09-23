from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
register = template.Library()

import application.settings

@register.simple_tag
def version():
    return settings.VERSION
    
@register.simple_tag
def debug_js():
    return "true" if settings.CONSOLE_DEBUG else "false"
