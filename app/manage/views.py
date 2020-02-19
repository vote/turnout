from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .forms import AuthenticationForm
from .mixins import ManageViewMixin


class LoginView(DjangoLoginView):
    form_class = AuthenticationForm
    template_name = "management/auth/login.html"
    next_page = reverse_lazy("manage:home")
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or self.next_page


class LogoutView(DjangoLogoutView):
    template_name = "management/auth/logout.html"


class ManageView(ManageViewMixin, TemplateView):
    template_name = "management/manage_home.html"
