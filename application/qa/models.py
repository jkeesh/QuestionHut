from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import re

class State(models.Model):
    CURRENT_QUARTER = 'winter-2012'
    
    @staticmethod
    def get_tag():
        try:
            tag = Tag.objects.get(title=State.CURRENT_QUARTER)
        except Tag.DoesNotExist:
            tag = Tag(title=State.CURRENT_QUARTER)
            tag.save()
        return tag

class Points():
    ANSWER_UPVOTE   = 10
    ANSWER_DOWNVOTE = -2
    QUESTION_UPVOTE = 5
    QUESTION_DOWNVOTE = -2
    ANSWER_ACCEPTED = 15

class Course(models.Model):
    title       =   models.CharField(max_length=50)
    slug        =   models.CharField(max_length=50, default='')
    description =   models.CharField(max_length=200, default='')
    default_level   =   models.IntegerField(default=1)
    public      =   models.BooleanField(default=True)
    
    
    @staticmethod
    def create_course(title, public=True, default_level=1):
        slug = title.lower().replace(' ', '-')
        new_course = Course(title=title, slug=slug, public=public, default_level=default_level)
        new_course.save()
    
    def set_description(self, description):
        self.description = description
        self.save()
        
    def has_approved(self, user):
        """Return if this user has auto-posting permissions. This is true if their level is
        >= APPROVED"""
        role = Role.objects.get(hut=self, profile=user.get_profile())
        return role.level >= Role.APPROVED
        
    def add_user(self, user, level=None):
        if not level:
            level = self.default_level
        role = Role(hut=self, profile=user.get_profile(), level=level)
        role.save()
            
    def __unicode__(self):
        visibility = 'public' if self.public else 'private'
        return "%s (%s) [%s] level=%d" % (self.title, self.slug, visibility, self.default_level)

class UserProfile(models.Model):
    user        =   models.OneToOneField(User)
    courses     =   models.ManyToManyField(Course, related_name='members', through='Role')
    is_moderator=   models.BooleanField(default=False)
    moderator_courses   =   models.ManyToManyField(Course, related_name='moderators')
    confirmation_code   =   models.CharField(max_length=100, default='')
    bio         =   models.CharField(max_length=30, default='')
    points      =   models.IntegerField(default=1)
    last_visited=   models.DateTimeField(auto_now=True, default=datetime.now())
    
    def set_role(self, hut, level):
        role = Role.objects.get(profile=self, hut=hut)
        role.level = level
        role.save()
        
    def get_points(self):
        if self.points < 1:
            return 1
        return self.points
        
    def change_points(self, points):
        self.points += points
        self.save()
        
    def add_points(self, points):
        self.change_points(points)
        
    def remove_points(self, points):
        self.change_points(-points)
        
    def moderator_roles(self):
        return Role.objects.filter(profile=self, level__gte=Role.MODERATOR)
        
    def moderator_huts(self):
        huts = self.moderator_roles().values('hut')
        return Course.objects.filter(id__in=huts) 
        
    def is_moderator_for_hut(self, hut):
        huts = self.moderator_huts()
        return hut in huts       
        
    def is_hut_moderator(self):
        return self.moderator_roles().count() > 0
        
    def __unicode__(self):
        return "%s" % self.user
    
class Role(models.Model):
    ## Represents a persons role in a hut
    profile     = models.ForeignKey(UserProfile)
    hut         = models.ForeignKey(Course)
    
    MEMBER      =   1
    APPROVED    =   2
    MODERATOR   =   3
    ADMIN       =   4
    
    level       = models.IntegerField(default=MEMBER) 
    
    def __unicode__(self):
        return "[%d] %s: %s" % (self.level, self.profile, self.hut)    
    

class Tag(models.Model):
    title       =   models.CharField(max_length=200)
    
    def __unicode__(self):
        return "%s" % self.title
                
