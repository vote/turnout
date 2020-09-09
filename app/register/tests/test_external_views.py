from base64 import b64encode
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlparse

import pytest
from model_bakery import baker
from rest_framework.test import APIClient

from common.enums import RegistrationFlowType, RegistrationGender, StateFieldFormats
from election.models import StateInformation, StateInformationFieldType
from register.external_views import (
    MARKDOWN_TEMPLATE,
    StateRegistrationData,
    generate_response,
    get_state_data,
    settings,
)
from register.models import Registration

MINIMAL_REGISTRATION = {
    "first_name": "John",
    "last_name": "Hancock",
    "date_of_birth": "1737-01-23",
    "email": "john@hancock.local",
    "address1": "30 Beacon Street",
    "city": "Boston",
    "state": "MA",
    "zipcode": "02108",
    "sms_opt_in": True,
}

MAXIMAL_REGISTRATION = {
    **MINIMAL_REGISTRATION,
    "title": "Mr",
    "suffix": "Jr.",
    "phone": "+16174567890",
    "sms_opt_in_subscriber": True,
}

REQUEST_ENDPOINT = "/v1/registration/external/request/"
RESUME_ENDPOINT = "/v1/registration/resume_token/"


def basicauth(username, password):
    return "Basic " + b64encode(":".join((username, password)).encode()).decode()


@pytest.fixture
def mock_markdown(mocker):
    patch = mocker.patch("register.external_views.render_to_string")
    patch.return_value = "some markdown"

    return patch


@pytest.fixture(autouse=True)
def mock_cache(mocker):
    patch_get = mocker.patch("register.external_views.cache.get")
    patch_get.return_value = None

    mocker.patch("register.external_views.cache.set")


def set_state_info(state, name, value):
    ft = StateInformationFieldType(slug=name, field_format=StateFieldFormats.MARKDOWN)
    ft.save()

    info = StateInformation.objects.get(state=state, field_type=ft)
    info.text = value
    info.save()


def set_state_url_info(state, name, value):
    ft = StateInformationFieldType(slug=name, field_format=StateFieldFormats.URL)
    ft.save()

    info = StateInformation.objects.get(state=state, field_type=ft)
    info.text = value
    info.save()


@pytest.fixture
def basic_state_info():
    set_state_url_info(
        MINIMAL_REGISTRATION["state"], "external_tool_ovr", "https://example.com"
    )
    set_state_info(MINIMAL_REGISTRATION["state"], "registration_directions", "reg dirs")
    set_state_info(MINIMAL_REGISTRATION["state"], "id_requirements_ovr", "reqs")
    set_state_info(
        MINIMAL_REGISTRATION["state"], "registration_ovr_directions", "ovr dirs"
    )


@pytest.mark.django_db
def test_get_state_data_ovr_or_print(mock_markdown):
    state = baker.make_recipe("election.state", code=MINIMAL_REGISTRATION["state"])

    set_state_url_info(state, "external_tool_ovr", "https://example.com")
    set_state_info(state, "registration_directions", "reg dirs")
    set_state_info(state, "id_requirements_ovr", "reqs")
    set_state_info(state, "registration_ovr_directions", "ovr dirs")

    assert get_state_data(state.pk) == StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.OVR_OR_PRINT,
        external_tool_ovr="https://example.com",
        registration_directions="reg dirs",
        id_requirements_ovr="reqs",
        registration_ovr_directions="ovr dirs",
    )

    mock_markdown.assert_called_with(
        MARKDOWN_TEMPLATE,
        {
            "state_infos": {
                "external_tool_ovr": "https://example.com",
                "registration_directions": "reg dirs",
                "id_requirements_ovr": "reqs",
                "registration_ovr_directions": "ovr dirs",
            },
            "state_name": "Massachusetts",
            "flow_type": "ovr_or_print",
            "has_ovr_id_requirements": True,
        },
    )


@pytest.mark.django_db
def test_get_state_data_print_only(mock_markdown):
    state = baker.make_recipe("election.state", code=MINIMAL_REGISTRATION["state"])

    set_state_url_info(state, "external_tool_ovr", "")
    set_state_info(state, "registration_directions", "reg dirs")
    set_state_info(state, "id_requirements_ovr", "n/a")
    set_state_info(state, "registration_ovr_directions", "ovr dirs")

    assert get_state_data(state.pk) == StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.PRINT_ONLY,
        external_tool_ovr="",
        registration_directions="reg dirs",
        id_requirements_ovr="n/a",
        registration_ovr_directions="ovr dirs",
    )

    mock_markdown.assert_called_with(
        MARKDOWN_TEMPLATE,
        {
            "state_infos": {
                "external_tool_ovr": "",
                "registration_directions": "reg dirs",
                "id_requirements_ovr": "n/a",
                "registration_ovr_directions": "ovr dirs",
            },
            "state_name": "Massachusetts",
            "flow_type": "print_only",
            "has_ovr_id_requirements": False,
        },
    )


