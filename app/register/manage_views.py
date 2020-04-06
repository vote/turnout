from django.views.generic import DetailView, ListView

from common.utils.uuid_slug_mixin import UUIDSlugMixin
from manage.mixins import ManageViewMixin

from .models import Registration


class RegistrationListView(ManageViewMixin, ListView):
    model = Registration
    context_object_name = "registrations"
    template_name = "register/manage/registration_list.html"
    paginate_by = 25


class RegistrationDetailView(UUIDSlugMixin, ManageViewMixin, DetailView):
    model = Registration
    context_object_name = "registration"
    template_name = "register/manage/registration_detail.html"
    slug_field = "uuid"
