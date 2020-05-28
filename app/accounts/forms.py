from django import forms
from django.contrib.auth.forms import UserCreationForm
from timezone_field import TimeZoneFormField

from .models import TIMEZONE_CHOICES, User


class InviteConsumeForm(UserCreationForm):
    timezone = TimeZoneFormField(choices=TIMEZONE_CHOICES)

    class Meta(object):
        model = User
        fields = ["first_name", "last_name", "timezone", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super(InviteConsumeForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


class ArticleAdminForm(forms.ModelForm):
    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data["email"]).exists():
            raise forms.ValidationError("User with that email address already exists")
        return self.cleaned_data["email"]


class UpdateProfileForm(forms.ModelForm):
    timezone = TimeZoneFormField(choices=TIMEZONE_CHOICES)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "timezone"]
