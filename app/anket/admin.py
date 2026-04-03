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

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]

admin.site.register(Option)
admin.site.register(Vote)
admin.site.register(PollParticipation)
