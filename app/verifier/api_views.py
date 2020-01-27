from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from election.models import State

from .models import Lookup
from .serializers import LookupSerializer
from .targetsmart import query_targetsmart


class LookupViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Lookup
    serializer_class = LookupSerializer
    queryset = Lookup.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query_targetsmart(serializer.validated_data)

        # set the state to a real model from the code
        serializer.validated_data["state"] = State.objects.get(
            code=serializer.validated_data["state"]
        )

        serializer.validated_data["response"] = {}
        serializer.validated_data["registered"] = False
        serializer.validated_data["too_many"] = False

        self.perform_create(serializer)

        response = {"registered": False}

        return Response(response)
