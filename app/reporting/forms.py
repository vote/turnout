from django import forms

from .models import Report


class ReportCreationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["type"]
