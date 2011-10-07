from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Course(models.Model):
    title       =   models.CharField(max_length=50)
    
    def __unicode__(self):
        return "%s" % self.title

class UserProfile(models.Model):
    user        =   models.OneToOneField(User)
    courses     =   models.ManyToManyField(Course, related_name='students')
    is_moderator=   models.BooleanField(default=False)
    moderator_courses   =   models.ManyToManyField(Course, related_name='moderators')
    confirmation_code   =   models.CharField(max_length=100, default='')

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
        if self.kind == 'A':
            obj = Answer.objects.get(pk=self.obj_id)
        else:
            obj = Question.objects.get(pk=self.obj_id)
                    
        obj.votes += score_change
        obj.save()
        return obj.votes
        
    def undo(self, new_score):
        ## If the new score == old score, this is an 'undo'
        should_delete = self.score == new_score

        undo_change = self.score * -1 # This undoes the vote
        votes = self.update_vote_count(undo_change)
        if should_delete:
            self.delete()
        return should_delete, votes
    
    @staticmethod
    def submit_vote(request):
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
    
    
    def get_answer_count(self):
        return len(self.answers.filter(approved=True))
    
    def deselect_all_answers(self):
        self.answers.all().update(selected=False)
    
    def select_answer(self, answer):
        self.deselect_all_answers()
        answer.selected = True
        answer.save()
        self.answered = True
        self.save()
        
    def add_tag(self, tag_title): 
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
       
class Answer(models.Model):
    author      =   models.ForeignKey(User)
    content     =   models.TextField()
    votes       =   models.IntegerField(default=0)
    created_at  =   models.DateTimeField(auto_now_add=True)
    last_updated=   models.DateTimeField(auto_now=True)
    question    =   models.ForeignKey(Question, related_name='answers')
    selected    =   models.BooleanField(default=False)
    approved    =   models.BooleanField(default=False)
    
    def moderate(self, action):
        if action == 'approve':
            self.approved = True
            self.save()
        else:
            self.delete()
    
    def __unicode__(self):
        return "%s: %s (%d)" % (self.author, self.content[:15], self.votes)
    
    
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