from django import forms

from .models import Client


class ChangeSubscriberManageForm(forms.Form):
    # ModelChoiceFields have to have a queryset as a kwarg of the same type as the
    # final queryset. We set the actual choices inside the FormView, so by default
    # we set this to `.none()`
    subscriber = forms.ModelChoiceField(queryset=Client.objects.none())
