from django.views.generic import DetailView, ListView

from action.mixin_manage_views import ActionListViewMixin
from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin

from .models import Registration


class RegistrationListView(ActionListViewMixin, ManageViewMixin, ListView):
    model = Registration
    context_object_name = "registrations"
    template_name = "register/manage/registration_list.html"


class RegistrationDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = Registration
    context_object_name = "registration"
    template_name = "register/manage/registration_detail.html"
    slug_field = "uuid"