class Vote(models.Model):
    VOTE_TYPES = (
        ('Q', 'Question'),
        ('A', 'Answer'),
    )
    user        =   models.ForeignKey(User)
    obj_id      =   models.PositiveIntegerField()
    score       =   models.IntegerField()
    kind        =   models.CharField(max_length=1, choices=VOTE_TYPES)
    
    def update_vote_count(self, score_change):
        obj, points = self.get_object()
                    
        obj.votes += score_change
        obj.save()
        return obj.votes
        
    def get_object(self):
        if self.kind == 'A':
            obj = Answer.objects.get(pk=self.obj_id)
            points = (Points.ANSWER_UPVOTE, Points.ANSWER_DOWNVOTE)
        else:
            obj = Question.objects.get(pk=self.obj_id)
            points = (Points.QUESTION_UPVOTE, Points.QUESTION_DOWNVOTE)
            
        return obj, points
        
    def change_points(self, multiplier=1):
        obj, points = self.get_object()
        point_diff = points[0] if self.score == 1 else points[1]
        obj.author.get_profile().change_points(multiplier*point_diff)
        
        
    def undo_points(self):
        """Since a vote was undone, the full amount of the points should be removed from the user."""
        self.change_points(multiplier=-1)
        
    def add_points(self):
        self.change_points()        
        
    def undo(self, new_score):
        ## If the new score == old score, this is an 'undo'
        should_delete = self.score == new_score

        undo_change = self.score * -1 # This undoes the vote
        votes = self.update_vote_count(undo_change)
        self.undo_points()

        if should_delete:
            self.delete()
        return should_delete, votes
    
    @staticmethod
    def submit_vote(request):
        """
        The process of submitting a vote is as follows:
            1. Get the new score for this vote. That is either a +1 or -1
            2. See if we had an old vote
                - If we did. Undo that vote (and also undo the points that went along with it)
                - If the new vote was the same as the old vote, that means this vote should be deleted entirely,
                    so just return the number of votes for this object
            3. If we didn't have an old vote
                - Create a new vote, but dont set the score. What we are trying to do is make it so that
                    in any situation we are starting "from scratch" and seeing the effect of the most recent vote.
            4. Set the new score, and save the vote.
            5. Add the points properly
            6. Update the vote count on the object
        """
        new_score = int(request.POST['action'])
        
        try:
            vote = Vote.objects.get(
                            user=request.user, 
                            kind=request.POST['type'],
                            obj_id=request.POST['id']
                        )
            should_delete, votes = vote.undo(new_score=new_score)
            if should_delete:
                return votes
        except Vote.DoesNotExist:
            vote = Vote(
                            user=request.user,
                            kind=request.POST['type'],
                            obj_id=request.POST['id']
                        )
        vote.score = new_score
        vote.save()
        vote.add_points()        
        return vote.update_vote_count(new_score)
    
    def __unicode__(self):
        return "%s voted on %c %d %d" % (self.user.name(), self.kind, self.id, self.score)

        
