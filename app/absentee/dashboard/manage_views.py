import os

from django.conf import settings
from django.db.models import Exists, OuterRef
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
from absentee.generateform import populate_storage_item
from absentee.mixins_manage_views import EsignAdminView
from absentee.models import (
    BallotRequest,
    LeoContactOverride,
    RegionEsignMethod,
    StateDashboardData,
)
from action.mixin_manage_views import ActionListViewMixin
from common import enums
from common.aws import s3_client
from common.rollouts import flag_enabled_for_state
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from election.choices import REGISTRATION_STATES
from election.models import State
from event_tracking.models import Event
from manage.mixins import ManageViewMixin
from official.models import Region
from storage.models import StorageItem

from .forms import (
    LeoContactOverrideManageCreateForm,
    LeoContactOverrideManageDeleteForm,
    LeoContactOverrideManageUpdateForm,
)


class EsignDashboardView(
    ActionListViewMixin, ManageViewMixin, EsignAdminView, ListView
):
    model = StateDashboardData
    context_object_name = "states"
    template_name = "absentee/dashboard/state_dashboard.html"

    def get_queryset(self):
        queryset = super().get_queryset()

        esign_states = [
            state_code
            for (state_code, state_name) in REGISTRATION_STATES
            if flag_enabled_for_state("vbm_esign", state_code)
        ]

        return queryset.filter(state_id__in=esign_states)


class EsignRegionDashboardView(ManageViewMixin, EsignAdminView, DetailView):
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


class LeoContactOverrideDetailView(
    UUIDSlugMixin, ManageViewMixin, EsignAdminView, DetailView
):
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
    RevisionMixin, ManageViewMixin, EsignAdminView, UpdateView
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
    RevisionMixin, ManageViewMixin, EsignAdminView, DeleteView
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
    RevisionMixin, ManageViewMixin, EsignAdminView, CreateView
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


class BallotRequestListView(
    EsignAdminView, ActionListViewMixin, ListView,
):
    model = BallotRequest
    context_object_name = "ballot_requests"
    template_name = "absentee/dashboard/ballot_request_list.html"

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                is_esign=Exists(
                    Event.objects.filter(
                        action_id=OuterRef("action_id"),
                        event_type__in=(
                            enums.EventType.FINISH_LEO,
                            enums.EventType.FINISH_LEO_FAX_PENDING,
                        ),
                    )
                )
            )
            .filter(is_esign=True)
        )

        search_query = self.request.GET.get("q")
        if search_query:
            queryset = queryset.filter(search=search_query)

        region_filter = self.request.GET.get("region")
        if region_filter:
            queryset = queryset.filter(region_id=int(region_filter))

        return queryset.select_related("state")


class BallotRequestDetailView(
    EsignAdminView, UUIDSlugMixin, DetailView,
):
    model = BallotRequest
    context_object_name = "ballot_request"
    template_name = "absentee/dashboard/ballot_request_detail.html"
    slug_field = "uuid"

    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ballot_request = context["ballot_request"]
        if (
            ballot_request.signature
            and ballot_request.result_item
            and not ballot_request.signature.purged
        ):
            storage_item, created = StorageItem.objects.get_or_create(
                preview_of=ballot_request.result_item,
                defaults={"app": ballot_request.result_item.app},
            )

            if created or not storage_item.file.storage.exists(storage_item.file.name):
                # Copy created_at so the preview gets purged with the original
                storage_item.created_at = ballot_request.result_item.created_at
                storage_item.save()

                populate_storage_item(storage_item, ballot_request, "XXXX", True)

                # Override content-disposition and content-type so the browser doesn't try to download it
                bucket_name = settings.AWS_STORAGE_PRIVATE_BUCKET_NAME  # type:ignore
                object_name = os.path.join(
                    storage_item.file.storage.location, storage_item.file.name
                )
                s3_client.copy_object(
                    Bucket=bucket_name,
                    Key=object_name,
                    ContentDisposition="inline",
                    ContentType="application/pdf",
                    MetadataDirective="REPLACE",
                    CopySource={"Bucket": bucket_name, "Key": object_name},
                )

            context["preview_pdf_url"] = storage_item.get_absolute_url()

        return context
