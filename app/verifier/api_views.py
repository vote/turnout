from rest_framework import status
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common import enums
from election.models import State

from .catalist import query_catalist
from .models import Lookup
from .serializers import LookupSerializer


class LookupViewSet(CreateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Lookup
    serializer_class = LookupSerializer
    queryset = Lookup.objects.none()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        catalist_response = query_catalist(serializer.validated_data)

        if "count" not in catalist_response:
            return Response(
                {"error": "Improper response from data provider"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        serializer.validated_data["response"] = catalist_response

        total_matches = catalist_response["count"]
        serializer.validated_data["total_matches"] = total_matches

        registered = None
        voter_status = None

        if total_matches == 1:
            catalist_status = catalist_response["mrPersons"][0]["voterstatus"]
            if catalist_status == "active":
                voter_status = enums.VoterStatus.ACTIVE
                registered = True
            elif catalist_status == "inactive":
                voter_status = enums.VoterStatus.INACTIVE
                registered = False
            elif catalist_status == "unregistered":
                voter_status = enums.VoterStatus.UNREGISTERED
                registered = False
            elif catalist_status == "multipleAppearances":
                voter_status = enums.VoterStatus.MULTIPLE_APPEARANCES
            elif catalist_status == "unmatchedMember":
                voter_status = enums.VoterStatus.UNMATCHED_MEMBER

        serializer.validated_data["voter_status"] = voter_status
        serializer.validated_data["registered"] = registered

        # set the state to a real model from the code
        serializer.validated_data["state"] = State.objects.get(
            code=serializer.validated_data["state"]
        )

        self.perform_create(serializer)

        # minimize personal data in response
        if total_matches > 1:
            response = {"error": "Multiple results found"}
        elif registered:
            response = {"registered": True}
        else:
            response = {"registered": False}

        return Response(response)
