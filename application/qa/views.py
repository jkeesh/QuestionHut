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
import re
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings

from qa.search import get_query
from django.contrib.auth.decorators import login_required

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

MESSAGES = {
    'moderation': 'Your question has been submitted for moderation, and if approved will be shown soon.',
    'email': 'You must enter in a properly formatted Stanford email address.',
    'fname': 'You must enter in a first name.',
    'lname': 'You must enter in a last name',
    'passwd': 'You must enter in a password',
    'class':  'You must select at least one class.',
    'amod': 'Your answer has been submitted for moderation, and if approved will be shown soon.',
    'act': 'Your account has been activated. Please log in with your email and password.',
    'inact': 'Your account could not be succesfully activated.',
    'waitforact': 'Thanks for creating an account. You should receive a confirmation email shortly which will activate your account.',
    'passwdmatch': 'Your passwords did not match. Please enter them again.',
    'notactive': 'Your account is not yet active.',
    'loginerror': 'There was an error loggin you in. Please check your password.'
}

@csrf_protect
@login_required  
def vote(request):
    votes = Vote.submit_vote(request)
    return json_response({
        "status": "ok",
        "votes": votes
    })

def verify_email(email):
    """
    Accept emails like 
        jkeeshin@stanford.edu and 
        jkeeshin@cs.stanford.edu
    
        NAME@(SUBDOMAIN.)?stanford.edu
    """
    if re.match("^.+\\@(.+\\.)?stanford\\.edu$", email) != None:
        return True
    return False
    
    
def send_email(subject, content, from_email, to_email):
    msg = EmailMessage(subject, content, from_email, to_email)
    msg.content_subtype = "html"  # Main content is now text/html
    msg.send()


def generate_code(user):
    import datetime, hashlib
    now = str(datetime.datetime.now())
    verify = "%s%s" % (user.email, now)
    code = hashlib.sha224(verify).hexdigest()
    
    up = user.get_profile()
    up.confirmation_code = code
    up.save()
    return code

## To email must be a list
def send_confirmation_email(user):
    code = generate_code(user)
    subject = 'Welcome to QuestionHut: Confirm Your Email Address'
    email_content = 'Thanks for signing up for Question Hut. Please confirm your email address by ' \
            'visititing the following link: <br/><br/> %sconfirm?u=%d&code=%s' % (settings.BASE_URL, user.id, code)
    print email_content
    send_email(subject, email_content, 'Question Hut <questionhut@gmail.com>', [user.email])
    print "Sent!"

def confirm(request):
    uid = request.GET['u']
    code = request.GET['code']
    
    user = User.objects.get(pk=uid)
    msg = 'inact'
    if user.get_profile().confirmation_code == code:
        msg = 'act'
        user.is_active = True
        user.save()
    
    return redirect('/?msg=%s' % msg ) ## include message

	
@csrf_protect
def join(request):
    try:
        User.objects.get(email=request.POST['email'])
        return redirect('/error')
    except User.DoesNotExist:
        pass
        
    if len(request.POST['first_name']) == 0:
        return redirect('/?msg=fname')
    if len(request.POST['last_name']) == 0:
        return redirect('/?msg=lname')
    if len(request.POST['password']) == 0:
        return redirect('/?msg=passwd')
        
    if request.POST['password'] != request.POST['password2']:
        return redirect('/?msg=passwdmatch')
    
    if len(request.POST.getlist('class')) == 0:
        return redirect('/?msg=class')
    
    if not verify_email(request.POST['email']):
        return redirect('/?msg=email')
    
    user = User.objects.create_user(request.POST['email'], #email is username
                                    request.POST['email'], #email
                                    request.POST['password'])
    user.first_name = request.POST['first_name']
    user.last_name = request.POST['last_name']
    user.is_active = False
    user.save()
    
    userprofile = UserProfile(user=user)
    userprofile.save()
    
    courses = request.POST.getlist('class')
    for course_id in courses:
        course = Course.objects.get(pk=course_id)
        userprofile.courses.add(course)
        
    send_confirmation_email(user)
    return redirect('/?msg=waitforact')
    #return authenticate(request, request.POST['email'], request.POST['password'])
    
def authenticate(request, email, password):
    user = auth.authenticate(username=email, password=password)
    if user is not None:
        if not user.is_active:
            auth.logout(request)
            return redirect('/?msg=notactive')

        auth.login(request, user)
        return redirect('/')
    else:
        return redirect('/?msg=loginerror')
    
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
        
    
def sort_questions(query_set, sort):
    if sort == 'best':
        return query_set.order_by('-votes')[:30]
    elif sort == 'popular':
        return query_set.order_by('-views')[:30]
    else:
        return query_set.order_by('-last_updated')[:30]