class Question(models.Model):
    author      =   models.ForeignKey(User)
    votes       =   models.IntegerField(default=0)
    views       =   models.IntegerField(default=0)
    title       =   models.CharField(max_length=200)
    content     =   models.TextField()
    created_at  =   models.DateTimeField(auto_now_add=True)
    last_updated=   models.DateTimeField(auto_now_add=True)
    tags        =   models.ManyToManyField(Tag, related_name="questions")   
    answered    =   models.BooleanField(default=False)
    course      =   models.ForeignKey(Course, default=None, blank=True, null=True)
    approved    =   models.BooleanField(default=False)
    followers   =   models.ManyToManyField(User, related_name="questions_followed")
    
    def update_timestamp(self):
        self.last_updated = datetime.now()
        self.save()
    
    def get_answer_count(self):
        return len(self.answers.filter(approved=True))
    
    def deselect_all_answers(self):
        previous = self.answers.filter(selected=True)
        if len(previous) == 1:
            previous[0].author.get_profile().remove_points(Points.ANSWER_ACCEPTED)
        
        self.answers.all().update(selected=False)
    
    def select_answer(self, answer):
        self.deselect_all_answers()
        answer.selected = True
        answer.save()
        ## give points to answerer
        answer.author.get_profile().add_points(Points.ANSWER_ACCEPTED)
        self.answered = True
        self.save()
        
    def add_tag(self, tag_title): 
        if len(tag_title) == 0:
            return
        if re.search('^\s+$', tag_title):
            return
            
        try:
            the_tag = Tag.objects.get(title=tag_title.strip().lower())
        except Tag.DoesNotExist:
            the_tag = Tag(title=tag_title.strip().lower())
            the_tag.save()
        if the_tag not in self.tags.all():
            self.tags.add(the_tag)
            
    def moderate(self, action):
        if action == 'approve':
            self.approved = True
            self.save()
        else:
            self.delete()
        
    def __unicode__(self):
        return "%s: %s (%d)" % (self.author, self.title, self.votes)
        
    def get_comments(self):
        """Return the comments for this question"""
        return Comment.objects.filter(kind=Comment.QUESTION_TYPE, obj_id=self.id)
       
class Answer(models.Model):
    author      =   models.ForeignKey(User)
    content     =   models.TextField()
    votes       =   models.IntegerField(default=0)
    created_at  =   models.DateTimeField(auto_now_add=True)
    last_updated=   models.DateTimeField(auto_now=True)
    question    =   models.ForeignKey(Question, related_name='answers')
    selected    =   models.BooleanField(default=False)
    approved    =   models.BooleanField(default=False)
    
    def update_timestamp(self):        
        self.question.update_timestamp()
    
    def moderate(self, action):
        if action == 'approve':
            self.approved = True
            self.save()
        else:
            self.delete()
    
    def __unicode__(self):
        return "%s: %s (%d)" % (self.author, self.content[:15], self.votes)
        
    def get_comments(self):
        """Return the comments for this answer"""
        return Comment.objects.filter(kind=Comment.ANSWER_TYPE, obj_id=self.id)
        
class Comment(models.Model):
    author      =   models.ForeignKey(User)
    content     =   models.TextField()
    votes       =   models.IntegerField(default=0)
    created_at  =   models.DateTimeField(auto_now_add=True)

    QUESTION_TYPE   =   'Q'
    ANSWER_TYPE     =   'A'
    
    PARENT_TYPES = (
        (QUESTION_TYPE, 'Question'),
        (ANSWER_TYPE, 'Answer'),
    )
    
    kind        =   models.CharField(max_length=1, choices=PARENT_TYPES)
    obj_id      =   models.PositiveIntegerField()
    
    def __unicode__(self):
        return "[%s:%d] %s - %s (%d)" % (self.kind, self.obj_id, self.content, self.author, self.votes)
        
    @staticmethod
    def get_parent(kind, obj_id):
        if kind == Comment.QUESTION_TYPE:
            return Question.objects.get(pk=obj_id)
        return Answer.objects.get(pk=obj_id)
        
    def parent(self):
        if self.kind == Comment.QUESTION_TYPE:
            return Question.objects.get(pk=self.obj_id)
        return Answer.objects.get(pk=self.obj_id)
    
    @staticmethod
    def create(author, content, obj):
        if type(obj) == Answer:
            kind = Comment.ANSWER_TYPE
        else:
            kind = Comment.QUESTION_TYPE
            
        comment = Comment(author=author, content=content, obj_id=obj.id, kind=kind)
        comment.save()
        comment.parent().update_timestamp()
        return comment
    
    
    
class UserMethods:
    """
    This class adds some additional convenience methods onto the User
    class.
    """
    def name(self):
        """
        Get the users full name
        """
        return self.first_name + " " + self.last_name
User.__bases__ += (UserMethods,)