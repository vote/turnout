from typing import List

from django import forms
from django.forms import Select

from absentee.contactinfo import get_absentee_contact_info
from absentee.models import LeoContactOverride
from official.models import Region


class SubmissionMethodSelect(Select):
    """
    Subclass of Django's select widget that disable unavailable options
    """

    def __init__(self, region_id, *args, **kwargs):
        self._region = (
            Region.objects.select_related("state")
            .select_related("state__absentee_dashboard_data")
            .get(pk=region_id)
        )
        self._contact_info = get_absentee_contact_info(region_id)

        super().__init__(*args, **kwargs)

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option_dict = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        if value == "leo_email":
            if not self._region.state.absentee_dashboard_data.email_allowed:
                option_dict["attrs"]["disabled"] = "disabled"
                option_dict["label"] = "LEO Email (Not Permitted By State)"

            if not self._contact_info.email:
                option_dict["attrs"]["disabled"] = "disabled"
                option_dict[
                    "label"
                ] = "LEO Email (No USVF Email; add an override email to enable)"

        if value == "leo_fax":
            if not self._region.state.absentee_dashboard_data.fax_allowed:
                option_dict["attrs"]["disabled"] = "disabled"
                option_dict["label"] = "LEO Fax (Not Permitted By State)"

            if not self._contact_info.fax:
                option_dict["attrs"]["disabled"] = "disabled"
                option_dict[
                    "label"
                ] = "LEO Fax (No USVF Fax; add an override fax to enable)"

        return option_dict


class LeoContactOverrideManageUpdateForm(forms.ModelForm):
    def __init__(self, region_id, usvf_data, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["submission_method"].widget = SubmissionMethodSelect(
            region_id, choices=self.fields["submission_method"].choices
        )
        self.fields["submission_method"].required = False
        self.fields["submission_method"].label = "Override Submission Method"

        self.fields["email"].required = False
        self.fields["email"].help_text = f"USVF Data: {usvf_data.email}"

        self.fields["phone"].required = False
        self.fields["phone"].help_text = f"USVF Data: {usvf_data.phone}"

        self.fields["fax"].required = False
        self.fields["fax"].help_text = f"USVF Data: {usvf_data.fax}"

    class Meta(object):
        model = LeoContactOverride
        fields = ["submission_method", "email", "phone", "fax", "notes"]


class LeoContactOverrideManageDeleteForm(forms.ModelForm):
    class Meta(object):
        model = LeoContactOverride
        fields: List[str] = []


class LeoContactOverrideManageCreateForm(LeoContactOverrideManageUpdateForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._region_id = kwargs["region_id"]

    def save(self, *args, **kwargs):
        self.instance.region_id = self._region_id
        return super().save(*args, **kwargs)
