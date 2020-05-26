from datetime import date
from typing import List

from django import forms
from django.core.validators import EmailValidator, URLValidator
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber

from common.enums import StateFieldFormats

from .models import LeoContactOverride


class LeoContactOverrideManageUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = False
        self.fields["phone"].required = False
        self.fields["fax"].required = False

    class Meta(object):
        model = LeoContactOverride
        fields = ["email", "phone", "fax"]


class LeoContactOverrideManageDeleteForm(forms.ModelForm):
    class Meta(object):
        model = LeoContactOverride
        fields: List[str] = []


class LeoContactOverrideManageCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].widget = forms.TextInput()
        self.fields["region"].label = "Region ID"

        self.fields["email"].required = False
        self.fields["phone"].required = False
        self.fields["fax"].required = False

    class Meta(object):
        model = LeoContactOverride
        fields = ["region", "email", "phone", "fax"]
