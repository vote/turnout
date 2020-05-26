from django.http import Http404
from rest_framework.response import Response
from rest_framework.views import APIView

from action.mixin_apiview import IncompleteActionViewSet
from common.enums import TurnoutActionStatus

from .models import BallotRequest
from .serializers import BallotRequestSerializer
from .state_pdf_data import STATE_DATA
from .tasks import process_ballotrequest_submission


class BallotRequestViewSet(IncompleteActionViewSet):
    model = BallotRequest
    serializer_class = BallotRequestSerializer
    queryset = BallotRequest.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
    task = process_ballotrequest_submission

    def create(self, request, *args, **kwargs) -> Response:
        incomplete = request.GET.get("incomplete") == "true"
        if not incomplete:
            return super().create(request, *args, **kwargs)

        # Logic for incomplete requests
        ballot_request = self.process_serializer(
            self.get_serializer(data=request.data, incomplete=True)
        )
        absentee_regions = ballot_request.state.region_set
        if ballot_request.state.code in ["MI", "WI"]:
            # MI and WI process absentee ballots only at the municipality level
            absentee_regions = absentee_regions.exclude(municipality__isnull=True)

        response = {
            "uuid": ballot_request.uuid,
            "action_id": ballot_request.action.pk,
            "regions": absentee_regions.order_by("name").values("name", "external_id"),
        }
        return Response(response)


class StateMetadataView(APIView):
    def get(self, request, state_code):
        state_data = STATE_DATA.get(state_code)
        if state_data is None:
            raise Http404

        return Response(
            {k: state_data.get(k) for k in ("signature_statement", "form_fields")}
        )
