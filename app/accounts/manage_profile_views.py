from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView

from manage.mixins import ManageViewMixin

from .forms import UpdateProfileForm
from .models import User


class UpdateProfileView(SuccessMessageMixin, ManageViewMixin, UpdateView):
    model = User
    form_class = UpdateProfileForm
    template_name = "accounts/manage/edit_profile.html"
    success_url = reverse_lazy("manage:home_redirect")
    success_message = "Your profile has been updated."

    def get_object(self):
        return self.request.user


class UpdatePasswordView(SuccessMessageMixin, ManageViewMixin, FormView):
    model = User
    form_class = PasswordChangeForm
    template_name = "accounts/manage/change_password.html"
    success_url = reverse_lazy("manage:home_redirect")
    success_message = "Your password has been updated."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
