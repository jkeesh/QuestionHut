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


@register.simple_tag
def format_time(timestamp = None):
    """
    Returns a humanized string representing time difference
    between now() and the input timestamp.

    The output rounds up to days, hours, minutes, or seconds.
    4 days 5 hours returns '4 days'
    0 days 4 hours 3 minutes returns '4 hours', etc...
    http://djangosnippets.org/snippets/412/
    """
    import datetime

    timeDiff = datetime.datetime.now() - timestamp
    days = timeDiff.days
    hours = timeDiff.seconds/3600
    minutes = timeDiff.seconds%3600/60
    seconds = timeDiff.seconds%3600%60

    str = ""
    tStr = ""
    if days > 7:
        return timestamp.strftime("%b %d, '%y %H:%M")
    elif days > 0:
        if days == 1:   tStr = "day"
        else:           tStr = "days"
        str = str + "%s %s ago" %(days, tStr)
        return str
    elif hours > 0:
        if hours == 1:  tStr = "hour"
        else:           tStr = "hours"
        str = str + "%s %s ago" %(hours, tStr)
        return str
    elif minutes > 0:
        if minutes == 1:tStr = "min"
        else:           tStr = "mins"           
        str = str + "%s %s ago" %(minutes, tStr)
        return str
    elif seconds > 0:
        if seconds == 1:tStr = "sec"
        else:           tStr = "secs"
        str = str + "%s %s ago" %(seconds, tStr)
        return str
    else:
        return "just now"