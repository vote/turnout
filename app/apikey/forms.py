from django import forms

from .models import ApiKey


class ApiKeyDeactivateForm(forms.ModelForm):
    confirm = forms.BooleanField(required=True)

    def clean_confirm(self):
        data = self.cleaned_data["confirm"]
        if data:
            return data
        else:
            raise forms.ValidationError("You must confirm API key deactivation.")

    class Meta:
        model = ApiKey
        fields = [
            "confirm",
        ]
        help_texts = {
            "confirm": "Confirm deactivate of API Key",
        }


class ApiKeyCreateForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        fields = [
            "description",
        ]
        help_texts = {
            "description": "Short name/description for this API Key",
        }
        widgets = {
            "description": forms.TextInput,
        }
