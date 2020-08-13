import logging

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

from .alloy import ALLOY_STATES_ENABLED, query_alloy
from .models import Lookup
from .serializers import LookupSerializer
from .targetsmart import query_targetsmart

logger = logging.getLogger("verifier")


class LookupViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Lookup
    serializer_class = LookupSerializer
    queryset = Lookup.objects.none()

    @statsd.timed("turnout.verifier.request")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # check alloy states first
        if serializer.validated_data["state"] in ALLOY_STATES_ENABLED:
            alloy_response = query_alloy(serializer.validated_data)

            if alloy_response.get("error"):
                statsd.increment("turnout.verifier.alloy_error")
                alloy_error_message = alloy_response.get("error")

                logger.error(f"Alloy Error {alloy_error_message}")
                return Response(
                    {"error": "Error from data provider"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # set the state to a real model from the code
            serializer.validated_data["state"] = State.objects.get(
                code=serializer.validated_data["state"]
            )

            serializer.validated_data["response"] = alloy_response
            serializer.validated_data["last_updated"] = alloy_response.get(
                "data", {}
            ).get("last_updated_date")

            registered = False

            if alloy_response["data"]:
                alloy_record = alloy_response["data"]
                if alloy_record["registration_status"] == "Active":
                    serializer.validated_data["voter_status"] = enums.VoterStatus.ACTIVE
                    registered = True
                elif alloy_record["registration_status"] == "Inactive":
                    serializer.validated_data[
                        "voter_status"
                    ] = enums.VoterStatus.INACTIVE
                else:
                    serializer.validated_data[
                        "voter_status"
                    ] = enums.VoterStatus.UNKNOWN

                statsd.increment("turnout.verifier.singleresult")
                # alloy only returns single results

        else:
            # then hit targetsmart
            targetsmart_response = query_targetsmart(serializer.validated_data)

            if targetsmart_response.get("error"):
                statsd.increment("turnout.verifier.ts_error")
                logger.error(f"Targetsmart Error {targetsmart_response['error']}")
                return Response(
                    {"error": "Error from data provider"},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            # set the state to a real model from the code
            serializer.validated_data["state"] = State.objects.get(
                code=serializer.validated_data["state"]
            )

            serializer.validated_data["response"] = targetsmart_response

            registered = False

            if targetsmart_response["result"]:
                # if result is true, there is a single matching record
                targetsmart_record = targetsmart_response["result_set"][0]
                if targetsmart_record["vb.vf_voter_status"] == "Active":
                    serializer.validated_data["voter_status"] = enums.VoterStatus.ACTIVE
                    registered = True
                elif targetsmart_record["vb.vf_voter_status"] == "Inactive":
                    serializer.validated_data[
                        "voter_status"
                    ] = enums.VoterStatus.INACTIVE
                else:
                    serializer.validated_data[
                        "voter_status"
                    ] = enums.VoterStatus.UNKNOWN

                statsd.increment("turnout.verifier.singleresult")

            if targetsmart_response["too_many"]:
                statsd.increment("turnout.verifier.toomany")
            serializer.validated_data["too_many"] = targetsmart_response["too_many"]

        serializer.validated_data["registered"] = registered

        instance = serializer.save()
        instance.action.track_event(EventType.FINISH)

        if settings.SMS_POST_SIGNUP_ALERT:
            send_welcome_sms.apply_async(
                args=(str(instance.phone), "verifier"),
                countdown=settings.SMS_OPTIN_REMINDER_DELAY,
            )

        if settings.ACTIONNETWORK_SYNC:
            sync_lookup_to_actionnetwork.delay(instance.uuid)

        response = {"registered": registered, "action_id": instance.action.pk}
        if serializer.validated_data.get("last_updated"):
            response["last_updated"] = serializer.validated_data["last_updated"]

        if registered:
            statsd.increment("turnout.verifier.registered")

        return Response(response)
