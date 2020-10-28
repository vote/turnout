import logging

from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common.rollouts import get_feature, get_feature_bool
from election.models import State
from official.match import get_region_for_address
from official.serializers import RegionDetailSerializer

from .models import PollingPlaceLookup
from .serializers import PollingPlaceLookupReportSerializer

logger = logging.getLogger("official")


class PollingPlaceLookupReportViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = PollingPlaceLookup
    serializer_class = PollingPlaceLookupReportSerializer
    queryset = PollingPlaceLookup.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        dnc_result = serializer.validated_data.get("source_result") or {}
        if not serializer.validated_data.get("source_status"):
            serializer.validated_data["source_status"] = dnc_result.get("data", {}).get(
                "status"
            )

        # extract address from geocod.io fields (embedded in dnc_result)
        addr = dnc_result.get("data", {}).get("home_address", {})
        state = addr.get("state")
        serializer.validated_data["address1"] = addr.get("address_line_1")
        serializer.validated_data["address2"] = addr.get("address_line_2")
        serializer.validated_data["city"] = addr.get("city")
        serializer.validated_data["zipcode"] = addr.get("zip")
        try:
            serializer.validated_data["state"] = State.objects.get(code=state)
        except State.DoesNotExist:
            pass

        # never store civic result
        serializer.validated_data["civic_result"] = None

        instance = serializer.save()

        response = {
            "action_id": instance.action.pk,
            "state_id": state,
        }

        # include region match, if any
        if (
            addr
            and get_feature("locator_region")
            and get_feature_bool("locator_region", state) != False
        ):
            region = get_region_for_address(
                addr.get("address_line_1"),
                addr.get("city"),
                state,
                addr.get("zip"),
                dnc_result.get("data", {}).get("county"),
            )
            if region:
                serializer = RegionDetailSerializer(region)
                response["region"] = serializer.data

        return Response(response)
