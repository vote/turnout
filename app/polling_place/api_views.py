from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from election.models import State

from .models import PollingPlaceLookup
from .serializers import PollingPlaceLookupReportSerializer


class PollingPlaceLookupReportViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = PollingPlaceLookup
    serializer_class = PollingPlaceLookupReportSerializer
    queryset = PollingPlaceLookup.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.validated_data["dnc_status"] = request.data.get(
            "dnc_result", {}
        ).get("status")

        # extract address from geocod.io fields (embedded in dnc_result)
        addr = request.data.get("dnc_result", {}).get("home_address", {})
        serializer.validated_data["address1"] = addr.get("address_line_1")
        serializer.validated_data["address2"] = addr.get("address_line_2")
        serializer.validated_data["city"] = addr.get("city")
        serializer.validated_data["zipcode"] = addr.get("zip")
        try:
            serializer.validated_data["state"] = State.objects.get(
                code=addr.get("state")
            )
        except State.DoesNotExist:
            pass

        instance = serializer.save()

        response = {"action_id": instance.action.pk}

        return Response(response)
