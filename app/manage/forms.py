from django import forms
from django.contrib.auth.forms import AuthenticationForm as DjangoAuthenticationForm


class AuthenticationForm(DjangoAuthenticationForm):
    """Form for authentication"""

    username = forms.CharField(
        label="Email",
        max_length=254,
        widget=forms.TextInput(attrs={"autofocus": True, "placeholder": "Email"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
    )
