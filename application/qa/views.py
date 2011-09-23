# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response

# Models
from django.contrib.auth.models import User
from qa.models import Tag, Question, Answer

def index(request):
    return render_to_response(
        "login.html",
        {},
        context_instance = RequestContext(request)
    )
    
def question(request, id=None):
    pass
    
def ask(request):
    pass