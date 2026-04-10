from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
import json

from .models import Poll, PollParticipation, Option, Vote, Group, Question


def in_editor_group(user):
    return user.groups.filter(name='teacher').exists()

# giris icin view
class CustomLoginView(LoginView):
    template_name = "login/login.html"


@login_required
@user_passes_test(in_editor_group)
@transaction.atomic
def create_poll(request):
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")

        group_ids = request.POST.getlist("groups")

        poll = Poll.objects.create(
            title=title,
            description=description
        )

        groups = Group.objects.filter(id__in=group_ids)
        poll.groups.set(groups)

        questions_json = request.POST.get("questions")
        questions_data = json.loads(questions_json)

        for q in questions_data:
            question = Question.objects.create(
                text=q["text"],
                poll=poll
            )

            Option.objects.bulk_create([
                Option(text=opt, question=question)
                for opt in q.get("options", [])
            ])

        return redirect("poll_list") 

    groups = Group.objects.all()
    return render(request, "anket/create_poll.html", {"groups": groups})

    
# anketlerin listelenme sayfasi
@login_required
def poll_list(request):
    polls = Poll.objects.filter(
        # student yada teacher olarak gruplara filtreleme
        groups__in=request.user.groups.all()
    ).distinct()

    return render(request, "anket/list.html", {"polls": polls})


# tek bir anketin detayi
@login_required
def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if not poll.groups.filter(id__in=request.user.groups.all()).exists():
        return redirect("polls")
    
    # sadece bir kere anketi doldumasi eger doldurduysan sonuc goster
    if PollParticipation.objects.filter(user=request.user, poll=poll).exists():
        return redirect("anket:poll_results", poll_id=poll.id)

    return render(request, "anket/poll_detail.html", {"poll": poll})


# oylama sistemi
@login_required
def vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if PollParticipation.objects.filter(user=request.user, poll=poll).exists():
        return redirect("anket:poll_results", poll_id=poll.id)

    if request.method != "POST":
        return redirect("anket:poll_detail", poll_id=poll.id)

    questions = poll.question_set.all()

    for question in questions:
        if not request.POST.get(f"question_{question.id}"):
            messages.error(request, "Tüm soruları cevaplamalısınız.")
            return redirect("anket:poll_detail", poll_id=poll.id)

    for question in questions:
        option_id = request.POST.get(f"question_{question.id}")
        option = get_object_or_404(Option, id=option_id, question=question)

        Vote.objects.update_or_create(
            user=request.user,
            poll=poll,
            question=question,
            defaults={"option": option}
        )

    PollParticipation.objects.get_or_create(user=request.user, poll=poll)

    messages.success(request, "Oy başarıyla kaydedildi.")

    return redirect("anket:poll_results", poll_id=poll.id)

# oylama sonucu
@login_required
def poll_results(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    questions = poll.question_set.all()

    for question in questions:
        options = question.option_set.all()

        for option in options:
            option.vote_count = Vote.objects.filter(
                question=question,
                option=option
            ).count()

        question.options = options

    return render(request, "anket/results.html", {
        "poll": poll,
        "questions": questions
    })
            

