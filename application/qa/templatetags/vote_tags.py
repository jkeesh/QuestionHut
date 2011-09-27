from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
register = template.Library()


@register.simple_tag
def user_vote(obj, type):
    return "worked"