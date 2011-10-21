from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
register = template.Library()
from qa.models import Question, Answer

@register.simple_tag
def mod_count(hut):
    q_count = Question.objects.filter(course=hut, approved=False).count()
    a_count = Answer.objects.filter(question__course=hut, approved=False).count()
    return q_count + a_count
