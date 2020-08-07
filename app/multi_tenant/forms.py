from typing import List

from django import forms
from django.utils.safestring import mark_safe

from accounts.models import Invite
from common.enums import ExternalToolType

from .models import (
    Association,
    Client,
    InviteAssociation,
    SubscriberIntegrationProperty,
)

API_KEY_PLACEHOLDER = "________________________________"


class ChangeSubscriberManageForm(forms.Form):
    # ModelChoiceFields have to have a queryset as a kwarg of the same type as the
    # final queryset. We set the actual choices inside the FormView, so by default
    # we set this to `.none()`
    subscriber = forms.ModelChoiceField(queryset=Client.objects.none())


class SubscriberSettingsForm(forms.ModelForm):
    sync_actionnetwork = forms.BooleanField(
        required=False,
        label="Enable ActionNetwork Sync",
        help_text="If new contacts should be added to your <a href='https://actionnetwork.org/'>ActionNetwork</a> email list",
    )
    actionnetwork_api_key = forms.CharField(
        max_length=64,
        required=False,
        label="ActionNetwork API Key",
        help_text="New ActionNetwork API key (leave blank if unchanged)",
        widget=forms.PasswordInput(render_value=True),
    )

    def clean(self):
        cleaned_data = super().clean()
        an = cleaned_data.get("sync_actionnetwork")
        an_key = cleaned_data.get("actionnetwork_api_key")
        if an_key and an_key != API_KEY_PLACEHOLDER and not an:
            self.add_error(
                "actionnetwork_api_key",
                "Cannot provide ActionNetwork API key without enabling ActionNetwork sync",
            )
        old_key = SubscriberIntegrationProperty.objects.filter(
            subscriber=self.instance,
            external_tool=ExternalToolType.ACTIONNETWORK,
            name="api_key",
        ).first()
        if an and not an_key and not old_key:
            self.add_error(
                "actionnetwork_api_key",
                "Must provide API key to enable ActionNetwork sync",
            )

    class Meta:
        model = Client
        fields = [
            "name",
            "url",
            "privacy_policy",
            "sms_enabled",
            "sms_checkbox",
            "sms_checkbox_default",
            "sync_tmc",
            "sync_bluelink",
        ]
        labels = {
            "sync_tmc": "Enable The Movement Cooperative Sync",
            "sync_bluelink": "Enable Bluelink Sync",
        }
        help_texts = {
            "name": "The name your organization will be referred to as throughout the tools.",
            "url": "The URL of your homepage.",
            "privacy_policy": "The URL of your privacy policy. This is highly recommended.",
            "sms_enabled": "If your organization has a SMS program.",
            "sms_checkbox": "If your organization requires a checkbox to be checked by users. Leave unchecked if you have no SMS program.",
            "sms_checkbox_default": "If, by default, your organization's SMS checkbox is checked. Leave this unchecked if you have no SMS program or no SMS checkbox.",
            "sms_disclaimer": "If you wish to have a custom disclaimer, or next to your checkbox if you have one.",
            "sync_tmc": mark_safe(
                "If your data should be included in a nightly sync to <a href='https://movementcooperative.org/' target='_blank' rel='noopener noreferrer'>The Movement Cooperative</a>."
            ),
            "sync_bluelink": mark_safe(
                "If your data should be included in a nightly sync to <a href='https://bluelink.org/lightrail/' target='_blank' rel='noopener noreferrer'>Bluelink</a>. "
                "Bluelink can flow your data to <a href='https://bluelink.org/lightrail/#integrations' target='_blank' rel='noopener noreferrer'>many tools</a>."
            ),
        }
        field_classes = {
            "sms_enabled": forms.BooleanField,
            "sms_checkbox": forms.BooleanField,
            "sms_checkbox_default": forms.BooleanField,
            "sync_tmc": forms.BooleanField,
            "sync_bluelink": forms.BooleanField,
        }


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
