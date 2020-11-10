from django import forms

from multi_tenant.forms import sms_mode_choice
from multi_tenant.models import Client, SubscriberSlug

from .models import Interest, Product


class InterestForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        label="Term",
        queryset=Product.objects.filter(public=True),
        widget=forms.RadioSelect,
    )
    sms_mode = sms_mode_choice

    class Meta:
        model = Interest
        fields = [
            "organization_name",
            "website",
            "first_name",
            "last_name",
            "email",
            "product",
            "nonprofit",
            "ein",
            "sms_mode",
        ]
        labels = {
            "organization_name": "Organization Name",
            "first_name": "First Name",
            "last_name": "Last Name",
            "nonprofit": "Check here if you are a 501(c)3 Non-Profit organization",
            "ein": "If yes to 501(c)3 please enter the EIN below",
        }
        help_texts = {
            "nonprofit": "If so, you will receive a 100% discount for the entirety of 2020.",
        }
        field_classes = {
            "nonprofit": forms.BooleanField,
        }
        widgets = {
            "organization_name": forms.TextInput,
            "first_name": forms.TextInput,
            "last_name": forms.TextInput,
            "ein": forms.TextInput,
        }

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["nonprofit"] and not cleaned_data["ein"]:
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
            "status",
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
