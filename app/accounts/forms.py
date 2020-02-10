from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class InviteConsumeForm(UserCreationForm):
    class Meta(object):
        model = User
        fields = ("first_name", "last_name", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super(InviteConsumeForm, self).__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


class ArticleAdminForm(forms.ModelForm):
    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data["email"]).exists():
            raise forms.ValidationError("User with that email address already exists")
        return self.cleaned_data["email"]
