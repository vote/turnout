from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from action.mixin_apiview import IncompleteActionViewSet
from common.enums import TurnoutActionStatus

from .custom_ovr_links import get_custom_ovr_link
from .models import Registration
from .serializers import RegistrationSerializer, StatusSerializer
from .tasks import process_registration_submission


class RegistrationViewSet(IncompleteActionViewSet):
    model = Registration
    serializer_class = RegistrationSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
    task = process_registration_submission

    def after_create(self, action_object):
        custom_link = get_custom_ovr_link(action_object)

        if custom_link:
            action_object.custom_ovr_link = custom_link
            action_object.save(update_fields=["custom_ovr_link"])

    def create_or_update_response(self, request, action_object):
        response = {
            "uuid": action_object.uuid,
            "action_id": action_object.action.pk,
            "custom_ovr_link": action_object.custom_ovr_link,
        }
        return Response(response)


class StatusViewSet(UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Registration
    serializer_class = StatusSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
