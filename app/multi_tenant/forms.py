from typing import List

from django import forms
from django.utils.safestring import mark_safe

from accounts.models import Invite

from .models import Association, Client, InviteAssociation


class ChangeSubscriberManageForm(forms.Form):
    # ModelChoiceFields have to have a queryset as a kwarg of the same type as the
    # final queryset. We set the actual choices inside the FormView, so by default
    # we set this to `.none()`
    subscriber = forms.ModelChoiceField(queryset=Client.objects.none())


class SubscriberSettingsForm(forms.ModelForm):
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
            "url": "Homepage URL",
            "privacy_policy": "Privacy Policy URL",
            "sms_enabled": "SMS Program Enabled",
            "sms_checkbox": "SMS Checkbox Enabled",
            "sms_checkbox_default": "SMS Checkbox Checked By Default",
            "sms_disclaimer": "SMS Disclaimer",
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


class SignupForm(forms.Form):
    name = forms.CharField(required=True, label="Organization name",)
    email = forms.EmailField(
        required=True,
        label="Contact Email",
        help_text="Primary contact email address for this subscription",
    )
    slug = forms.CharField(
        required=True,
        label="Slug",
        help_text="Short, alphanumeric identifier for your organization that will be included in URLs",
    )
    url = forms.URLField(
        label="URL", required=False, help_text="URL for your organization's web site"
    )
    is_c3 = forms.BooleanField(
        label="501(c)3", required=False, help_text="Check if you are a 501(c)3"
    )
