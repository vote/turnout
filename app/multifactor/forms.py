from django import forms
from django_otp.models import VerifyNotAllowed

from common.analytics import statsd


class TokenForm(forms.Form):
    token = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"autocomplete": "off"})
    )

    def __init__(self, device=None, request=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.device = device

    def clean_token(self):
        token = self.cleaned_data["token"]

        verify_is_allowed, extra = self.device.verify_is_allowed()
        if not verify_is_allowed:
            statsd.increment("turnout.multifactor.verification_not_allowed")
            statsd.increment("turnout.multifactor.verification_failure")
            # Try to match specific conditions we know about.
            if (
                "reason" in extra
                and extra["reason"] == VerifyNotAllowed.N_FAILED_ATTEMPTS
            ):
                raise forms.ValidationError(
                    "Verification temporarily disabled because of too many failed attempts, please try again soon."
                )
            if "error_message" in extra:
                raise forms.ValidationError(extra["error_message"])
            # Fallback to generic message otherwise.
            raise forms.ValidationError(
                "Verification of the token is currently disabled"
            )

        verified = self.device.verify_token(token)

        if not verified:
            statsd.increment("turnout.multifactor.verification_failure")
            raise forms.ValidationError("Invalid token")

        statsd.increment("turnout.multifactor.verification_success")
