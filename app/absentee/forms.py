from typing import List

from django import forms

from .models import RegionOVBMLink


class RegionOVBMLinkManageUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["url"].required = False

    class Meta(object):
        model = RegionOVBMLink
        fields = ["url"]


class RegionOVBMLinkManageDeleteForm(forms.ModelForm):
    class Meta(object):
        model = RegionOVBMLink
        fields: List[str] = []


class RegionOVBMLinkManageCreateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["region"].widget = forms.TextInput()
        self.fields["region"].label = "Region ID"
        self.fields[
            "region"
        ].help_text = 'You can find this ID by going to <a href="https://www.voteamerica.com/local-election-offices/" target="_blank">the LEO tool</a>, looking up the region, and copying the ID from the URL. For example, the ID for Cambridge, MA is 431101.'

        self.fields["url"].required = False

    def clean_region(self):
        region = self.cleaned_data["region"]

        if region.state.code == "FL":
            raise forms.ValidationError("Florida regions are managed automatically.")

        return region

    class Meta(object):
        model = RegionOVBMLink
        fields = ["region", "url"]
