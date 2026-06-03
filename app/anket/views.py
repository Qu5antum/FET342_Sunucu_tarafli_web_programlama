from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Count
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse
from django.utils import timezone
import json
import csv
from datetime import datetime

from .models import Poll, PollParticipation, Option, Vote, Group, Question, User, Visibility, PollShare, QuestionType, PollComment
from .form import UserAuthenticationForm

def in_editor_group(user):
    return user.groups.filter(name='teacher').exists()

# giris icin view
class CustomLoginView(LoginView):
    template_name = "login/login.html"
    authentication_form = UserAuthenticationForm

# çıkış için view
def logout_user(request):
    logout(request)
    return redirect("login/login.html")


def generate_share_link(request, poll):
    share, created = PollShare.objects.get_or_create(
        poll=poll,
        defaults={}
    )

    url = request.build_absolute_uri(
        reverse("anket:poll_by_token", args=[str(share.token)])
    )

    return url

# anket oluşturma (sadece hocalar görebilir)
@login_required
@transaction.atomic
def create_poll(request):
    url = None

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        visibility = request.POST.get("visibility", Visibility.PRIVATE)
        expires_at_raw = request.POST.get("expires_at")

        expires_at = None

        if expires_at_raw:
            try:
                expires_at = datetime.strptime(
                    expires_at_raw,
                    "%Y-%m-%d %H:%M"
                )

                expires_at = timezone.make_aware(expires_at)

                if expires_at <= timezone.now():
                    messages.error(
                        request,
                        "Son tarih gelecekte olmalıdır."
                    )

                    return redirect("anket:create_poll")

            except ValueError:
                messages.error(
                    request,
                    "Geçersiz tarih formatı."
                )

                return redirect("anket:create_poll")

        if visibility not in Visibility.values:
            visibility = Visibility.PRIVATE

        group_ids = request.POST.getlist("groups")

        allow_vote_cancel = (request.POST.get("allow_vote_cancel") == "on")

        poll = Poll.objects.create(
            title=title,
            description=description,
            visibility=visibility,
            expires_at=expires_at,
            allow_vote_cancel=allow_vote_cancel
        )

        groups = Group.objects.filter(id__in=group_ids)
        poll.groups.set(groups)

        questions_json = request.POST.get("questions")
        questions_data = json.loads(questions_json)

        for q in questions_data:
            question = Question.objects.create(
                text=q["text"],
                poll=poll,
                type=q.get("type", QuestionType.SINGLE)
            )

            Option.objects.bulk_create([
                Option(text=opt, question=question)
                for opt in q.get("options", [])
            ])

        
        if poll.visibility == Visibility.PRIVATE:
            url = generate_share_link(request, poll)

        return render(request, "anket/created_poll.html", {
            "poll": poll,
            "url": url
        })    

    return render(request, "anket/create_poll.html", {
        "groups": Group.objects.all(),
        "visibilities": Visibility.choices,
        "url": None
    })

# kapali ankete katilma linki 
@login_required
def poll_by_token(request, token):
    try:
        share = PollShare.objects.select_related("poll").get(token=token)
    except PollShare.DoesNotExist:
        raise Http404
    
    poll = share.poll
    user = request.user

    has_group_access = poll.groups.filter(
        id__in=user.groups.all()
    ).exists()

    if not has_group_access:
        return HttpResponseForbidden("Bu ankete erişim izniniz yok")
    
    already_voted = Vote.objects.filter(
        user=user,
        poll=poll
    ).exists()

    if already_voted:
        return redirect("anket:poll_results", poll_id=poll.id)

    return render(request, "anket/poll_detail.html", {
        "poll": poll
    })
    
# anketlerin listelenme sayfasi
@login_required
def poll_list(request):
    polls = Poll.objects.filter(
        # student yada teacher olarak gruplara filtreleme, ve sadece public olanlari gosterme
        groups__in=request.user.groups.all(),
        visibility=Visibility.PUBLIC
    ).distinct()

    return render(request, "anket/list.html", {"polls": polls})


