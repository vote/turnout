from django.views.generic import DetailView, ListView

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from multi_tenant.mixins_manage_views import (
    SubscriberDataViewMixin,
    SubscriberGenericViewMixin,
)

from .models import Lookup


class LookupListView(
    SubscriberGenericViewMixin, SubscriberDataViewMixin, ActionListViewMixin, ListView,
):
    model = Lookup
    context_object_name = "lookups"
    template_name = "verifier/manage/lookup_list.html"


class LookupDetailView(
    SubscriberGenericViewMixin, SubscriberDataViewMixin, UUIDSlugMixin, DetailView,
):
    model = Lookup
    context_object_name = "lookup"
    template_name = "verifier/manage/lookup_detail.html"
    slug_field = "uuid"
