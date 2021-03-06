import datetime

import pytest
from model_bakery import baker
from pdf_template import PDFTemplateSection, SignatureBoundingBox

from absentee.baker_recipes import IS_18_OR_OVER, STATE_ID_NUMBER
from absentee.generateform import (
    ENVELOPE_PATH,
    FAX_COVER_SHEET_PATH,
    NOTRACKER_PRINT_AND_FORWARD_COVER_SHEET_PATH,
    PRINT_AND_FORWARD_COVER_SHEET_PATH,
    SELF_PRINT_COVER_SHEET_PATH,
    generate_name,
    generate_pdf_template,
    get_submission_method,
    prepare_formdata,
)
from common.enums import SubmissionType
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS

from ..state_pdf_data import STATE_DATA
from .test_data import add_state_info


def test_generate_name():
    assert (
        generate_name("MA", "McAdams~Webster") == "ma-mcadamswebster-ballotrequest.pdf"
    )
    assert (
        generate_name("MA", "McAdams~Webster", suffix="foo")
        == "ma-mcadamswebster-ballotrequest-foo.pdf"
    )


@pytest.fixture
def mock_i90(mocker):
    mocker.patch("absentee.generateform.shorten_url", return_value="foo")
    mocker.patch("absentee.generateform.get_shortened_url", return_value=None)


@pytest.mark.django_db
def test_prepare_formdata(mock_i90):
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
    assert form_data["vbm_first_day_to_apply"] == "Some DATE"
    assert form_data["leo_contact_info"] == f"Email: {addr.email}\nPhone: {addr.phone}"


@pytest.mark.django_db
def test_prepare_formdata_just_phone(mock_i90):
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
def test_prepare_formdata_no_phone_or_email(mock_i90):
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
def test_prepare_formdata_no_deadline(mock_i90):
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request", region=addr.office.region, state=state
    )

    add_state_info(state, "vbm_first_day_to_apply", "Some DATE")

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["vbm_deadline"] == "As soon as possible."
    assert form_data["vbm_first_day_to_apply"] == "Some DATE"


@pytest.mark.django_db
def test_prepare_formdata_no_first_day_to_apply(mock_i90):
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
def test_prepare_formdata_state_fields(mock_i90):
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
def test_prepare_formdata_no_state_fields(mock_i90):
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
def test_prepare_formdata_state_fields_dont_overwrite(mock_i90):
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
def test_prepare_formdata_state_id_number(mock_i90):
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
def test_prepare_formdata_auto_todays_date(mocker, mock_i90):
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
def test_prepare_formdata_auto_copy(mocker, mock_i90):
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
def test_prepare_formdata_auto_static(mocker, mock_i90):
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
def test_prepare_formdata_auto_conditional(mocker, mock_i90):
    addr = baker.make_recipe("official.absentee_ballot_address")
    state = baker.make_recipe("election.state")
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        email="foo@example.com",
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
                    # This one should activate
                    {
                        "type": "conditional",
                        "condition": {
                            "slug": "state_field_foo",
                            "value": "state_field_foo_val",
                        },
                        "fill": {"slug": "filled_field", "value": "filled_value"},
                    },
                    # This one should activate
                    {
                        "type": "conditional",
                        "condition": {
                            "slug": "state_field_foo",
                            "value": "state_field_foo_val",
                        },
                        "fill": {"slug": "filled_field_2", "value_from": "email"},
                    },
                    # This one should be ignored
                    {
                        "type": "conditional",
                        "condition": {
                            "slug": "state_field_foo",
                            "value": "state_field_bar_val",
                        },
                        "fill": {"slug": "wrong_fill", "value": "wrong_val"},
                    },
                    # This one should also be ignored
                    {
                        "type": "conditional",
                        "condition": {
                            "slug": "state_field_other",
                            "value": "state_field_bar_val",
                        },
                        "fill": {"slug": "wrong_fill_2", "value_from": "email"},
                    },
                ]
            }
        },
    )

    form_data = prepare_formdata(ballot_request, STATE_ID_NUMBER, IS_18_OR_OVER,)

    assert form_data["state_field_foo"] == "state_field_foo_val"
    assert form_data["filled_field"] == "filled_value"
    assert form_data["filled_field_2"] == "foo@example.com"
    assert form_data.get("wrong_fill") is None
    assert form_data.get("wrong_fill_2") is None


@pytest.mark.django_db
def test_get_submission_method():
    req = baker.make_recipe("absentee.ballot_request")

    # If there is a request mailing address,
    assert get_submission_method(req) == SubmissionType.PRINT_AND_FORWARD

    req.request_mailing_address1 = ""

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

    template, num_pages = generate_pdf_template("XX", SubmissionType.LEO_EMAIL)

    assert num_pages == 2
    assert template.template_files == [
        PDFTemplateSection(
            path="absentee/templates/pdf/states/XX.pdf",
            is_form=True,
            flatten_form=False,
            signature_locations={2: SignatureBoundingBox(x=1, y=2, width=3, height=4),},
        )
    ]


def test_generate_pdf_fax(mocker):
    mocker.patch.dict(
        STATE_DATA, {"XX": {"pages": 3,}},
    )

    template, num_pages = generate_pdf_template("XX", SubmissionType.LEO_FAX)
    assert num_pages == 4
    assert template.template_files == [
        PDFTemplateSection(path=FAX_COVER_SHEET_PATH, is_form=True),
        PDFTemplateSection(
            path="absentee/templates/pdf/states/XX.pdf",
            is_form=True,
            flatten_form=False,
            signature_locations=None,
        ),
    ]


def test_generate_pdf_self_print(mocker):
    template, num_pages = generate_pdf_template("XX", SubmissionType.SELF_PRINT)
    assert num_pages == 3
    assert template.template_files == [
        PDFTemplateSection(path=SELF_PRINT_COVER_SHEET_PATH, is_form=True),
        PDFTemplateSection(
            path="absentee/templates/pdf/states/XX.pdf",
            is_form=True,
            flatten_form=False,
            signature_locations=None,
        ),
        PDFTemplateSection(path=ENVELOPE_PATH, is_form=True),
    ]


@pytest.mark.django_db
def test_generate_pdf_mail(mocker):
    template, num_pages = generate_pdf_template("XX", SubmissionType.PRINT_AND_FORWARD)
    assert num_pages == 3
    assert template.template_files == [
        PDFTemplateSection(
            path=NOTRACKER_PRINT_AND_FORWARD_COVER_SHEET_PATH,
            is_form=True,
            flatten_form=True,
        ),
        PDFTemplateSection(
            path="absentee/templates/pdf/states/XX.pdf",
            is_form=True,
            flatten_form=True,
            signature_locations=None,
        ),
    ]
