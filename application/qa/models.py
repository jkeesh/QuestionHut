from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    user        =   models.OneToOneField(User)

class Tag(models.Model):
    title       =   models.CharField(max_length=200)
    
    def __unicode__(self):
        return "%s" % self.title

class Question(models.Model):
    author      =   models.ForeignKey(User)
    votes       =   models.IntegerField(default=0)
    views       =   models.IntegerField(default=0)
    title       =   models.CharField(max_length=200)
    content     =   models.TextField()
    created_at  =   models.DateTimeField(auto_now_add=True)
    tags        =   models.ManyToManyField(Tag)   
    
    def __unicode__(self):
        return "%s: %s (%d)" % (self.author, self.title, self.votes)
    
class Answer(models.Model):
    author      =   models.ForeignKey(User)
    content     =   models.TextField()
    votes       =   models.IntegerField(default=0)
    created_at  =   models.DateTimeField(auto_now_add=True)
    question    =   models.ForeignKey(Question, related_name='answers')
    
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