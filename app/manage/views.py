from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import FormView, TemplateView
from two_factor.views import LoginView as TFLoginView

from multi_tenant.forms import ChangeSubscriberManageForm
from multi_tenant.mixins_manage_views import SubscriberManageViewMixin

from .forms import AuthenticationForm
from .mixins import ManageViewMixin


class LoginView(TFLoginView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["stats"] = self.subscriber.stats
        context["by_state"] = sorted(self.subscriber.stats.get("by_state", {}).items())
        return context


class RedirectToSubscriberManageView(LoginRequiredMixin, FormView):
    form_class = ChangeSubscriberManageForm
    template_name = "management/manage_nosubscriber.html"

    def dispatch(self, request, *args, **kwargs):
        # only add special behavior if authenticated
        if request.user.is_authenticated:
            # If the user is not authorized with 2 factor, send them there
            if not request.user.is_verified():
                return HttpResponseRedirect(reverse("two_factor:profile"))

            # If the user has an "active client" (nearly all will) redirect to that dashboard
            if request.user.active_client:
                return HttpResponseRedirect(
                    reverse("manage:home", args=[self.request.user.active_client_slug])
                )

        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form = super().get_form()
        # Explicitly set the choices by changing the queryset of the "subscriber"
        # field. Django will validate that the submission is inside of this
        # queryset.
        form.fields["subscriber"].queryset = self.request.user.allowed_clients
        return form

    def form_valid(self, form):
        new_client = form.cleaned_data["subscriber"]
        self.request.user.active_client = new_client
        self.request.user.save(update_fields=["active_client"])
        return HttpResponseRedirect(reverse("manage:home", args=[new_client.slug]))
