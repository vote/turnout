from django.views.generic import DetailView, ListView

from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin

from .models import Lookup


class LookupListView(ManageViewMixin, ListView):
    model = Lookup
    context_object_name = "lookups"
    template_name = "verifier/manage/lookup_list.html"
    paginate_by = 25


class LookupDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = Lookup
    context_object_name = "lookup"
    template_name = "verifier/manage/lookup_detail.html"
    slug_field = "uuid"
