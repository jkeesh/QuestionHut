from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
register = template.Library()
from qa.models import Vote

@register.simple_tag
def user_vote(user, obj, kind, score):
    try:
        vote = Vote.objects.get(user=user, obj_id=obj.id, kind=kind)
        if vote.score == score:
            return 'voted'
        return ''
    except Vote.DoesNotExist:
        return ''