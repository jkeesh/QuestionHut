# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.contrib import auth

# Models
from django.contrib.auth.models import User
from qa.models import Tag, Question, Answer

@csrf_protect
def join(request):
    user = User.objects.create_user(request.POST['email'], #email is username
                                    request.POST['email'], #email
                                    request.POST['password'])
    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    user.save()
    
    return authenticate(request, request.POST['email'], request.POST['password'])
    
def authenticate(request, email, password):
    user = auth.authenticate(username=email, password=password)
    if user is not None:
        auth.login(request, user)
        print "authenticated"
        return HttpResponseRedirect('/')
    else:
        return HttpResponseRedirect('/error')
    
@csrf_protect
def login(request):
    return authenticate(request, request.POST['email'], request.POST['password'])
    
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/')
    
def error(request):
    return render_to_response(
        "error.html",
        {},
        context_instance = RequestContext(request)
    )

def index(request):
    if not request.user.is_authenticated():
        return render_to_response(
            "login.html",
            {},
            context_instance = RequestContext(request)
        )
    else:
        
        return render_to_response(
            "index.html",
            {
                'user': request.user
            },
            context_instance = RequestContext(request)
        )
        
    
def question(request, id=None):
    pass
    
def ask(request):
    pass