@pytest.mark.django_db
def test_get_state_data_ineligible(mock_markdown):
    state = baker.make_recipe("election.state", code="ND")

    set_state_url_info(state, "external_tool_ovr", "")
    set_state_info(state, "registration_directions", "reg dirs")
    set_state_info(state, "id_requirements_ovr", "")
    set_state_info(state, "registration_ovr_directions", "ovr dirs")

    assert get_state_data(state.pk) == StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.INELIGIBLE,
        external_tool_ovr="",
        registration_directions="reg dirs",
        id_requirements_ovr="",
        registration_ovr_directions="ovr dirs",
    )

    mock_markdown.assert_called_with(
        MARKDOWN_TEMPLATE,
        {
            "state_infos": {
                "external_tool_ovr": "",
                "registration_directions": "reg dirs",
                "id_requirements_ovr": "",
                "registration_ovr_directions": "ovr dirs",
            },
            "state_name": "North Dakota",
            "flow_type": "ineligible",
            "has_ovr_id_requirements": False,
        },
    )


@pytest.mark.django_db
def test_generate_response_ovr_or_print(mocker):
    mocker.patch(
        "register.external_views.get_state_data"
    ).return_value = StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.OVR_OR_PRINT,
        external_tool_ovr="https://example.com",
        registration_directions="reg dirs",
        id_requirements_ovr="reqs",
        registration_ovr_directions="ovr dirs",
    )

    mocker.patch("register.external_views.get_custom_ovr_link").return_value = None

    mocker.patch("register.external_views.make_action_jwt").return_value = (
        "jwt-token",
        datetime(2020, 7, 3, 12, 13, 14, tzinfo=timezone.utc),
    )

    mocker.patch.object(
        settings, "REGISTER_RESUME_URL", "https://voteamerica.example/resume/",
    )

    registration = baker.make_recipe(
        "register.registration",
        action=baker.make_recipe(
            "action.action", uuid="123e4567-e89b-12d3-a456-426614174000"
        ),
    )

    assert generate_response(registration) == {
        "message_markdown": "some markdown",
        "buttons": [
            {
                "message_text": "Register online",
                "primary": True,
                "url": "https://example.com",
                "event_tracking": {
                    "action": "123e4567-e89b-12d3-a456-426614174000",
                    "event_type": "FinishExternal",
                },
            },
            {
                "message_text": "Register by mail",
                "primary": False,
                "url": "https://voteamerica.example/resume/?skip_ovr=true&token=jwt-token",
                "url_expiry": "2020-07-03T12:13:14+00:00",
            },
        ],
    }


@pytest.mark.django_db
def test_generate_response_custom_ovr_or_print(mocker):
    mocker.patch(
        "register.external_views.get_state_data"
    ).return_value = StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.OVR_OR_PRINT,
        external_tool_ovr="https://example.com",
        registration_directions="reg dirs",
        id_requirements_ovr="reqs",
        registration_ovr_directions="ovr dirs",
    )

    mocker.patch(
        "register.external_views.get_custom_ovr_link"
    ).return_value = "https://example.com/custom"

    mocker.patch("register.external_views.make_action_jwt").return_value = (
        "jwt-token",
        datetime(2020, 7, 3, 12, 13, 14, tzinfo=timezone.utc),
    )

    mocker.patch.object(
        settings, "REGISTER_RESUME_URL", "https://voteamerica.example/resume/",
    )

    registration = baker.make_recipe(
        "register.registration",
        action=baker.make_recipe(
            "action.action", uuid="123e4567-e89b-12d3-a456-426614174000"
        ),
    )

    assert generate_response(registration) == {
        "message_markdown": "some markdown",
        "buttons": [
            {
                "message_text": "Register online",
                "primary": True,
                "url": "https://example.com/custom",
                "event_tracking": {
                    "action": "123e4567-e89b-12d3-a456-426614174000",
                    "event_type": "FinishExternal",
                },
            },
            {
                "message_text": "Register by mail",
                "primary": False,
                "url": "https://voteamerica.example/resume/?skip_ovr=true&token=jwt-token",
                "url_expiry": "2020-07-03T12:13:14+00:00",
            },
        ],
    }


@pytest.mark.django_db
def test_generate_response_print_only(mocker):
    mocker.patch(
        "register.external_views.get_state_data"
    ).return_value = StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.PRINT_ONLY,
        external_tool_ovr="https://example.com",
        registration_directions="reg dirs",
        id_requirements_ovr="reqs",
        registration_ovr_directions="ovr dirs",
    )

    mocker.patch("register.external_views.get_custom_ovr_link").return_value = None

    mocker.patch("register.external_views.make_action_jwt").return_value = (
        "jwt-token",
        datetime(2020, 7, 3, 12, 13, 14, tzinfo=timezone.utc),
    )

    mocker.patch.object(
        settings, "REGISTER_RESUME_URL", "https://voteamerica.example/resume/",
    )

    registration = baker.make_recipe(
        "register.registration",
        action=baker.make_recipe(
            "action.action", uuid="123e4567-e89b-12d3-a456-426614174000"
        ),
    )

    assert generate_response(registration) == {
        "message_markdown": "some markdown",
        "buttons": [
            {
                "message_text": "Register by mail",
                "primary": True,
                "url": "https://voteamerica.example/resume/?skip_ovr=true&token=jwt-token",
                "url_expiry": "2020-07-03T12:13:14+00:00",
            },
        ],
    }


