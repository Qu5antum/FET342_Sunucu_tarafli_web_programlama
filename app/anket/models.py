from django.db import models

# Kullanici gruplar (student ve teacher) django nun kendi default modelleri
from django.contrib.auth.models import User, Group

# Anket modeli
class Poll(models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    groups = models.ManyToManyField(Group)
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

# kullanicinin 1 sadece 1 kez oy yapabilmesi
class PollParticipation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'poll')
