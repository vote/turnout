from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from manage.mixins import ManageViewMixin

from .forms import ChangePartnerManageForm
from .mixins_manage_views import PartnerManageViewMixin


class EmbedCodeSampleView(PartnerManageViewMixin, ManageViewMixin, TemplateView):
    template_name = "multi_tenant/manage/embed.html"


class ChangePartnerView(ManageViewMixin, FormView):
    form_class = ChangePartnerManageForm
    template_name = "multi_tenant/manage/change_partner_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.multi_client_admin:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        form = super().get_form()
        # Explicitly set the choices by changing the queryset of the "partner"
        # field. Django will validate that the submission is inside of this
        # queryset.
        form.fields["partner"].queryset = self.request.user.allowed_clients
        return form

    def form_valid(self, form):
        new_client = form.cleaned_data["partner"]
        self.request.user.active_client = new_client
        self.request.user.save(update_fields=["active_client"])
        return HttpResponseRedirect(reverse("manage:home", args=[new_client.slug]))
