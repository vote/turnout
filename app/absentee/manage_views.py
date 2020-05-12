from django.views.generic import DetailView, ListView

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin
from multi_tenant.mixins_manage_views import PartnerGenericViewMixin

from .models import BallotRequest


class BallotRequestListView(
    PartnerGenericViewMixin, ActionListViewMixin, ManageViewMixin, ListView
):
    model = BallotRequest
    context_object_name = "ballot_requests"
    template_name = "absentee/manage/ballot_request_list.html"


class BallotRequestDetailView(
    PartnerGenericViewMixin, UUIDSlugMixin, ManageViewMixin, DetailView
):
    model = BallotRequest
    context_object_name = "ballot_request"
    template_name = "absentee/manage/ballot_request_detail.html"
    slug_field = "uuid"