# tek bir anketin detayi
@login_required
def poll_detail(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if poll.expires_at and timezone.now() > poll.expires_at:
        voted = PollParticipation.objects.filter(
            user=request.user,
            poll=poll
        ).exists()

        if voted:
            message = "Anket sona erdi. Katılımınız için teşekkür ederiz."
        else:
            message = "Anket sona erdi. Oy verme süresi doldu."

        return render(request, "anket/anket_expired.html", {
            "poll": poll,
            "message": message
        })
    
    # sadece bir kere anketi doldumasi eger doldurduysan sonuc goster
    if PollParticipation.objects.filter(user=request.user, poll=poll).exists():
        return redirect("anket:poll_results", poll_id=poll.id)

    if not poll.groups.filter(id__in=request.user.groups.all()).exists():
        return redirect("polls")

    return render(request, "anket/poll_detail.html", {"poll": poll})


# oylama sistemi
@login_required
def vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if PollParticipation.objects.filter(
        user=request.user,
        poll=poll
    ).exists():
        return redirect("anket:poll_results", poll_id=poll.id)

    if request.method != "POST":
        return redirect("anket:poll_detail", poll_id=poll.id)

    questions = poll.question_set.all()

    for question in questions:

        if question.type == QuestionType.SINGLE:

            selected = request.POST.get(
                f"question_{question.id}"
            )

            if not selected:
                messages.error(request, "Tüm soruları cevaplamalısınız.")

                return redirect("anket:poll_detail", poll_id=poll.id)
        else:
            selected = request.POST.getlist(
                f"question_{question.id}"
            )

            if not selected:
                messages.error(request, "Tüm soruları cevaplamalısınız.")

                return redirect("anket:poll_detail", poll_id=poll.id)

    for question in questions:
        Vote.objects.filter(
            user=request.user,
            question=question
        ).delete()

        if question.type == QuestionType.MULTIPLE:

            option_ids = request.POST.getlist(
                f"question_{question.id}"
            )

            for option_id in option_ids:

                option = get_object_or_404(
                    Option,
                    id=option_id,
                    question=question
                )

                Vote.objects.create(
                    user=request.user,
                    poll=poll,
                    question=question,
                    option=option
                )
        else:
            option_id = request.POST.get(
                f"question_{question.id}"
            )

            option = get_object_or_404(
                Option,
                id=option_id,
                question=question
            )

            Vote.objects.create(
                user=request.user,
                poll=poll,
                question=question,
                option=option
            )
        
    feedback_message = request.POST.get("feedback_message","").strip()
    
    if feedback_message:
        PollComment.objects.update_or_create(
            user=request.user,
            poll=poll,
            defaults={
                "message": feedback_message
            }
        )

    PollParticipation.objects.get_or_create(
        user=request.user,
        poll=poll
    )

    messages.success(
        request,
        "Oy başarıyla kaydedildi."
    )

    return redirect(
        "anket:poll_results",
        poll_id=poll.id
    )

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

    poll_comments = PollComment.objects.filter(
        poll=poll
    ).select_related("user")

    return render(request, "anket/results.html", {
        "poll": poll,
        "questions": questions,
        "poll_comments": poll_comments
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
@user_passes_test(in_editor_group)
def list_poll_of_students_for_teacher(request):
    polls = Poll.objects.filter(
        groups__name="student",
        visibility = Visibility.PUBLIC
    )

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

@login_required
def cancel_vote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if not poll.allow_vote_cancel:
        message.error(request, "Bu ankette oy iptali kapalıdır")

        return redirect("anket:poll_results", poll_id=poll.id)

    if poll.expires_at and timezone.now() > poll.expires_at:
        voted = PollParticipation.objects.filter(
            user=request.user,
            poll=poll
        ).exists()

        if voted:
            message = "Anket sona erdi. Katılımınız için teşekkür ederiz."
        else:
            message = "Anket sona erdi. Oy verme süresi doldu."

        return render(request, "anket/anket_expired.html", {
            "poll": poll,
            "message": message
        })

    if request.method == "POST":
        Vote.objects.filter(
            user=request.user,
            poll=poll
        ).delete

    PollParticipation.objects.filter(
        user=request.user,
        poll=poll
    ).delete()

    return redirect("anket:poll_detail", poll_id=poll.id)