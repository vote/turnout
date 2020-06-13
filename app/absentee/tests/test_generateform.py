import datetime

import pytest
from model_bakery import baker

from absentee.baker_recipes import IS_18_OR_OVER, STATE_ID_NUMBER
from absentee.generateform import (
    ENVELOPE_PATH,
    FAX_COVER_SHEET_PATH,
    SELF_PRINT_COVER_SHEET_PATH,
    generate_name,
    generate_pdf,
    get_submission_method,
    prepare_formdata,
)
from common.enums import SubmissionType
from common.pdf.pdftemplate import PDFTemplateSection, SignatureBoundingBox
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS

from ..state_pdf_data import STATE_DATA
from .test_data import add_state_info


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

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)
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

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)
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

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert (
        form_data["leo_contact_info"]
        == "https://www.voteamerica.com/local-election-offices/"
    )


@pytest.mark.django_db
def test_prepare_formdata_no_deadline():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

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

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["vbm_deadline"] == "some deadline"
    assert (
        form_data["vbm_first_day_to_apply"] == "At least 55 days before the election."
    )


@pytest.mark.django_db
def test_prepare_formdata_state_fields():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        region=addr.office.region,
        state=state,
        state_fields={"test_custom_field": "some_value"},
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["test_custom_field"] == "some_value"


@pytest.mark.django_db
def test_prepare_formdata_no_state_fields():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        region=addr.office.region,
        state=state,
        state_fields=None,
    )
    add_state_info(state, "vbm_deadline_mail", "Some DEADLINE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["vbm_deadline"] == "some deadline"


@pytest.mark.django_db
def test_prepare_formdata_state_fields_dont_overwrite():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state,
    )
    # include a duplicate key in state_fields
    ballot_request.state_fields = {"us_citizen": "not valid"}

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["us_citizen"] == True


@pytest.mark.django_db
def test_prepare_formdata_state_id_number():
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state,
    )

    # Default
    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["state_id_number"] == STATE_ID_NUMBER
    assert form_data.get("state_id_number_opt_1") == None
    assert form_data.get("state_id_number_opt_2") == None
    assert form_data.get("state_id_number_opt_3") == None

    # Option 1
    ballot_request.state_fields = {
        "state_id_number_opt_1": True,
    }
    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["state_id_number"] == STATE_ID_NUMBER
    assert form_data.get("state_id_number_opt_1") == STATE_ID_NUMBER
    assert form_data.get("state_id_number_opt_2") == None
    assert form_data.get("state_id_number_opt_3") == None

    # Option 2
    ballot_request.state_fields = {
        "state_id_number_opt_2": True,
    }
    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["state_id_number"] == STATE_ID_NUMBER
    assert form_data.get("state_id_number_opt_1") == None
    assert form_data.get("state_id_number_opt_2") == STATE_ID_NUMBER
    assert form_data.get("state_id_number_opt_3") == None


@pytest.mark.django_db
def test_prepare_formdata_auto_todays_date(mocker):
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        region=addr.office.region,
        state=state,
        submit_date=datetime.date(2020, 5, 10),
    )

    mocker.patch.dict(
        STATE_DATA,
        {state.code: {"auto_fields": [{"type": "todays_date", "slug": "some_date"}]}},
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)
    assert form_data["some_date"] == "05/10/2020"


@pytest.mark.django_db
def test_prepare_formdata_auto_copy(mocker):
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        region=addr.office.region,
        state=state,
        date_of_birth=datetime.date(1992, 5, 10),
        state_fields={"state_field_foo": "state_field_foo_val"},
    )

    mocker.patch.dict(
        STATE_DATA,
        {
            state.code: {
                "auto_fields": [
                    # Copy a top-level field
                    {"type": "copy", "slug": "cp_dob", "field": "date_of_birth"},
                    # Copy a computed field
                    {"type": "copy", "slug": "cp_year", "field": "year_of_birth"},
                    # Copy a state field
                    {"type": "copy", "slug": "cp_state", "field": "state_field_foo"},
                ]
            }
        },
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["date_of_birth"] == "05/10/1992"
    assert form_data["cp_dob"] == "05/10/1992"

    assert form_data["year_of_birth"] == "1992"
    assert form_data["cp_year"] == "1992"

    assert form_data["state_field_foo"] == "state_field_foo_val"
    assert form_data["cp_state"] == "state_field_foo_val"


@pytest.mark.django_db
def test_prepare_formdata_auto_static(mocker):
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state,
    )

    mocker.patch.dict(
        STATE_DATA,
        {
            state.code: {
                "auto_fields": [{"type": "static", "slug": "foo", "value": "bar"}]
            }
        },
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)
    assert form_data["foo"] == "bar"


