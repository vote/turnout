from django.http import Http404
from django.shortcuts import get_object_or_404

from manage.mixins import ManageViewMixin
from multi_tenant.models import Client


class SubscriberManageViewMixin(ManageViewMixin):
    def check_subscriber_access(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.subscriber = get_object_or_404(
            Client, default_slug__slug=kwargs["subscriber"]
        )
        if request.user.is_authenticated and (
            self.subscriber != request.user.active_client
            or self.subscriber not in request.user.allowed_clients
        ):
            raise Http404

        self.check_subscriber_access()

        return super().dispatch(request, *args, **kwargs)


class SubscriberGenericViewMixin:
    def get_queryset(self):
        return super().get_queryset().filter(subscriber=self.subscriber)
