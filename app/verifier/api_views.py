import logging

from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common import enums
from common.analytics import statsd
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

    @statsd.timed("turnout.verifier.request")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

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
            if targetsmart_record["vb.voterbase_registration_status"] == "Registered":
                registered = True

            if targetsmart_record["vb.vf_voter_status"] == "Active":
                serializer.validated_data["voter_status"] = enums.VoterStatus.ACTIVE
            elif targetsmart_record["vb.vf_voter_status"] == "Inactive":
                serializer.validated_data["voter_status"] = enums.VoterStatus.INACTIVE
            else:
                serializer.validated_data["voter_status"] = enums.VoterStatus.UNKNOWN

            statsd.increment("turnout.verifier.singleresult")

        serializer.validated_data["too_many"] = targetsmart_response["too_many"]
        serializer.validated_data["registered"] = registered

        self.perform_create(serializer)

        response = {"registered": registered}

        if targetsmart_response["too_many"]:
            statsd.increment("turnout.verifier.toomany")

        if registered:
            statsd.increment("turnout.verifier.registered")

        return Response(response)
