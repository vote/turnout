from typing import List

from django import forms

from .models import LeoContactOverride


class LeoContactOverrideManageUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["submission_method"].required = False
        self.fields["submission_method"].label = "Override Submission Method"
        self.fields["email"].required = False
        self.fields["phone"].required = False
        self.fields["fax"].required = False

    class Meta(object):
        model = LeoContactOverride
        fields = ["submission_method", "email", "phone", "fax"]


class LeoContactOverrideManageDeleteForm(forms.ModelForm):
    class Meta(object):
        model = LeoContactOverride
        fields: List[str] = []


class LeoContactOverrideManageCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].widget = forms.TextInput()
        self.fields["region"].label = "Region ID"

        self.fields["submission_method"].required = False
        self.fields["submission_method"].label = "Override Submission Method"

        self.fields["email"].required = False
        self.fields["phone"].required = False
        self.fields["fax"].required = False

    class Meta(object):
        model = LeoContactOverride
        fields = ["region", "submission_method", "email", "phone", "fax"]
