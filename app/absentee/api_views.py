import logging
from typing import Any, Dict

import sentry_sdk
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from lob.error import LobError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from action.mixin_apiview import IncompleteActionViewSet
from action.tasks import action_check_unfinished, action_finish
from common.enums import SubmissionType, TurnoutActionStatus
from common.rollouts import flag_enabled_for_state
from election.models import State, StateInformation
from integration.lob import check_deliverable, generate_lob_token, send_letter
from official.api_views import get_regions_for_address
from official.models import Region

from .contactinfo import get_absentee_contact_info
from .generateform import process_ballot_request
from .models import BallotRequest
from .region_links import ovbm_link_for_ballot_request
from .serializers import BallotRequestSerializer
from .state_pdf_data import STATE_DATA

logger = logging.getLogger("absentee")


def get_esign_method_for_region(state: State, region: Region) -> SubmissionType:
    if not flag_enabled_for_state("vbm_esign", state.code):
        return SubmissionType.SELF_PRINT

    # Construct a list of submission options in order of preference
    contact_info = get_absentee_contact_info(region.external_id)

    submission_options = [SubmissionType.LEO_EMAIL, SubmissionType.LEO_FAX]
    if contact_info.submission_method_override:
        if contact_info.submission_method_override == SubmissionType.SELF_PRINT:
            # If we've overridden to self-print, always do that
            return SubmissionType.SELF_PRINT

        submission_options = [contact_info.submission_method_override]

    # From that prioritized list, select the first one that is legal in this
    # state, and that we have the contact info for
    state_infos = StateInformation.objects.select_related("field_type").filter(
        field_type__slug__in=("vbm_app_submission_email", "vbm_app_submission_fax"),
        state=state,
    )

    email_allowed_for_state = any(
        info.boolean_value()
        for info in state_infos
        if info.field_type.slug == "vbm_app_submission_email"
    )
    email_allowed_for_region = email_allowed_for_state and contact_info.email

    fax_allowed_for_state = any(
        info.boolean_value()
        for info in state_infos
        if info.field_type.slug == "vbm_app_submission_fax"
    )
    fax_allowed_for_region = fax_allowed_for_state and contact_info.fax

    for submission_option in submission_options:
        if submission_option == SubmissionType.SELF_PRINT:
            # always allowed
            return SubmissionType.SELF_PRINT
        elif (
            submission_option == SubmissionType.LEO_EMAIL
        ) and email_allowed_for_region:
            return SubmissionType.LEO_EMAIL
        elif (submission_option == SubmissionType.LEO_FAX) and fax_allowed_for_region:
            return SubmissionType.LEO_FAX

    return SubmissionType.SELF_PRINT


def get_esign_method(ballot_request: BallotRequest) -> SubmissionType:
    return get_esign_method_for_region(ballot_request.state, ballot_request.region)


def populate_esign_method(ballot_request: BallotRequest):
    if ballot_request.region and not ballot_request.esign_method:
        ballot_request.esign_method = get_esign_method(ballot_request)
        ballot_request.save(update_fields=["esign_method"])


class BallotRequestViewSet(IncompleteActionViewSet):
    tool = "absentee"
    model = BallotRequest
    serializer_class = BallotRequestSerializer
    queryset = BallotRequest.objects.all()

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
                absentee_regions = ballot_request.state.region_set.exclude(hidden=True)

                if ballot_request.state.code in ["MI", "WI"]:
                    # MI and WI process absentee ballots only at the municipality level
                    absentee_regions = absentee_regions.exclude(
                        municipality__isnull=True
                    )

                extra_response_data["regions"] = absentee_regions.order_by(
                    "name"
                ).values("name", "external_id")

        action_check_unfinished.apply_async(
            args=(str(ballot_request.action.pk),),
            countdown=settings.ACTION_CHECK_UNFINISHED_DELAY,
        )

        return self.create_or_update_response(ballot_request, extra_response_data)

    def after_create_or_update(self, ballot_request: BallotRequest):
        populate_esign_method(ballot_request)

        # only do this for print-and-forward for now!
        # check_deliverable("")
        # check_deliverable("mailing_")
        check_deliverable(self.request.data, ballot_request, "request_mailing_")

    def create_or_update_response(
        self, ballot_request: BallotRequest, extra_response_data: Dict[str, Any] = {},
    ) -> Response:

        response = {
            "uuid": ballot_request.uuid,
            "action_id": ballot_request.action.pk,
            "region": ballot_request.region.pk if ballot_request.region else None,
            "esign_method": ballot_request.esign_method.value
            if ballot_request.esign_method
            else None,
            "allow_print_and_forward": ballot_request.state.allow_print_and_forward,
            "ovbm_link": ovbm_link_for_ballot_request(ballot_request),
            #            "deliverable": ballot_request.deliverable,
            #            "mailing_deliverable": ballot_request.mailing_deliverable,
            "request_mailing_deliverable": ballot_request.request_mailing_deliverable,
        }

        response.update(extra_response_data)

        if (
            ballot_request.request_mailing_address1
            and not ballot_request.request_mailing_deliverable
            and not self.request.data.get("ignore_undeliverable")
        ):
            return Response(
                {
                    "request_mailing_address1": "Address does not appear to be deliverable by USPS",
                    "request_mailing_deliverable_not_ignored": True,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(response)

    def complete(
        self,
        serializer,
        action_object,
        state_id_number,
        state_id_number_2,
        is_18_or_over,
        ignore_undeliverable,
    ):
        if (
            action_object.request_mailing_address1
            and not action_object.request_mailing_deliverable
            and not ignore_undeliverable
        ):
            # do not complete since they did not ignore_undeliverable
            return

        # NOTE: we drop state_id_number_2 on the floor here since only register needs it, and it overrides
        # this method.
        serializer.validated_data["status"] = TurnoutActionStatus.PENDING
        action_object.save()

        self.after_complete(action_object, state_id_number, is_18_or_over)

    def after_complete(self, action_object, state_id_number, is_18_or_over):
        process_ballot_request(action_object, state_id_number, is_18_or_over)
        action_finish.delay(action_object.action.pk)


class StateMetadataView(APIView):
    def get(self, request, state_code):
        state_data = STATE_DATA.get(state_code)
        if state_data is None:
            raise Http404

        return Response(
            {k: state_data.get(k) for k in ("signature_statement", "form_fields")}
        )


@api_view(["PUT"])
@permission_classes([AllowAny])
def lob_confirm(request, uuid):
    try:
        ballot_request = BallotRequest.objects.get(action_id=uuid)
    except ObjectDoesNotExist:
        raise Http404
    if generate_lob_token(ballot_request) != request.GET.get("token", ""):
        raise Http404

    try:
        send_date = send_letter(ballot_request)
        return Response({"send_date": send_date.isoformat()})
    except LobError as e:
        sentry_sdk.capture_exception(e)
        return Response(
            {"lob_error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
