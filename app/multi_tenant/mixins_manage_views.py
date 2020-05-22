from multi_tenant.models import Client


class PartnerGenericViewMixin:
    def dispatch(self, request, *args, **kwargs):
        self.partner = Client.objects.get(default_slug__slug=kwargs["partner"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(partner=self.partner)
