from django.http import Http404

from multi_tenant.models import Client


class PartnerManageViewMixin:
    def dispatch(self, request, *args, **kwargs):
        self.partner = Client.objects.get(default_slug__slug=kwargs["partner"])
        if (
            self.partner != request.user.active_client
            or self.partner not in request.user.allowed_clients
        ):
            raise Http404
        return super().dispatch(request, *args, **kwargs)


class PartnerGenericViewMixin:
    def get_queryset(self):
        return super().get_queryset().filter(partner=self.partner)
