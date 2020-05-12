from django.views.generic import DetailView, ListView

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin
from multi_tenant.mixins_manage_views import PartnerGenericViewMixin

from .models import Lookup


class LookupListView(
    PartnerGenericViewMixin, ActionListViewMixin, ManageViewMixin, ListView
):
    model = Lookup
    context_object_name = "lookups"
    template_name = "verifier/manage/lookup_list.html"


class LookupDetailView(
    PartnerGenericViewMixin, UUIDSlugMixin, ManageViewMixin, DetailView
):
    model = Lookup
    context_object_name = "lookup"
    template_name = "verifier/manage/lookup_detail.html"
    slug_field = "uuid"
