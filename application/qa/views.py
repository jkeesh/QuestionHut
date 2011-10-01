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
from qa.models import Tag, Question, Answer, Vote, UserProfile, Course

from django.utils import simplejson
def json_response(obj):
    """
    Helper method to turn a python object into json format and return an HttpResponse object.
    """
    return HttpResponse(simplejson.dumps(obj), mimetype="application/x-javascript")


models = {
    'A': Answer,
    'Q': Question
}

@csrf_protect
def vote(request):
    votes = Vote.submit_vote(request)
    return json_response({
        "status": "ok",
        "votes": votes
    })


@csrf_protect
def join(request):
    try:
        User.objects.get(email=request.POST['email'])
        return redirect('/error')
    except User.DoesNotExist:
        pass
    
    print request.POST
    user = User.objects.create_user(request.POST['email'], #email is username
                                    request.POST['email'], #email
                                    request.POST['password'])
    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    user.save()
    
    userprofile = UserProfile(user=user)
    userprofile.save()
    
    courses = request.POST.getlist('class')
    for course_id in courses:
        print course_id
        course = Course.objects.get(pk=course_id)
        print course
        userprofile.courses.add(course)
    
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
        
def sort(request, method):
    """
    Sort the home page questions by some method (recent, best, popular)
    """
    if method == 'best':
        questions = Question.objects.all().order_by('-votes')[:30]
    elif method == 'popular':
        questions = Question.objects.all().order_by('-views')[:30]
    else:
        questions = Question.objects.all().order_by('-created_at')[:30]
    
    return render_to_response(
        "index.html",
        {
            'user': request.user,
            'questions': questions,
            'sort': method,
            'courses': request.user.get_profile().courses.all()
        },
        context_instance = RequestContext(request)
    )
    
def sort_questions(query_set, sort):
    if sort == 'best':
        return query_set.order_by('-votes')[:30]
    elif sort == 'popular':
        return query_set.order_by('-views')[:30]
    else:
        return query_set.order_by('-created_at')[:30]

def get_questions(course, approved=True):
    if course == 'all':
        return Question.objects.filter(approved=approved)
    course_tag = Tag.objects.get(title=course)
    return course_tag.questions.filter(approved=approved)
    
def questions_display(request):
    sort = request.GET['sort'] if 'sort' in request.GET else 'recent'
    course = request.GET['course'] if 'course' in request.GET else 'all'
    
    query_set = get_questions(course=course)
    query_set = sort_questions(query_set=query_set, sort=sort)
    
    return render_to_response(
        "index.html",
        {
            'user': request.user,
            'questions': query_set,
            'sort': sort,
            'course': course,
            'courses': request.user.get_profile().courses.all()
        },
        context_instance = RequestContext(request)
    )
    
def index(request):
    if not request.user.is_authenticated():
        return render_to_response(
            "login.html",
            {
                'courses': Course.objects.all()
            },
            context_instance = RequestContext(request)
        )
    else:
        return questions_display(request=request)


        
        
def tag(request, tag_title):
    cur_tag = Tag.objects.get(title=tag_title)
    questions = cur_tag.questions.all().order_by('-created_at')
    
    
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
    question.views += 1
    question.save()
    return render_to_response(
        "question.html",
        {
            'user': request.user,
            'question': question,
            'answers': question.answers.all().order_by('-votes')
        },
        context_instance = RequestContext(request)
    )
    

def answer_question(request):
    print request.user
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        q_id = request.POST['question']
        content = request.POST['answer']
        question = Question.objects.get(pk=q_id)
        answer = Answer(author=request.user,
                        question=question,
                        content=content)
        answer.save()
        return redirect('/question/%s' % q_id)
    
    
@csrf_protect
def ask_question(request):
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        title = request.POST['title']
        if len(title) == 0:
            return ask(request, error='You need to enter a title.')
        
        content = request.POST['content']
        if len(content) == 0:
            return ask(request, error='You need to enter some content to your question.', title=title)
            
        course_id = request.POST['course']
        course = Course.objects.get(pk=course_id)
        
        question = Question(title=title, content=content, author=request.user, course=course)
        question.save()

        question.add_tag(course.title)
        
        
        
        tags = request.POST['tags'].replace(',', '').split(' ')
        if len(tags) == 1 and len(tags[0]) == 0:
            return ask(request, error='You need to enter some tags.', title=title, content=content)
            
        for tag in tags:
            question.add_tag(tag)
        
        return redirect('/')
    
def ask(request, error=None, title=None, content=None):
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        print "error", error
        return render_to_response(
            "ask.html",
            {
                'user': request.user,
                'courses': Course.objects.all(),
                'error': error,
                'title': title,
                'content': content
            },
            context_instance = RequestContext(request)
        )
        
        
        
def moderate(request):
    if not request.user.is_authenticated() and request.user.get_profile().is_moderator:
        return redirect('/')

    sort = request.GET['sort'] if 'sort' in request.GET else 'recent'    
    course = request.GET['course'] if 'course' in request.GET else 'all'
    
    query_set = get_questions(course=course, approved=False)
    query_set = sort_questions(query_set=query_set, sort=sort)

    return render_to_response(
        "moderate.html",
        {
            'user': request.user,
            'questions': query_set,
            'sort': sort,
            'course': course,
            'courses': request.user.get_profile().courses.all()
        },
        context_instance = RequestContext(request)
    )
    