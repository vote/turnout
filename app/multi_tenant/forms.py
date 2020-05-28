from typing import List

from django import forms

from accounts.models import Invite

from .models import Association, Client, InviteAssociation


class ChangeSubscriberManageForm(forms.Form):
    # ModelChoiceFields have to have a queryset as a kwarg of the same type as the
    # final queryset. We set the actual choices inside the FormView, so by default
    # we set this to `.none()`
    subscriber = forms.ModelChoiceField(queryset=Client.objects.none())


class AssociationManageDeleteForm(forms.ModelForm):
    class Meta:
        model = Association
        fields: List[str] = []


class InviteAssociationManageDeleteForm(forms.ModelForm):
    class Meta:
        model = InviteAssociation
        fields: List[str] = []


class InviteCreateForm(forms.ModelForm):
    class Meta:
        model = Invite
        fields: List[str] = ["email"]
