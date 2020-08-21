import logging

from django.conf import settings
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from action.mixin_apiview import IncompleteActionViewSet
from common.enums import (
    EventType,
    PoliticalParties,
    RegistrationGender,
    TurnoutActionStatus,
)
from integration.tasks import sync_registration_to_actionnetwork
from official.api_views import get_regions_for_address
from smsbot.tasks import send_welcome_sms
from voter.tasks import voter_lookup_action

from .custom_ovr_links import get_custom_ovr_link
from .generateform import process_registration
from .models import Registration
from .pa import pa_fill_region, process_pa_registration
from .serializers import RegistrationSerializer, StatusSerializer

logger = logging.getLogger("register")


class RegistrationViewSet(IncompleteActionViewSet):
    model = Registration
    serializer_class = RegistrationSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)

    def after_validate(self, serializer):
        if self.request.GET.get("match_region") == "true":
            address1 = serializer.validated_data.get("address1")
            city = serializer.validated_data.get("city")
            state = serializer.validated_data.get("state")
            zipcode = serializer.validated_data.get("zipcode")

            if address1 and city and state and zipcode:
                # everything was provided in this POST/PATCH
                regions, _ = get_regions_for_address(
                    street=address1, city=city, state=state.code, zipcode=zipcode,
                )
            else:
                # we need to load at least some of this from the db
                registration = self.get_object()
                regions, _ = get_regions_for_address(
                    street=address1 or registration.address1,
                    city=city or registration.city,
                    state=state.code if state else registration.state_id,
                    zipcode=zipcode or registration.zipcode,
                )

            if regions and len(regions) == 1:
                serializer.validated_data["matched_region"] = regions[0]

    def after_create_or_update(self, registration):
        if (
            registration.state_id == "PA"
            and registration.state_fields is not None
            and not registration.state_fields.get("region_id")
        ):
            pa_fill_region(registration)

    def complete(
        self,
        serializer,
        registration,
        state_id_number,
        state_id_number_2,
        is_18_or_over,
    ):
        if registration.state_id == "PA" and registration.state_fields:
            success = process_pa_registration(
                registration, state_id_number, state_id_number_2, is_18_or_over
            )
            registration.save()
            if not success:
                return
        else:
            registration.status = TurnoutActionStatus.PENDING
            registration.save()

            process_registration(registration, state_id_number, is_18_or_over)

        # common reg completion path
        if settings.SMS_POST_SIGNUP_ALERT:
            send_welcome_sms.apply_async(
                args=(str(registration.phone), "register"),
                countdown=settings.SMS_OPTIN_REMINDER_DELAY,
            )

        if settings.ACTIONNETWORK_SYNC:
            sync_registration_to_actionnetwork.delay(registration.uuid)
        voter_lookup_action(registration.action.uuid)

    def after_create(self, action_object):
        custom_link = get_custom_ovr_link(action_object)

        if custom_link:
            action_object.custom_ovr_link = custom_link
            action_object.save(update_fields=["custom_ovr_link"])

        if settings.SMS_POST_SIGNUP_ALERT:
            send_welcome_sms.apply_async(
                args=(str(action_object.phone), "register"),
                countdown=settings.SMS_OPTIN_REMINDER_DELAY,
            )

    def create_or_update_response(self, action_object):
        response = {
            "uuid": action_object.uuid,
            "action_id": action_object.action.pk,
            "custom_ovr_link": action_object.custom_ovr_link,
        }
        if action_object.state_api_result:
            if "status" in action_object.state_api_result:
                response["state_api_status"] = action_object.state_api_result.get(
                    "status"
                )
                response["state_api_error"] = action_object.state_api_result.get(
                    "error"
                )
            if "regions" in action_object.state_api_result:
                response["state_api_regions"] = action_object.state_api_result.get(
                    "regions"
                )

        if self.request.GET.get("match_region") == "true":
            regions = action_object.state.region_set.exclude(hidden=True)

            response["regions"] = regions.order_by("name").values("name", "external_id")

            response["matched_region"] = (
                action_object.matched_region.pk
                if action_object.matched_region
                else None
            )

        return Response(response)


class StatusViewSet(UpdateModelMixin, GenericViewSet):
    permission_classes = [AllowAny]
    model = Registration
    serializer_class = StatusSerializer
    queryset = Registration.objects.filter(status=TurnoutActionStatus.INCOMPLETE)
