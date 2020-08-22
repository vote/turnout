import logging

import gevent
from django.conf import settings
from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common import enums
from common.analytics import statsd
from common.enums import EventType
from election.models import State
from integration.tasks import sync_lookup_to_actionnetwork
from smsbot.tasks import send_welcome_sms
from voter.tasks import voter_lookup_action

from .alloy import query_alloy
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

        alloy = gevent.spawn(query_alloy, serializer.validated_data)
        targetsmart = gevent.spawn(query_targetsmart, serializer.validated_data)
        gevent.joinall([alloy, targetsmart])

        serializer.validated_data["targetsmart_response"] = targetsmart.value
        serializer.validated_data["alloy_response"] = alloy.value

        if alloy.value.get("error"):
            statsd.increment("turnout.verifier.alloy_error")
            logger.error(f"Alloy Error {alloy.value['error']}")

        if targetsmart.value.get("error"):
            statsd.increment("turnout.verifier.ts_error")
            logger.error(f"Targetsmart Error {targetsmart.value['error']}")

        if targetsmart.value.get("error") and alloy.value.get("error"):
            return Response(
                {"error": "Error from data providers"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        alloy_record = alloy.value.get("data", {})
        if len(targetsmart.value.get("result_set", [])) == 1:
            targetsmart_record = targetsmart.value.get("result_set")[0]
        else:
            targetsmart_record = {}

        targetsmart_status = enums.VoterStatus.UNKNOWN
        if targetsmart_record.get("vb.vf_voter_status") == "Inactive":
            targetsmart_status = enums.VoterStatus.INACTIVE
        elif targetsmart_record.get("vb.vf_voter_status") == "Active":
            targetsmart_status = enums.VoterStatus.ACTIVE

        alloy_status = enums.VoterStatus.UNKNOWN
        if alloy_record.get("registration_status") == "Inactive":
            alloy_status = enums.VoterStatus.INACTIVE
        elif alloy_record.get("registration_status") == "Active":
            alloy_status = enums.VoterStatus.ACTIVE

        registered = False
        final_status = enums.VoterStatus.UNKNOWN
        if (
            alloy_status == enums.VoterStatus.INACTIVE
            or targetsmart_status == enums.VoterStatus.INACTIVE
        ):
            final_status = enums.VoterStatus.INACTIVE
        elif (
            alloy_status == enums.VoterStatus.ACTIVE
            or targetsmart_status == enums.VoterStatus.ACTIVE
        ):
            final_status = enums.VoterStatus.ACTIVE
            registered = True

        serializer.validated_data["targetsmart_status"] = targetsmart_status
        serializer.validated_data["alloy_status"] = alloy_status
        serializer.validated_data["voter_status"] = final_status
        serializer.validated_data["registered"] = registered

        if alloy_status != targetsmart_status:
            statsd.increment(
                "turnout.verifier.vendor_mismatch", tags=[f"state:{state_code}"]
            )

        serializer.validated_data["state"] = State.objects.get(code=state_code)

        instance = serializer.save()
        instance.action.track_event(EventType.FINISH)

        if settings.SMS_POST_SIGNUP_ALERT:
            send_welcome_sms.apply_async(
                args=(str(instance.phone), "verifier"),
                countdown=settings.SMS_OPTIN_REMINDER_DELAY,
            )

        if settings.ACTIONNETWORK_SYNC:
            sync_lookup_to_actionnetwork.delay(instance.uuid)
        voter_lookup_action.delay(instance.action.uuid)

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