@pytest.mark.django_db
def test_generate_response_ineligible(mocker):
    mocker.patch(
        "register.external_views.get_state_data"
    ).return_value = StateRegistrationData(
        instructions_markdown="some markdown",
        flow_type=RegistrationFlowType.INELIGIBLE,
        external_tool_ovr="https://example.com",
        registration_directions="reg dirs",
        id_requirements_ovr="reqs",
        registration_ovr_directions="ovr dirs",
    )

    mocker.patch("register.external_views.get_custom_ovr_link").return_value = None

    mocker.patch("register.external_views.make_action_jwt").return_value = (
        "jwt-token",
        datetime(2020, 7, 3, 12, 13, 14, tzinfo=timezone.utc),
    )

    mocker.patch.object(
        settings, "REGISTER_RESUME_URL", "https://voteamerica.example/resume/",
    )

    registration = baker.make_recipe(
        "register.registration",
        action=baker.make_recipe(
            "action.action", uuid="123e4567-e89b-12d3-a456-426614174000"
        ),
    )

    assert generate_response(registration) == {
        "message_markdown": "some markdown",
        "buttons": [],
    }


@pytest.mark.django_db
def test_create_and_resume_minimal(basic_state_info, mocker):
    key = baker.make_recipe("apikey.apikey")
    mocker.patch(
        "register.external_views.get_custom_ovr_link"
    ).return_value = "some link"

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.hashed_secret()))
    response = client.post(REQUEST_ENDPOINT, MINIMAL_REGISTRATION)

    assert response.status_code == 200

    registration = Registration.objects.first()
    assert registration.subscriber == key.subscriber
    assert registration.gender == None

    jwt_url = response.json()["buttons"][1]["url"]
    jwt_qs = parse_qs(urlparse(jwt_url).query)
    jwt = jwt_qs["token"][0]

    unauth_client = APIClient()
    response = unauth_client.get(f"{RESUME_ENDPOINT}?skip_ovr=true&token={jwt}")

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(registration.pk),
        "state": MINIMAL_REGISTRATION["state"],
        "action_id": str(registration.action_id),
        "custom_ovr_link": "some link",
        "allow_print_and_forward": False,
    }

    uuid_response = unauth_client.get(f"{RESUME_ENDPOINT}?uuid={registration.uuid}")

    assert response.status_code == 200
    assert response.json() == {
        "uuid": str(registration.pk),
        "state": MINIMAL_REGISTRATION["state"],
        "action_id": str(registration.action_id),
        "custom_ovr_link": "some link",
        "allow_print_and_forward": False,
    }


@pytest.mark.django_db
def test_create_maximal(basic_state_info):
    key = baker.make_recipe("apikey.apikey")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.hashed_secret()))
    response = client.post(REQUEST_ENDPOINT, MAXIMAL_REGISTRATION)

    assert response.status_code == 200

    registration = Registration.objects.first()
    assert registration.subscriber == key.subscriber
    assert registration.gender == RegistrationGender.MALE


@pytest.mark.django_db
def test_create_no_api_key():
    baker.make_recipe("apikey.apikey")

    client = APIClient()
    response = client.post(REQUEST_ENDPOINT, MINIMAL_REGISTRATION)

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_invalid_api_key():
    key = baker.make_recipe("apikey.apikey")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.secret))
    response = client.post(REQUEST_ENDPOINT, MINIMAL_REGISTRATION)

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_missing_field():
    key = baker.make_recipe("apikey.apikey")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.hashed_secret()))
    response = client.post(
        REQUEST_ENDPOINT,
        {
            "first_name": "John",
            "last_name": "Hancock",
            "date_of_birth": "1737-01-23",
            "email": "john@hancock.local",
            "address1": "30 Beacon Street",
            "city": "Boston",
            "state": "MA",
            "zipcode": "02108",
        },
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_extra_field():
    key = baker.make_recipe("apikey.apikey")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.hashed_secret()))
    response = client.post(
        REQUEST_ENDPOINT, {**MAXIMAL_REGISTRATION, "extra": "field",}
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_tn_mx():
    key = baker.make_recipe("apikey.apikey")

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=basicauth(str(key.uuid), key.hashed_secret()))
    response = client.post(
        REQUEST_ENDPOINT, {**MAXIMAL_REGISTRATION, "state": "TN", "title": "Mx"}
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_resume_invalid_jwt():
    unauth_client = APIClient()
    response = unauth_client.get(f"{RESUME_ENDPOINT}?skip_ovr=true&token=bad")

    assert response.status_code == 400


@pytest.mark.django_db
def test_resume_missing_jwt():
    unauth_client = APIClient()
    response = unauth_client.get(f"{RESUME_ENDPOINT}")

    assert response.status_code == 400
