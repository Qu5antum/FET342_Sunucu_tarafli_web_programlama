from django.db import models
import uuid

# Kullanici gruplar (student ve teacher) django nun kendi default modelleri
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

User = get_user_model()

class Visibility(models.TextChoices):
    PRIVATE = 'private', 'Private'
    PUBLIC = 'public', 'Public'
    

class Permission(models.TextChoices):
    EDIT = 'Edit', 'edit'
    VOTE = 'Vote', 'vote'

# Anket modeli
class Poll(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    groups = models.ManyToManyField(Group)
    
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.PRIVATE  
    )

    created_at = models.DateField(auto_now_add=True)


# Anketi paylaşmak için link oluşturması
class PollShare(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    token = models.UUIDField(default=uuid.uuid4, unique=True)

    permission = models.CharField(
        max_length=20,
        choices=Permission.choices,
        default=Permission.EDIT
    )

    created_at = models.DateField(auto_now_add=True)
    

# Soru modeli
class Question(models.Model):
    text = models.CharField(max_length=200)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

# Sorunun Seçenek modeli
class Option(models.Model):
    text = models.CharField(max_length=100)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)

# Oy modeli
class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option = models.ForeignKey(Option, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'poll', 'question')

# kullanicinin sadece 1 kez oy yapabilmesi
class PollParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'poll')
