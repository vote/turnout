import pytest
from model_bakery import baker

from absentee.baker_recipes import IS_18_OR_OVER, STATE_ID_NUMBER
from absentee.generateform import generate_name, prepare_formdata
from election.models import State, StateInformation
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS


def add_state_info(state: State, slug: str, value: str):
    ft = baker.make_recipe("election.markdown_field_type", slug=slug)

    info = StateInformation.objects.get(state=state.code, field_type=ft.uuid)
    info.text = value
    info.save()


def test_generate_name():
    assert (
        generate_name("MA", "McAdams~Webster") == "ma-mcadamswebster-ballotrequest.pdf"
    )


@pytest.mark.django_db
def test_prepare_formdata():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)
    assert form_data["mailto"] == ABSENTEE_BALLOT_MAILING_ADDRESS
    assert form_data["vbm_deadline"] == "some deadline"
    assert form_data["vbm_first_day_to_apply"] == "some date"
    assert form_data["leo_contact_info"] == f"Email: {addr.email}\nPhone: {addr.phone}"


@pytest.mark.django_db
def test_prepare_formdata_just_phone():
    addr = baker.make_recipe("official.absentee_ballot_address", email=None)
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)
    assert form_data["leo_contact_info"] == f"Phone: {addr.phone}"


@pytest.mark.django_db
def test_prepare_formdata_no_phone_or_email():
    addr = baker.make_recipe("official.absentee_ballot_address", email=None, phone=None)
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)

    assert (
        form_data["leo_contact_info"]
        == "https://www.usvotefoundation.org/vote/eoddomestic.htm"
    )


@pytest.mark.django_db
def test_prepare_formdata_no_deadline():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)

    assert form_data["vbm_deadline"] == "As soon as possible."
    assert form_data["vbm_first_day_to_apply"] == "some date"


@pytest.mark.django_db
def test_prepare_formdata_no_first_day_to_apply():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_deadline_mail", "Some DEADLINE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)

    assert form_data["vbm_deadline"] == "some deadline"
    assert (
        form_data["vbm_first_day_to_apply"] == "At least 55 days before the election."
    )


@pytest.mark.django_db
def test_prepare_formdata_state_fields():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state,
        state_fields={"test_custom_field": "some_value"}
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)

    assert form_data["test_custom_field"] == "some_value"


@pytest.mark.django_db
def test_prepare_formdata_state_fields_dont_overwrite():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state,
    )
    # include a duplicate key in state_fields
    ballot_request.state_fields = {"us_citizen": "not valid"}

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER)

    assert form_data["us_citizen"] == True
