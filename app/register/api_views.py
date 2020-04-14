from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import GenericViewSet

from action.mixin_apiview import IncompleteActionViewSet
from common.enums import TurnoutActionStatus

from .models import Registration
from .serializers import RegistrationSerializer, StatusSerializer
from .tasks import process_registration_submission


class RegistrationViewSet(IncompleteActionViewSet):
    model = Registration
    serializer_class = RegistrationSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
    task = process_registration_submission


class StatusViewSet(UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Registration
    serializer_class = StatusSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
