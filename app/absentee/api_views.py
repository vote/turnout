from typing import Any, Dict

from django.http import Http404
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from action.mixin_apiview import IncompleteActionViewSet
from common.enums import SubmissionType, TurnoutActionStatus
from official.api_views import get_regions_for_address

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest
from .serializers import BallotRequestSerializer
from .state_pdf_data import STATE_DATA
from .tasks import process_ballotrequest_submission


def get_esign_method(ballot_request: BallotRequest):
    state_submission_method = ballot_request.state.vbm_submission_type
    if state_submission_method == SubmissionType.SELF_PRINT:
        return SubmissionType.SELF_PRINT

    # Check that we have the right contact info for fax/email
    contact_info = get_absentee_contact_info(ballot_request.region.external_id)

    if state_submission_method == SubmissionType.LEO_FAX and not contact_info.fax:
        return SubmissionType.SELF_PRINT
    if state_submission_method == SubmissionType.LEO_EMAIL and not contact_info.email:
        return SubmissionType.SELF_PRINT

    return state_submission_method


def populate_esign_method(ballot_request: BallotRequest):
    if ballot_request.region and not ballot_request.esign_method:
        ballot_request.esign_method = get_esign_method(ballot_request)
        ballot_request.save(update_fields=["esign_method"])


class BallotRequestViewSet(IncompleteActionViewSet):
    model = BallotRequest
    serializer_class = BallotRequestSerializer
    queryset = BallotRequest.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
    task = process_ballotrequest_submission

    def create(self, request, *args, **kwargs):
        incomplete = request.GET.get("incomplete") == "true"
        if not incomplete:
            return super().create(request, *args, **kwargs)

        serializer = self.get_serializer(data=request.data, incomplete=incomplete)
        serializer.is_valid(raise_exception=True)

        # For backwards-compatibility, we default to including the list of
        # regions in the state. If the user passes ?match_region=true, then
        # instead we attempt to determine the region from the address. If we're
        # successful, then we just set the region on the model and don't return
        # a list of regions. If we're unsuccessful, we return a (possibly filtered)
        # list of regions.
        include_regions = True
        include_specific_regions = None
        if request.GET.get("match_region") == "true":
            # Try to pick the correct region
            regions, _ = get_regions_for_address(
                street=f"{serializer.validated_data['address1']}",
                city=serializer.validated_data["city"],
                state=serializer.validated_data["state"],
                zipcode=serializer.validated_data["zipcode"],
            )

            if not regions or len(regions) == 0:
                # No region matching data -- user has to pick
                pass
            elif len(regions) > 1:
                # Inexact region match -- user has to pick but only from a
                # filtered list
                include_specific_regions = sorted(
                    [{"name": r.name, "external_id": r.external_id} for r in regions],
                    key=lambda r: r["name"],
                )
            else:
                # Exact region mach!
                serializer.validated_data["region"] = regions[0]
                include_regions = False

        ballot_request = self.process_serializer(serializer, is_create=True)

        # Based on the results of region mapping, attach a list of regions
        # to the response
        extra_response_data = {}
        if include_regions:
            if include_specific_regions:
                extra_response_data["regions"] = include_specific_regions
            else:
                absentee_regions = ballot_request.state.region_set

                if ballot_request.state.code in ["MI", "WI"]:
                    # MI and WI process absentee ballots only at the municipality level
                    absentee_regions = absentee_regions.exclude(
                        municipality__isnull=True
                    )

                extra_response_data["regions"] = absentee_regions.order_by(
                    "name"
                ).values("name", "external_id")

        return self.create_or_update_response(
            request, ballot_request, extra_response_data
        )

    def after_create_or_update(self, ballot_request: BallotRequest):
        populate_esign_method(ballot_request)

    def create_or_update_response(
        self,
        request: Request,
        ballot_request: BallotRequest,
        extra_response_data: Dict[str, Any] = {},
    ) -> Response:

        response = {
            "uuid": ballot_request.uuid,
            "action_id": ballot_request.action.pk,
            "region": ballot_request.region.pk if ballot_request.region else None,
            "esign_method": ballot_request.esign_method.value
            if ballot_request.esign_method
            else None,
        }

        response.update(extra_response_data)

        return Response(response)


class StateMetadataView(APIView):
    def get(self, request, state_code):
        state_data = STATE_DATA.get(state_code)
        if state_data is None:
            raise Http404

        return Response(
            {k: state_data.get(k) for k in ("signature_statement", "form_fields")}
        )
