from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from manage.mixins import ManageViewMixin

from .forms import ChangeSubscriberManageForm
from .mixins_manage_views import SubscriberManageViewMixin


class EmbedCodeSampleView(SubscriberManageViewMixin, ManageViewMixin, TemplateView):
    template_name = "multi_tenant/manage/embed.html"


class ChangeSubscriberView(ManageViewMixin, FormView):
    form_class = ChangeSubscriberManageForm
    template_name = "multi_tenant/manage/change_subscriber_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.multi_client_admin:
            raise Http404
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