@pytest.mark.django_db
def test_get_submission_method():
    req = baker.make_recipe("absentee.ballot_request")

    # With a signature, use the state's submission method
    assert get_submission_method(req) == SubmissionType.SELF_PRINT

    req.esign_method = SubmissionType.LEO_FAX
    assert get_submission_method(req) == SubmissionType.LEO_FAX

    req.esign_method = SubmissionType.LEO_EMAIL
    assert get_submission_method(req) == SubmissionType.LEO_EMAIL

    req.esign_method = SubmissionType.SELF_PRINT
    assert get_submission_method(req) == SubmissionType.SELF_PRINT

    # Without a signature, always use self-print
    req.signature = None

    req.esign_method = SubmissionType.LEO_FAX
    assert get_submission_method(req) == SubmissionType.SELF_PRINT

    req.esign_method = SubmissionType.LEO_EMAIL
    assert get_submission_method(req) == SubmissionType.SELF_PRINT

    req.esign_method = SubmissionType.SELF_PRINT
    assert get_submission_method(req) == SubmissionType.SELF_PRINT


def test_generate_pdf_email(mocker):
    mocker.patch.dict(
        STATE_DATA,
        {
            "XX": {
                "pages": 2,
                "signatures": {2: {"x": 1, "y": 2, "width": 3, "height": 4}},
            }
        },
    )

    MockPDFTemplate = mocker.patch("absentee.generateform.PDFTemplate")

    generate_pdf({"some": "data",}, "XX", SubmissionType.LEO_EMAIL, "some-sig")

    MockPDFTemplate.assert_called_with(
        [
            PDFTemplateSection(
                path="absentee/templates/pdf/states/XX.pdf",
                is_form=True,
                flatten_form=False,
                signature_locations={
                    2: SignatureBoundingBox(x=1, y=2, width=3, height=4),
                },
            )
        ]
    )

    MockPDFTemplate().fill.assert_called_with(
        {"some": "data", "num_pages": "2"}, signature="some-sig"
    )


def test_generate_pdf_fax(mocker):
    mocker.patch.dict(
        STATE_DATA, {"XX": {"pages": 3,}},
    )

    MockPDFTemplate = mocker.patch("absentee.generateform.PDFTemplate")

    generate_pdf({"some": "data"}, "XX", SubmissionType.LEO_FAX, "some-sig")

    MockPDFTemplate.assert_called_with(
        [
            PDFTemplateSection(path=FAX_COVER_SHEET_PATH, is_form=True),
            PDFTemplateSection(
                path="absentee/templates/pdf/states/XX.pdf",
                is_form=True,
                flatten_form=False,
                signature_locations=None,
            ),
        ]
    )

    MockPDFTemplate().fill.assert_called_with(
        {"some": "data", "num_pages": "4"}, signature="some-sig"
    )


def test_generate_pdf_self_print(mocker):
    MockPDFTemplate = mocker.patch("absentee.generateform.PDFTemplate")

    generate_pdf({"some": "data"}, "XX", SubmissionType.SELF_PRINT, "some-sig")

    MockPDFTemplate.assert_called_with(
        [
            PDFTemplateSection(path=SELF_PRINT_COVER_SHEET_PATH, is_form=True),
            PDFTemplateSection(
                path="absentee/templates/pdf/states/XX.pdf",
                is_form=True,
                flatten_form=False,
                signature_locations=None,
            ),
            PDFTemplateSection(path=ENVELOPE_PATH, is_form=True),
        ]
    )

    MockPDFTemplate().fill.assert_called_with(
        {"some": "data", "num_pages": "3"}, signature="some-sig"
    )
