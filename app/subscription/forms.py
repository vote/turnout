from django import forms

from multi_tenant.models import Client, SubscriberSlug

from .models import Interest, Product


class InterestForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(public=True), widget=forms.RadioSelect
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
            "product",
            "nonprofit",
            "ein",
        ]
        labels = {
            "organization_name": "Organization Name",
            "first_name": "First Name",
            "last_name": "Last Name",
            "product": "Term requested:",
            "nonprofit": "Are you a 501(c)3 nonprofit?",
            "ein": "If yes to 501(c)3 please enter the EIN below",
        }
        help_texts = {
            "nonprofit": "If so, you will receive a 100% discount for the entirety of 2020."
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
    class Meta:
        model = Client
        fields = [
            "name",
            "url",
            "status",
            "email",
            "privacy_policy",
            "sms_enabled",
            "sms_checkbox",
            "sms_checkbox_default",
            "sms_disclaimer",
            "sync_tmc",
            "sync_bluelink",
        ]
        help_texts = {
            "email": "Only change this after the subscriber has added our DKIM records"
        }
        field_classes = {
            "sms_enabled": forms.BooleanField,
            "sms_checkbox": forms.BooleanField,
            "sms_checkbox_default": forms.BooleanField,
            "sync_tmc": forms.BooleanField,
            "sync_bluelink": forms.BooleanField,
        }


class ActivateInterestForm(forms.ModelForm):
    slug = forms.SlugField(help_text="Organization Slug")
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
