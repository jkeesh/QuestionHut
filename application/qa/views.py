# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_protect
from django.contrib import auth
from django.shortcuts import get_object_or_404

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
        return redirect('/')
    else:
        return redirect('/error')
    
@csrf_protect
def login(request):
    return authenticate(request, request.POST['email'], request.POST['password'])
    
def logout(request):
    auth.logout(request)
    return redirect('/')
    
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
        questions = Question.objects.all()[:10]
        
        
        return render_to_response(
            "index.html",
            {
                'user': request.user,
                'questions': questions
            },
            context_instance = RequestContext(request)
        )
        
    
def question_view(request, id=None):
    if not id: 
        return redirect('/error')
    question = get_object_or_404(Question, pk=id)
    return render_to_response(
        "question.html",
        {
            'user': request.user,
            'question': question,
            'answers': question.answers.all()
        },
        context_instance = RequestContext(request)
    )
    
    
@csrf_protect
def ask_question(request):
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        title = request.POST['title']
        content = request.POST['content']
        question = Question(title=title, content=content, author=request.user)
        question.save()
        
        return redirect('/')
    
def ask(request):
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        return render_to_response(
            "ask.html",
            {
                'user': request.user
            },
            context_instance = RequestContext(request)
        )