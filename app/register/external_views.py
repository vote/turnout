from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.template.loader import render_to_string
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from action.tasks import action_check_unfinished
from apikey.auth import ApiKeyAuthentication, ApiKeyRequired
from apikey.crypto import make_action_jwt, verify_action_jwt
from common.enums import EventType, RegistrationFlowType
from election.choices import STATES
from election.models import StateInformation

from .custom_ovr_links import get_custom_ovr_link
from .models import Registration
from .serializers import ExternalRegistrationSerializer

MARKDOWN_TEMPLATE = "register/external/external_registration.md"
JWT_EXPIRATION = timedelta(minutes=settings.REGISTER_JWT_EXPIRATION_MINUTES)
STATE_CACHE_TIMEOUT = 5 * 60


@dataclass
class StateRegistrationData:
    instructions_markdown: str
    flow_type: RegistrationFlowType

    external_tool_ovr: Optional[str]
    registration_directions: Optional[str]
    id_requirements_ovr: Optional[str]
    registration_ovr_directions: Optional[str]


INELIGIBLE_STATES = {"ND", "NH", "WY"}

# TODO: cache this
def get_state_data(state_code: str) -> StateRegistrationData:
    state_infos = {}
    for info in StateInformation.objects.select_related("field_type").filter(
        field_type__slug__in=(
            "external_tool_ovr",
            "registration_directions",
            "id_requirements_ovr",
            "registration_ovr_directions",
        ),
        state_id=state_code,
    ):
        state_infos[info.field_type.slug] = info.text

    if state_infos["external_tool_ovr"]:
        flow_type = RegistrationFlowType.OVR_OR_PRINT
    elif state_code in INELIGIBLE_STATES:
        flow_type = RegistrationFlowType.INELIGIBLE
    else:
        flow_type = RegistrationFlowType.PRINT_ONLY

    state_name = next(
        state_name for state_id, state_name in STATES if state_id == state_code
    )

    context = {
        "state_infos": state_infos,
        "state_name": state_name,
        "flow_type": flow_type.value,
        "has_ovr_id_requirements": bool(state_infos["id_requirements_ovr"])
        and state_infos["id_requirements_ovr"].upper() != "N/A",
    }

    instructions_markdown = render_to_string(MARKDOWN_TEMPLATE, context)

    return StateRegistrationData(
        instructions_markdown=instructions_markdown, flow_type=flow_type, **state_infos
    )


def get_state_data_cached(state_code: str) -> StateRegistrationData:
    cache_key = f"register__external_views__get_state_data__{state_code}"
    cached_value = cache.get(cache_key)
    if cached_value:
        return cached_value

    data = get_state_data(state_code)
    cache.set(cache_key, data, STATE_CACHE_TIMEOUT)

    return data


def generate_response(registration: Registration) -> Dict[str, Any]:
    state_data = get_state_data_cached(registration.state_id)

    custom_ovr_link = get_custom_ovr_link(registration)
    ovr_link = custom_ovr_link or state_data.external_tool_ovr

    if state_data.flow_type == RegistrationFlowType.OVR_OR_PRINT:
        jwt, jwt_expiry = make_action_jwt(
            action_id=str(registration.action_id),
            action_type="registration",
            expiration=JWT_EXPIRATION,
        )
        buttons = [
            {
                "message_text": "Register online",
                "primary": True,
                "url": ovr_link,
                "event_tracking": {
                    "action": str(registration.action_id),
                    "event_type": "FinishExternal",
                },
            },
            {
                "message_text": "Register by mail",
                "primary": False,
                "url": f"{settings.REGISTER_RESUME_URL}?skip_ovr=true&token={jwt}",
                "url_expiry": jwt_expiry.isoformat(),
            },
        ]
    elif state_data.flow_type == RegistrationFlowType.PRINT_ONLY:
        jwt, jwt_expiry = make_action_jwt(
            action_id=str(registration.action_id),
            action_type="registration",
            expiration=JWT_EXPIRATION,
        )
        buttons = [
            {
                "message_text": "Register by mail",
                "primary": True,
                "url": f"{settings.REGISTER_RESUME_URL}?skip_ovr=true&token={jwt}",
                "url_expiry": jwt_expiry.isoformat(),
            }
        ]
    else:
        buttons = []

    return {"message_markdown": state_data.instructions_markdown, "buttons": buttons}


class ExternalRegistrationViewSet(CreateModelMixin, GenericViewSet):
    authentication_classes = [ApiKeyAuthentication]
    permission_classes = [ApiKeyRequired]

    model = Registration
    serializer_class = ExternalRegistrationSerializer
    queryset = Registration.objects

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        registration = serializer.save()

        action_check_unfinished.apply_async(
            args=(registration.action.pk,),
            countdown=settings.ACTION_CHECK_UNFINISHED_DELAY,
        )
        registration.action.track_event(EventType.START_ACTION_API)

        return Response(generate_response(registration), status=200)


class RegistrationResumeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        uuid = request.GET.get("uuid")
        if uuid:
            registration = Registration.objects.get(uuid=uuid)
        else:
            token = request.GET.get("token")
            if not token:
                return Response({"error": "No token or uuid given"}, status=400)

            action_id = verify_action_jwt(token, action_type="registration")
            if not action_id:
                return Response({"error": "Invalid token"}, status=400)

            registration = Registration.objects.select_related("state").get(
                action_id=action_id
            )

        return Response(
            {
                "uuid": registration.uuid,
                "state": registration.state_id,
                "action_id": registration.action_id,
                "custom_ovr_link": get_custom_ovr_link(registration),
                "allow_print_and_forward": registration.state.allow_print_and_forward
                if registration.state
                else None,
            },
            status=200,
        )
