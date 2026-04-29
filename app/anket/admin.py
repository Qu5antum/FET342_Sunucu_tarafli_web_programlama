from django.contrib import admin
from .models import Option, Question, Vote, Poll, PollParticipation

class OptionInline(admin.TabularInline):
    model = Option
    extra = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    
@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    filter_horizontal = ("groups",)
    list_display = ("title", "created_at")


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    list_display = ("text", "poll")


@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question")


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("user", "poll", "question", "option")
    list_filter = ("poll", "question")
