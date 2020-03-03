from django.views.generic import ListView

from manage.mixins import ManageViewMixin

from .models import Registration


class RegistrationListView(ManageViewMixin, ListView):
    model = Registration
    context_object_name = "registrations"
    template_name = "register/manage/registration_list.html"
    paginate_by = 25
