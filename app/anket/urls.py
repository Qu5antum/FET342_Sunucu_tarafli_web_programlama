from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import CustomLoginView, poll_list, poll_detail, vote, poll_results, create_poll, import_csv, list_poll_of_students_for_teacher, poll_summary_dashboard, delete_poll, get_my_info, poll_by_token

app_name = "anket"

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name='logout'),
    path("account/", get_my_info, name="account"),
    path("polls/", poll_list, name="polls"),
    path("poll/<uuid:token>/", poll_by_token, name="poll_by_token"),
    path("polls/<int:poll_id>/", poll_detail, name="poll_detail"),
    path("polls/<int:poll_id>/vote/", vote, name="vote"),
    path("polls/<int:poll_id>/results/", poll_results, name="poll_results"),
    path("create_poll/", create_poll, name="create_poll"),
    path('polls/<int:poll_id>/export/', import_csv, name='export_poll'),
    path('polls/student_polls/', list_poll_of_students_for_teacher, name="student_poll"),
    path('polls/<int:poll_id>/summary/', poll_summary_dashboard, name='poll_summary'),
    path('polls/<int:poll_id>/delete/', delete_poll, name='delete_poll')
]