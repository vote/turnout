from django.urls import reverse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from action.mixin_manage_views import ActionListViewMixin
from election.mixins_manage_views import ElectionAdminView
from manage.mixins import ManageViewMixin

from .forms import (
    RegionOVBMLinkManageCreateForm,
    RegionOVBMLinkManageDeleteForm,
    RegionOVBMLinkManageUpdateForm,
)
from .models import RegionOVBMLink


class RegionOVBMLinkListView(
    ActionListViewMixin, ManageViewMixin, ElectionAdminView, ListView
):
    model = RegionOVBMLink
    context_object_name = "region_ovbm_links"
    template_name = "absentee/manage/region_ovbm_link_list.html"

    def get_queryset(self):
        return RegionOVBMLink.objects.exclude(region__state__code="FL")


class RegionOVBMLinkUpdateView(ManageViewMixin, ElectionAdminView, UpdateView):
    model = RegionOVBMLink
    context_object_name = "region_ovbm_link"
    template_name = "absentee/manage/region_ovbm_link_update.html"
    form_class = RegionOVBMLinkManageUpdateForm

    def get_success_url(self):
        return reverse("manage:absentee_region_ovbm:region_ovbm_link_list")


class RegionOVBMLinkDeleteView(ManageViewMixin, ElectionAdminView, DeleteView):
    model = RegionOVBMLink
    context_object_name = "region_ovbm_link"
    template_name = "absentee/manage/region_ovbm_link_delete.html"
    form_class = RegionOVBMLinkManageDeleteForm

    def get_success_url(self):
        return reverse("manage:absentee_region_ovbm:region_ovbm_link_list")


class RegionOVBMLinkCreateView(ManageViewMixin, ElectionAdminView, CreateView):
    model = RegionOVBMLink
    context_object_name = "region_ovbm_link"
    template_name = "absentee/manage/region_ovbm_link_create.html"
    form_class = RegionOVBMLinkManageCreateForm

    def get_success_url(self):
        return reverse("manage:absentee_region_ovbm:region_ovbm_link_list")
