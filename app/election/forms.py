from datetime import date

from django import forms
from django.core.validators import URLValidator

from common.enums import StateFieldFormats

from .models import StateInformation


class StateInformationManageForm(forms.ModelForm):
    def __init__(self, field_format, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_format = field_format
        if field_format == StateFieldFormats.URL:
            self.fields["text"].widget = forms.URLInput()
            self.fields["text"].label = "URL"
        elif field_format == StateFieldFormats.BOOLEAN:
            self.fields["text"] = forms.ChoiceField(
                choices=[("True", "True"), ("False", "False")],
                label="Boolean",
                widget=forms.RadioSelect,
            )
        elif field_format == StateFieldFormats.DATE:
            self.fields["text"].widget = forms.TextInput()
            self.fields["text"].label = "Date"
            self.fields["text"].help_text = "A date in the format YYYY-MM-DD"
        else:
            self.fields["text"].help_text = "Markdown allowed"

    def clean_text(self) -> str:
        text = self.cleaned_data["text"]
        if text == '':
            return ''
        if self.field_format == StateFieldFormats.URL:
            validator = URLValidator()
            validator(text)
        if self.field_format == StateFieldFormats.BOOLEAN:
            if text not in ["True", "False"]:
                raise forms.ValidationError("Entry must be 'True' or 'False'")
        if self.field_format == StateFieldFormats.DATE:
            try:
                date.fromisoformat(text)
            except ValueError:
                raise forms.ValidationError(
                    "Entry must be a valid date in the format YYYY-MM-DD"
                )
        return text

    class Meta(object):
        model = StateInformation
        fields = ["text", "notes"]
