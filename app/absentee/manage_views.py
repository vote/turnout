from django.views.generic import DetailView, ListView

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin

from .models import BallotRequest


class BallotRequestListView(ActionListViewMixin, ManageViewMixin, ListView):
    model = BallotRequest
    context_object_name = "ballot_requests"
    template_name = "absentee/manage/ballot_request_list.html"


class BallotRequestDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = BallotRequest
    context_object_name = "ballot_request"
    template_name = "absentee/manage/ballot_request_detail.html"
    slug_field = "uuid"
