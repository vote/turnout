from django import forms

from common import enums
from multi_tenant.forms import sms_mode_choice
from multi_tenant.models import Client, SubscriberSlug

from .models import Interest, Subscription


class InterestForm(forms.ModelForm):
    sms_mode = sms_mode_choice

    plan = forms.ChoiceField(
        choices=[
            # (
            #     enums.SubscriberPlan.FREE,
            #     "Free: Embed VoteAmerica's tools on your own website and see aggregated stats, at no cost.",
            # ),
            (
                enums.SubscriberPlan.PREMIUM,
                "Premium - $2,000/mo: Get contact information for voters who use your instance of the VoteAmerica tools.",
            ),
            (
                enums.SubscriberPlan.NONPROFIT,
                "Nonprofit - $0/mo: 501(c)3 charitable organizations can use VoteAmerica's premium tools for free.",
            ),
        ],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Interest
        fields = [
            "organization_name",
            "website",
            "first_name",
            "last_name",
            "email",
            "phone",
            "plan",
            "ein",
            "sms_mode",
        ]
        labels = {
            "organization_name": "Organization Name",
            "first_name": "First Name",
            "last_name": "Last Name",
            "ein": "If you are signing up for the Nonprofit plan, please provide your EIN here.",
        }
        widgets = {
            "organization_name": forms.TextInput,
            "first_name": forms.TextInput,
            "last_name": forms.TextInput,
            "ein": forms.TextInput,
        }

    def clean(self):
        cleaned_data = super().clean()

        if (
            cleaned_data["plan"] == str(enums.SubscriberPlan.NONPROFIT)
            and not cleaned_data["ein"]
        ):
            self.add_error(
                "ein", "In order to receive a 501(c)3 discount, you must provide an EIN"
            )


class SubscriberAdminSettingsForm(forms.ModelForm):
    sms_mode = sms_mode_choice

    class Meta:
        model = Client
        fields = [
            "name",
            "url",
            "email",
            "privacy_policy",
            "sms_disclaimer",
            "sync_tmc",
            "sync_bluelink",
        ]
        help_texts = {
            "email": "Only change this after the subscriber has added our DKIM records",
        }
        field_classes = {
            "sync_tmc": forms.BooleanField,
            "sync_bluelink": forms.BooleanField,
        }


class SubscriptionAdminSettingsForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = [
            "primary_contact_first_name",
            "primary_contact_last_name",
            "primary_contact_email",
            "primary_contact_phone",
            "plan",
            "internal_notes",
        ]
        widgets = {
            "primary_contact_first_name": forms.TextInput,
            "primary_contact_last_name": forms.TextInput,
        }


class ActivateInterestForm(forms.ModelForm):
    slug = forms.SlugField(
        help_text="A short word for the subscriber, with no spaces e.g. 'voteamerica' or 'example-company'"
    )
    initial_user = forms.EmailField(help_text="First admin to be invited")

    class Meta:
        model = Client
        fields = [
            "name",
            "url",
            "slug",
            "initial_user",
        ]

    def clean_slug(self):
        data = self.cleaned_data["slug"]
        if SubscriberSlug.objects.filter(slug=data).exists():
            raise forms.ValidationError(f"Subscriber slug '{data}' is already in use")
        return data


class RejectInterestForm(forms.ModelForm):
    class Meta:
        model = Interest
        fields = [
            "reject_reason",
        ]
        help_texts = {
            "reject_reason": "Explanation (to be sent to user)",
        }
        field_class = {
            "reject_reason": forms.Textarea(attrs={"rows": 5}),
        }