def get_questions(course, tags=None, approved=True, status='all'):
    qs = Question.objects.filter(approved=approved)
    if status == 'unanswered':
        qs = qs.filter(answered=False)
    if course != 'all':
        course_tag = Tag.objects.get(title=course)
        qs = qs.filter(tags=course_tag)
    if tags is not None:
        tag_list = tags.split(',')
        for tag in tag_list:
            try: 
                the_tag = Tag.objects.get(title=tag)
                qs = qs.filter(tags=the_tag)
            except Tag.DoesNotExist:
                pass

    return qs
    
@login_required  
def questions_display(request, message=None):
    sort = request.GET['sort'] if 'sort' in request.GET else 'recent'
    course = request.GET['course'] if 'course' in request.GET else 'all'
    tags = request.GET['tags'] if 'tags' in request.GET else None
    status = request.GET['status'] if 'status' in request.GET else 'all'
        
    query_set = get_questions(course=course, tags=tags, status=status)
    query_set = sort_questions(query_set=query_set, sort=sort)
    
    return render_to_response(
        "index.html",
        {
            'user': request.user,
            'questions': query_set,
            'sort': sort,
            'course': course,
            'status': status,
            'courses': request.user.get_profile().courses.all(),
            'message': message
        },
        context_instance = RequestContext(request)
    )
    
def index(request, message=None):
    message = None
    if 'msg' in request.GET:
        the_msg = request.GET['msg']
        if the_msg in MESSAGES:
            message = MESSAGES[the_msg]
    
    if not request.user.is_authenticated():
        return render_to_response(
            "login.html",
            {
                'courses': Course.objects.all(),
                'message': message
            },
            context_instance = RequestContext(request)
        )
    else:
        return questions_display(request=request, message=message)
        
@login_required  
def question_view(request, id=None):
    if not id: 
        return redirect('/error')

    message = None
    if 'msg' in request.GET:
        the_msg = request.GET['msg']
        if the_msg in MESSAGES:
            message = MESSAGES[the_msg]
        
        
    question = get_object_or_404(Question, pk=id)
    question.views += 1
    question.save()
    return render_to_response(
        "question.html",
        {
            'user': request.user,
            'question': question,
            'message': message,
            'answers': question.answers.filter(approved=True).order_by('-votes')
        },
        context_instance = RequestContext(request)
    )
    
@login_required  
def answer_question(request):
    print request.user
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        q_id = request.POST['question']
        content = request.POST['answer']
        question = Question.objects.get(pk=q_id)
        question.update_timestamp()
        answer = Answer(author=request.user,
                        question=question,
                        content=content)
        answer.save()
        return redirect('/question/%s?msg=amod' % q_id)
    
    
@csrf_protect
@login_required  
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
        
        
        return redirect('/?msg=moderation')
    
@login_required  
def ask(request, error=None, title=None, content=None):
    if not request.user.is_authenticated():
        return redirect('/')
    else:
        return render_to_response(
            "ask.html",
            {
                'user': request.user,
                'courses': request.user.get_profile().courses.all(),
                'error': error,
                'title': title,
                'content': content
            },
            context_instance = RequestContext(request)
        )
        
        
def select_answer(request):
    answer = Answer.objects.get(pk=request.POST['answer'])
    question = Question.objects.get(pk=request.POST['question'])
    question.select_answer(answer)
    return json_response({
        "status": "ok"
    })
        
@login_required  
def moderate(request):
    if not request.user.is_authenticated() or not request.user.get_profile().is_moderator:
        return redirect('/')

    course = request.GET['course'] if 'course' in request.GET else None    
    sort = request.GET['sort'] if 'sort' in request.GET else 'recent'    
    
    query_set = answers = None
    if course:   
        the_course = Course.objects.get(title=course)
        if the_course not in request.user.get_profile().moderator_courses.all():
            ## Then they cannot moderate this specific class
            return redirect('/moderate')
        
        query_set = get_questions(course=course, approved=False)
        query_set = sort_questions(query_set=query_set, sort=sort)    
        answers = Answer.objects.filter(approved=False, question__course__title=course).order_by('-created_at')

    return render_to_response(
        "moderate.html",
        {
            'user': request.user,
            'questions': query_set,
            'sort': sort,
            'course': course,
            'moderator_courses': request.user.get_profile().moderator_courses.all(),
            'answers': answers
        },
        context_instance = RequestContext(request)
    )
    
@csrf_protect  
@login_required    
def moderate_action(request):
    obj_id = request.POST['id']
    action = request.POST['action']
    Model = models[request.POST['kind']] # 'Q' or 'A'
    obj = Model.objects.get(pk=obj_id)
    obj.moderate(action)
    return json_response({
        "status": "ok"
    })
    
@login_required  
def search(request):
    q_query = get_query(request.GET['q'], ['title', 'content'])    
    questions = Question.objects.filter(q_query).filter(approved=True).order_by('-votes')

    return render_to_response(
        "search.html",
        {
            'user': request.user,
            'questions': questions
        },
        context_instance = RequestContext(request)
    )
