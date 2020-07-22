from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from reversion.views import RevisionMixin

from absentee.contactinfo import get_absentee_contact_info
from absentee.models import LeoContactOverride, RegionEsignMethod, StateDashboardData
from action.mixin_manage_views import ActionListViewMixin
from common import enums
from common.rollouts import flag_enabled_for_state
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from election.choices import STATES
from election.mixins_manage_views import ElectionAdminView
from election.models import State
from manage.mixins import ManageViewMixin
from official.models import Region

from .forms import (
    LeoContactOverrideManageCreateForm,
    LeoContactOverrideManageDeleteForm,
    LeoContactOverrideManageUpdateForm,
)


class EsignDashboardView(
    ActionListViewMixin, ManageViewMixin, ElectionAdminView, ListView
):
    model = StateDashboardData
    context_object_name = "states"
    template_name = "absentee/dashboard/state_dashboard.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        esign_states = [
            state_code
            for (state_code, state_name) in STATES
            if flag_enabled_for_state("vbm_esign", state_code)
        ]

        return queryset.filter(state_id__in=esign_states)


class EsignRegionDashboardView(ManageViewMixin, ElectionAdminView, DetailView):
    model = State
    context_object_name = "state"
    template_name = "absentee/dashboard/region_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        filters = {"state": kwargs["object"]}

        if self.request.GET.get("filter") == "leo_email":
            filters["submission_method"] = enums.SubmissionType.LEO_EMAIL

        if self.request.GET.get("filter") == "leo_fax":
            filters["submission_method"] = enums.SubmissionType.LEO_FAX

        if self.request.GET.get("filter") == "self_print":
            filters["submission_method"] = enums.SubmissionType.SELF_PRINT

        if self.request.GET.get("overrides_only"):
            filters["has_override"] = True

        context["regions"] = RegionEsignMethod.objects.select_related(
            "region__esign_stats"
        ).filter(**filters)

        context["total_stats"] = {
            "emails_sent_1d": sum(
                region.region.esign_stats.emails_sent_1d
                for region in context["regions"]
            ),
            "faxes_sent_1d": sum(
                region.region.esign_stats.faxes_sent_1d for region in context["regions"]
            ),
            "emails_sent_7d": sum(
                region.region.esign_stats.emails_sent_7d
                for region in context["regions"]
            ),
            "faxes_sent_7d": sum(
                region.region.esign_stats.faxes_sent_7d for region in context["regions"]
            ),
        }

        return context


class LeoContactOverrideDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/dashboard/leo_contact_override_detail.html"
    slug_field = "uuid"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state"] = State.objects.get(code=self.kwargs["state"])
        context["usvf_data"] = get_absentee_contact_info(
            self.kwargs["pk"], skip_overrides=True
        )

        return context


class LeoContactOverrideUpdateView(
    RevisionMixin, ManageViewMixin, ElectionAdminView, UpdateView
):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/dashboard/leo_contact_override_update.html"
    form_class = LeoContactOverrideManageUpdateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state"] = State.objects.get(code=self.kwargs["state"])

        return context

    def get_form_kwargs(self):
        return {
            "region_id": self.kwargs["pk"],
            "usvf_data": get_absentee_contact_info(
                self.kwargs["pk"], skip_overrides=True
            ),
            **super().get_form_kwargs(),
        }

    def get_success_url(self):
        return reverse(
            "manage:absentee_dashboard:leo_contact_override_detail",
            args=[self.kwargs["state"], self.object.pk],
        )


class LeoContactOverrideDeleteView(
    RevisionMixin, ManageViewMixin, ElectionAdminView, DeleteView
):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/dashboard/leo_contact_override_delete.html"
    form_class = LeoContactOverrideManageDeleteForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state"] = State.objects.get(code=self.kwargs["state"])

        return context

    def get_success_url(self):
        return reverse(
            "manage:absentee_dashboard:esign_region_dashboard",
            args=[self.kwargs["state"]],
        )


class LeoContactOverrideCreateView(
    RevisionMixin, ManageViewMixin, ElectionAdminView, CreateView
):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/dashboard/leo_contact_override_create.html"
    form_class = LeoContactOverrideManageCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["state"] = State.objects.get(code=self.kwargs["state"])
        context["region"] = Region.objects.get(pk=self.kwargs["pk"])
        return context

    def get_form_kwargs(self):
        return {
            "region_id": self.kwargs["pk"],
            "usvf_data": get_absentee_contact_info(
                self.kwargs["pk"], skip_overrides=True
            ),
            **super().get_form_kwargs(),
        }

    def get_success_url(self):
        return reverse(
            "manage:absentee_dashboard:leo_contact_override_detail",
            args=[self.kwargs["state"], self.object.pk],
        )
