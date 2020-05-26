from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from reversion.views import RevisionMixin

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin

from .forms import (
    LeoContactOverrideManageCreateForm,
    LeoContactOverrideManageDeleteForm,
    LeoContactOverrideManageUpdateForm,
)
from .models import LeoContactOverride


class LeoContactOverrideListView(ActionListViewMixin, ManageViewMixin, ListView):
    model = LeoContactOverride
    context_object_name = "leo_contact_overrides"
    template_name = "absentee/manage/leo_contact_override_list.html"


class LeoContactOverrideDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/manage/leo_contact_override_detail.html"
    slug_field = "uuid"


class LeoContactOverrideUpdateView(RevisionMixin, ManageViewMixin, UpdateView):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/manage/leo_contact_override_update.html"
    form_class = LeoContactOverrideManageUpdateForm

    def get_success_url(self):
        return reverse(
            "manage:absentee_override:leo_contact_override_detail",
            args=[self.object.pk],
        )


class LeoContactOverrideDeleteView(RevisionMixin, ManageViewMixin, DeleteView):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/manage/leo_contact_override_delete.html"
    form_class = LeoContactOverrideManageDeleteForm

    def get_success_url(self):
        return reverse("manage:absentee_override:leo_contact_override_list",)


class LeoContactOverrideCreateView(RevisionMixin, ManageViewMixin, CreateView):
    model = LeoContactOverride
    context_object_name = "leo_contact_override"
    template_name = "absentee/manage/leo_contact_override_create.html"
    form_class = LeoContactOverrideManageCreateForm

    def get_success_url(self):
        return reverse(
            "manage:absentee_override:leo_contact_override_detail",
            args=[self.object.pk],
        )
