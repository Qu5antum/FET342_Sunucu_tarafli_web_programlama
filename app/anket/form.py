from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class UserAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(label="Email")

    def clean(self):
        email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if email and password:
            if not User.objects.filter(email=email).exists():
                raise forms.ValidationError("Hesap veya Şifre yanlış")

            self.user_cache = authenticate(
                self.request,
                email=email,
                password=password
            )

            if self.user_cache is None:
                raise forms.ValidationError("Hesap veya Şifre yanlış")

            if not self.user_cache.is_active:
                raise forms.ValidationError("Hesap kapalı")

        return self.cleaned_data