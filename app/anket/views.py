from django.shortcuts import render
from django.contrib.auth.views import LoginView

# giris icin view
class CustomLoginView(LoginView):
    template_name = "login/login.html"

