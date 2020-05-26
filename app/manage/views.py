from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.urls import reverse, reverse_lazy
from django.views.generic import RedirectView, TemplateView

from multi_tenant.mixins_manage_views import SubscriberManageViewMixin

from .forms import AuthenticationForm
from .mixins import ManageViewMixin


class LoginView(DjangoLoginView):
    form_class = AuthenticationForm
    template_name = "management/auth/login.html"
    next_page = reverse_lazy("manage:home_redirect")
    redirect_authenticated_user = True

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or self.next_page


class LogoutView(DjangoLogoutView):
    template_name = "management/auth/logout.html"


class ManageView(SubscriberManageViewMixin, ManageViewMixin, TemplateView):
    template_name = "management/manage_home.html"


class RedirectToSubscriberManageView(ManageViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse("manage:home", args=[self.request.user.active_client_slug])
