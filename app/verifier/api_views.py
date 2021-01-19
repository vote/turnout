import logging

from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from action.tasks import action_finish
from common import enums
from common.analytics import statsd
from common.enums import EventType
from election.models import State

from .models import Lookup
from .serializers import LookupSerializer
from .targetsmart import query_targetsmart

logger = logging.getLogger("verifier")


class LookupViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Lookup
    serializer_class = LookupSerializer
    queryset = Lookup.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        state_code = serializer.validated_data["state"]

        targetsmart = query_targetsmart(serializer.validated_data)

        serializer.validated_data["targetsmart_response"] = targetsmart

        if targetsmart.get("error"):
            statsd.increment("turnout.verifier.ts_error")
            logger.error(f"Targetsmart Error {targetsmart['error']}")

            return Response(
                {"error": "Error from data providers"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if len(targetsmart.get("result_set", [])) == 1:
            targetsmart_record = targetsmart.get("result_set")[0]
        else:
            targetsmart_record = {}

        registered = False
        targetsmart_status = enums.VoterStatus.UNKNOWN
        if targetsmart_record.get("vb.vf_voter_status") == "Inactive":
            targetsmart_status = enums.VoterStatus.INACTIVE
        elif targetsmart_record.get("vb.vf_voter_status") == "Active":
            targetsmart_status = enums.VoterStatus.ACTIVE
            registered = True

        serializer.validated_data["targetsmart_status"] = targetsmart_status
        serializer.validated_data["voter_status"] = targetsmart_status
        serializer.validated_data["registered"] = registered

        serializer.validated_data["state"] = State.objects.get(code=state_code)

        instance = serializer.save()
        instance.action.track_event(EventType.FINISH)

        action_finish.delay(instance.action.pk)

        response = {"registered": registered, "action_id": instance.action.pk}

        if registered:
            statsd.increment(
                "turnout.verifier.registered", tags=[f"state:{state_code}"]
            )
        else:
            statsd.increment(
                "turnout.verifier.unregistered", tags=[f"state:{state_code}"]
            )

        return Response(response)
