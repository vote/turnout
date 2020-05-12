from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, RedirectView

from manage.mixins import ManageViewMixin
from multi_tenant.models import Client


class ChangePartnerListView(ManageViewMixin, ListView):
    model = Client
    queryset = Client.objects.select_related("default_slug").order_by("name")
    context_object_name = "partners"
    template_name = "multi_tenant/manage/change_partner_list.html"


class ChangePartnerView(ManageViewMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        client = get_object_or_404(
            Client, default_slug__slug=self.kwargs["partner_slug"]
        )
        self.request.user.active_client = client
        self.request.user.save(update_fields=["active_client"])
        return reverse("manage:home", args=[client.slug])
