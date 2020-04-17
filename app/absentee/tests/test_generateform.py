import pytest
from model_bakery import baker

from absentee.generateform import generate_name, prepare_formdata
from election.models import State, StateInformation
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS


def add_text_info(state: State, slug: str, value: str):
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

    add_text_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_text_info(state, "vbm_first_day_to_apply", "Some DATE")

    assert prepare_formdata(addr.office.region.external_id, state.code) == {
        "vbm_submission_address": ABSENTEE_BALLOT_MAILING_ADDRESS,
        "vbm_deadline": "some deadline",
        "vbm_first_day_to_apply": "some date",
        "vbm_contact_info": f"Email: {addr.email}\nPhone: {addr.phone}",
    }


@pytest.mark.django_db
def test_prepare_formdata_just_phone():
    addr = baker.make_recipe("official.absentee_ballot_address", email=None)
    state = baker.make_recipe("election.state")

    add_text_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_text_info(state, "vbm_first_day_to_apply", "Some DATE")

    assert prepare_formdata(addr.office.region.external_id, state.code) == {
        "vbm_submission_address": ABSENTEE_BALLOT_MAILING_ADDRESS,
        "vbm_deadline": "some deadline",
        "vbm_first_day_to_apply": "some date",
        "vbm_contact_info": f"Phone: {addr.phone}",
    }


@pytest.mark.django_db
def test_prepare_formdata_no_phone_or_email():
    addr = baker.make_recipe("official.absentee_ballot_address", email=None, phone=None)
    state = baker.make_recipe("election.state")

    add_text_info(state, "vbm_deadline_mail", "Some DEADLINE")
    add_text_info(state, "vbm_first_day_to_apply", "Some DATE")

    assert prepare_formdata(addr.office.region.external_id, state.code) == {
        "vbm_submission_address": ABSENTEE_BALLOT_MAILING_ADDRESS,
        "vbm_deadline": "some deadline",
        "vbm_first_day_to_apply": "some date",
        "vbm_contact_info": "https://www.usvotefoundation.org/vote/eoddomestic.htm",
    }


@pytest.mark.django_db
def test_prepare_formdata_no_deadline():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")

    add_text_info(state, "vbm_first_day_to_apply", "Some DATE")

    assert prepare_formdata(addr.office.region.external_id, state.code) == {
        "vbm_submission_address": ABSENTEE_BALLOT_MAILING_ADDRESS,
        "vbm_deadline": "As soon as possible.",
        "vbm_first_day_to_apply": "some date",
        "vbm_contact_info": f"Email: {addr.email}\nPhone: {addr.phone}",
    }


@pytest.mark.django_db
def test_prepare_formdata_no_first_day_to_apply():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")

    add_text_info(state, "vbm_deadline_mail", "Some DEADLINE")

    assert prepare_formdata(addr.office.region.external_id, state.code) == {
        "vbm_submission_address": ABSENTEE_BALLOT_MAILING_ADDRESS,
        "vbm_deadline": "some deadline",
        "vbm_first_day_to_apply": "At least 55 days before the election.",
        "vbm_contact_info": f"Email: {addr.email}\nPhone: {addr.phone}",
    }
