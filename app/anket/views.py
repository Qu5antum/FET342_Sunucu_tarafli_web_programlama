from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
import json
import csv

from .models import Poll, PollParticipation, Option, Vote, Group, Question, User

def in_editor_group(user):
    return user.groups.filter(name='teacher').exists()

# giris icin view
class CustomLoginView(LoginView):
    template_name = "login/login.html"

# çıkış için view
def logout_user(request):
    logout(request)
    return redirect("login/login.html")

# anket oluşturma (sadece hocalar görebilir)
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

        return redirect("anket:polls") 

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
            

# sonuçları csv formatında indirme
@login_required
def import_csv(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="poll_{poll_id}_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Anket', 'Soru', 'Seçenek', 'Oy'])

    options = Option.objects.filter(question__poll=poll).annotate(
        vote_count=Count('vote')
    )

    for option in options:
        writer.writerow([
            poll.title,
            option.question.text,
            option.text,
            option.vote_count
        ])

    return response


@login_required
def list_poll_of_students_for_teacher(request):
    polls = Poll.objects.filter(groups__name="student")

    return render(request, "anket/teacher_poll_list.html", {"polls": polls})


# oy özetleme
@login_required
def poll_summary_dashboard(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)

    groups = poll.groups.all()

    total_potential_users = User.objects.filter(
        groups__in=groups
    ).distinct().count()

    if total_potential_users == 0:
        total_potential_users = User.objects.count()

    total_votes = Vote.objects.filter(poll=poll).count()

    participation_rate = (
        (total_votes / total_potential_users) * 100
        if total_potential_users > 0 else 0
    )

    questions_data = []

    questions = Question.objects.filter(poll=poll)

    for question in questions:

        options = Option.objects.filter(question=question)

        options_with_votes = []

        max_votes = 0

        for option in options:
            votes_count = Vote.objects.filter(option=option).count()

            if votes_count > max_votes:
                max_votes = votes_count

            options_with_votes.append({
                "text": option.text,
                "votes": votes_count
            })

        choices_list = []

        for opt in options_with_votes:

            percentage = (
                (opt["votes"] / total_votes * 100)
                if total_votes > 0 else 0
            )

            choices_list.append({
                "text": opt["text"],
                "votes": opt["votes"],
                "percentage": round(percentage, 2),
                "is_winner": opt["votes"] == max_votes and max_votes > 0
            })

        questions_data.append({
            "question_text": question.text,
            "choices": choices_list
        })

    context = {
        "poll": poll,
        "total_votes": total_votes,
        "total_potential_users": total_potential_users,
        "participation_rate": round(participation_rate, 2),
        "questions_data": questions_data,
    }

    return render(request, "anket/poll_summary.html", context)
    
# anket silme
@login_required
@permission_required('anket.delete_poll', raise_exception=True)
def delete_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if request.method == "POST":
        poll.delete()
        return redirect("anket:student_poll") 

    return render(request, "anket/delete.html", {"poll": poll})

# kullanicinin kendi hesabi gorunteleme
@login_required
def get_my_info(request):
    context = {
        'user': request.user
    }

    return render(request, 'anket/account.html', context)
