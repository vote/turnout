from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import SubscriberSlug


class SubscriberSlugViewSet(GenericViewSet):
    permission_classes = [AllowAny]
    model = SubscriberSlug
    queryset = SubscriberSlug.objects.select_related("subscriber")
    lookup_field = "slug"

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        subscriber = instance.subscriber

        return Response(
            {
                "name": subscriber.name,
                "url": subscriber.url,
                "terms_of_service": subscriber.terms_of_service,
                "privacy_policy": subscriber.privacy_policy,
                "has_data_access": subscriber.plan_has_data_access(),
                "sms_enabled": subscriber.sms_enabled == True
                if subscriber.plan_has_data_access()
                else False,
                "sms_checkbox_default": subscriber.sms_checkbox_default == True,
                "sms_disclaimer": subscriber.sms_disclaimer,
                "sms_checkbox": subscriber.sms_checkbox == True,
                "disclaimer": subscriber.disclaimer,
            }
        )
