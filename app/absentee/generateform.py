import datetime
import logging
import os
from typing import Any, Dict, Optional, Tuple

from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify
from pdf_template import PDFTemplate, PDFTemplateSection, SignatureBoundingBox

from common import enums
from common.apm import tracer
from common.models import DelayedTask
from common.pdf.pdftemplate import fill_pdf_template
from common.utils.format import StringFormatter
from election.models import StateInformation
from storage.models import StorageItem

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest
from .state_pdf_data import STATE_DATA
from .tasks import (
    send_ballotrequest_leo_email,
    send_ballotrequest_leo_fax,
    send_ballotrequest_notification,
)

logger = logging.getLogger("absentee")

SELF_PRINT_COVER_SHEET_PATH = "absentee/templates/pdf/cover.pdf"
PRINT_AND_FORWARD_COVER_SHEET_PATH = (
    "absentee/templates/pdf/print-and-forward-cover.pdf"
)
FAX_COVER_SHEET_PATH = "absentee/templates/pdf/fax-cover.pdf"
ENVELOPE_PATH = "absentee/templates/pdf/envelope.pdf"


def generate_name(state_code: str, last_name: str, suffix: str = None):
    """
    Generates a name for the PDF
    """
    base = f"{state_code} {last_name} ballotrequest"
    if suffix:
        base += f" {suffix}"
    filename = slugify(base).lower()
    return f"{filename}.pdf"


def state_text_property(state_code: str, slug: str, lower=False) -> Optional[str]:
    """
    Helper to read a sigle StateInformation field
    """
    try:
        text = (
            StateInformation.objects.only("field_type", "text")
            .get(state=state_code, field_type__slug=slug)
            .text
        )

        if lower:
            text = text.lower()

        return text
    except StateInformation.DoesNotExist:
        return None


@tracer.wrap()
def prepare_formdata(
    ballot_request: BallotRequest, state_id_number: str, is_18_or_over: bool,
) -> Dict[str, Any]:
    """
    Assembles all the form data we need to fill out an absentee ballot request
    form.
    """
    form_data = model_to_dict(ballot_request)
    # insert state_fields into form_data top-level, without overwriting existing
    state_fields = form_data.get("state_fields", {})
    if state_fields:
        for state_field_key, state_field_value in state_fields.items():
            if not state_field_key in form_data:
                form_data[state_field_key] = state_field_value

        # Some states (AK) have different boxes for different types of state ID
        # numbers. So we allow for a radio button to select which box the state ID
        # should go in.
        if state_fields.get("state_id_number_opt_1"):
            form_data["state_id_number_opt_1"] = state_id_number
        elif state_fields.get("state_id_number_opt_2"):
            form_data["state_id_number_opt_2"] = state_id_number
        elif state_fields.get("state_id_number_opt_3"):
            form_data["state_id_number_opt_3"] = state_id_number

    fmt = StringFormatter(missing="")

    # some fields need to be converted to string representation
    # state, date_of_birth, enums
    form_data["state"] = ballot_request.state.code
    if ballot_request.mailing_state:
        form_data["mailing_state"] = ballot_request.mailing_state.code
    form_data["date_of_birth"] = ballot_request.date_of_birth.strftime("%m/%d/%Y")
    form_data["month_of_birth"] = ballot_request.date_of_birth.strftime("%m")
    form_data["day_of_birth"] = ballot_request.date_of_birth.strftime("%d")
    form_data["year_of_birth"] = ballot_request.date_of_birth.strftime("%Y")
    form_data["state_id_number"] = state_id_number
    form_data["is_18_or_over"] = is_18_or_over

    if ballot_request.middle_name:
        form_data["middle_initial"] = form_data["middle_name"][0].upper()
        form_data["full_name"] = fmt.format(
            "{first_name} {middle_name} {last_name}", **form_data
        )
    else:
        form_data["full_name"] = fmt.format("{first_name} {last_name}", **form_data)

    # get county from region
    form_data["county"] = ballot_request.region.county
    form_data["region"] = ballot_request.region.name

    # combine address fields for states where the form is wonky
    form_data["address1_2"] = fmt.format("{address1} {address2}", **form_data).strip()
    form_data["address1_2_city"] = fmt.format("{address1_2}, {city}", **form_data)
    form_data["address_city_state_zip"] = fmt.format(
        "{city}, {state} {zipcode}", **form_data
    )
    form_data["full_address"] = fmt.format(
        "{address1_2} {address_city_state_zip}", **form_data
    )
    if ballot_request.mailing_state:
        form_data["has_mailing_address"] = True
        form_data["mailing_address1_2"] = fmt.format(
            "{mailing_address1} {mailing_address2}", **form_data
        ).strip()
        form_data["mailing_city_state_zip"] = fmt.format(
            "{mailing_city}, {mailing_state} {mailing_zipcode}", **form_data
        )
        form_data["mailing_full_address"] = fmt.format(
            "{mailing_address1_2} {mailing_city_state_zip}", **form_data
        )
    else:
        form_data["same_mailing_address"] = True

    # Some forms always want your mailing address, even if it's the same as
    # your registered address (NC, for example). The mailing_* vars are only
    # populated if you *do* have a separate address, but these are *always*
    # populated.
    if ballot_request.mailing_state:
        form_data["mailing_or_reg_address1"] = form_data["mailing_address1"]
        form_data["mailing_or_reg_address2"] = form_data["mailing_address2"]
        form_data["mailing_or_reg_city"] = form_data["mailing_city"]
        form_data["mailing_or_reg_state"] = form_data["mailing_state"]
        form_data["mailing_or_reg_zipcode"] = form_data["mailing_zipcode"]
        form_data["mailing_or_reg_address1_2"] = form_data["mailing_address1_2"]
        form_data["mailing_or_reg_city_state_zip"] = form_data["mailing_city_state_zip"]
        form_data["mailing_or_reg_full_address"] = form_data["mailing_full_address"]
    else:
        form_data["mailing_or_reg_address1"] = form_data["address1"]
        form_data["mailing_or_reg_address2"] = form_data["address2"]
        form_data["mailing_or_reg_city"] = form_data["city"]
        form_data["mailing_or_reg_state"] = form_data["state"]
        form_data["mailing_or_reg_zipcode"] = form_data["zipcode"]
        form_data["mailing_or_reg_address1_2"] = form_data["address1_2"]
        form_data["mailing_or_reg_city_state_zip"] = form_data["address_city_state_zip"]
        form_data["mailing_or_reg_full_address"] = form_data["full_address"]

    # consolidated ballot request address
    form_data["request_mailing_address_full"] = (
        form_data["request_mailing_address1"] or ""
    )
    if form_data["request_mailing_address2"]:
        form_data["request_mailing_address_full"] += (
            "\n" + form_data["request_mailing_address2"]
        )
    form_data["request_mailing_address_full"] += fmt.format(
        "\n{request_mailing_city}, {request_mailing_state} {request_mailing_zipcode}",
        **form_data,
    )

    # find the mailing address and contact info
    contact_info = get_absentee_contact_info(ballot_request.region.external_id)
    if contact_info.full_address:
        form_data["mailto"] = contact_info.full_address
        form_data["mailto_address1"] = contact_info.address1
        form_data["mailto_address2"] = contact_info.address2
        form_data["mailto_address3"] = contact_info.address3
        form_data["mailto_city_state_zip"] = contact_info.city_state_zip

        # split by linebreaks, because each line is a separate field in the envelope PDF
        for num, line in enumerate(form_data["mailto"].splitlines()):
            form_data[f"mailto_line_{num+1}"] = line
            form_data[f"mailto_line_upper_{num+1}"] = line

        if contact_info.email or contact_info.phone:
            contact_info_lines = []
            if contact_info.email:
                contact_info_lines.append(f"Email: {contact_info.email}")
            if contact_info.phone:
                contact_info_lines.append(f"Phone: {contact_info.phone}")

            form_data["leo_contact_info"] = "\n".join(contact_info_lines)
        else:
            form_data[
                "leo_contact_info"
            ] = "https://www.voteamerica.com/local-election-offices/"
    else:
        form_data[
            "leo_contact_info"
        ] = "https://www.voteamerica.com/local-election-offices/"

    if contact_info.fax:
        form_data["leo_fax"] = contact_info.fax

    # Find state-specific info
    form_data["vbm_deadline"] = (
        state_text_property(ballot_request.state.code, "vbm_deadline_mail", lower=True)
        or "As soon as possible."
    )

    # If we don't have data, make the most conservative assumption: 55 days before the election
    form_data["vbm_first_day_to_apply"] = (
        state_text_property(
            ballot_request.state.code, "vbm_first_day_to_apply", lower=True
        )
        or "At least 55 days before the election."
    )

    # Signatures are handled separately
    del form_data["signature"]

    # Handle auto_fields
    state_data = STATE_DATA.get(ballot_request.state.code.upper())
    if state_data and state_data.get("auto_fields"):
        for auto_field in state_data["auto_fields"]:
            auto_type = auto_field["type"]
            if auto_type == "todays_date":
                if ballot_request.submit_date:
                    form_data[auto_field["slug"]] = ballot_request.submit_date.strftime(
                        "%m/%d/%Y"
                    )
            elif auto_type == "copy":
                form_data[auto_field["slug"]] = form_data.get(auto_field["field"])
            elif auto_type == "static":
                form_data[auto_field["slug"]] = auto_field["value"]
            elif auto_type == "conditional":
                if (
                    form_data.get(auto_field["condition"]["slug"])
                    == auto_field["condition"]["value"]
                ):
                    if auto_field["fill"].get("value"):
                        form_data[auto_field["fill"]["slug"]] = auto_field["fill"][
                            "value"
                        ]
                    else:
                        form_data[auto_field["fill"]["slug"]] = form_data.get(
                            auto_field["fill"]["value_from"]
                        )
            else:
                raise RuntimeError(f"Invalid auto_field type: {auto_type}")

    # 2020 vbm deadline
    try:
        state_mail_deadline_2020 = (
            StateInformation.objects.only("field_type", "text")
            .get(
                state=ballot_request.state,
                field_type__slug="2020_vbm_deadline_by_mail",
            )
            .text
        )
    except StateInformation.DoesNotExist:
        state_mail_deadline_2020 = "mailed as soon as possible."
    form_data["2020_state_deadline"] = state_mail_deadline_2020

    return form_data


@tracer.wrap()
def get_signature_locations(
    state_code: str,
) -> Optional[Dict[int, SignatureBoundingBox]]:
    state_data = STATE_DATA.get(state_code.upper())
    if not state_data:
        return None

    sig_data = state_data.get("signatures")
    if not sig_data:
        return None

    return {
        page: SignatureBoundingBox(**location) for page, location in sig_data.items()
    }


@tracer.wrap()
def generate_pdf_template(
    state_code: str, submission_method: enums.SubmissionType,
) -> Tuple[PDFTemplate, int]:
    # We assume a 1-page form if there's no YAML file with the number of pages.
    # This is usually true, and we also don't use the page count except in
    # esign states, where we always have the YAML file with the accurate page
    # count.
    state_template_pages = STATE_DATA.get(state_code, {}).get("pages", 1)

    if submission_method == enums.SubmissionType.LEO_EMAIL:
        sections = [
            PDFTemplateSection(
                path=f"absentee/templates/pdf/states/{state_code}.pdf",
                is_form=True,
                flatten_form=False,
                signature_locations=get_signature_locations(state_code),
            )
        ]

        num_pages = state_template_pages
    elif submission_method == enums.SubmissionType.LEO_FAX:
        sections = [
            PDFTemplateSection(path=FAX_COVER_SHEET_PATH, is_form=True),
            PDFTemplateSection(
                path=f"absentee/templates/pdf/states/{state_code}.pdf",
                is_form=True,
                flatten_form=False,
                signature_locations=get_signature_locations(state_code),
            ),
        ]

        num_pages = state_template_pages + 1
    elif submission_method == enums.SubmissionType.PRINT_AND_FORWARD:
        form_path = f"absentee/templates/pdf/states/{state_code}-print-and-forward.pdf"
        if not os.path.exists(form_path):
            form_path = f"absentee/templates/pdf/states/{state_code}.pdf"
        sections = [
            PDFTemplateSection(
                path=PRINT_AND_FORWARD_COVER_SHEET_PATH,
                is_form=True,
                flatten_form=True,
            ),
            PDFTemplateSection(path=form_path, is_form=True, flatten_form=True,),
        ]
        num_pages = state_template_pages + 2
    else:
        # Self-print
        sections = [
            PDFTemplateSection(path=SELF_PRINT_COVER_SHEET_PATH, is_form=True),
            PDFTemplateSection(
                path=f"absentee/templates/pdf/states/{state_code}.pdf",
                is_form=True,
                flatten_form=False,
            ),
            PDFTemplateSection(path=ENVELOPE_PATH, is_form=True),
        ]

        num_pages = state_template_pages + 2

    return (PDFTemplate(sections), num_pages)


def get_submission_method(ballot_request: BallotRequest) -> enums.SubmissionType:
    if ballot_request.request_mailing_address1:
        return enums.SubmissionType.PRINT_AND_FORWARD

    if ballot_request.signature is None:
        return enums.SubmissionType.SELF_PRINT

    return ballot_request.esign_method or enums.SubmissionType.SELF_PRINT


def populate_storage_item(
    item: StorageItem,
    ballot_request: BallotRequest,
    state_id_number: str,
    is_18_or_over: bool,
):
    form_data = prepare_formdata(ballot_request, state_id_number, is_18_or_over)
    submission_method = get_submission_method(ballot_request)

    pdf_template, num_pages = generate_pdf_template(
        ballot_request.state.code, submission_method
    )
    form_data.update({"num_pages": str(num_pages)})

    file_name = generate_name(ballot_request.state.code, ballot_request.last_name)

    fill_pdf_template(
        pdf_template, form_data, item, file_name, ballot_request.signature
    )

    if submission_method == enums.SubmissionType.PRINT_AND_FORWARD:
        mail_item = StorageItem(
            app=enums.FileType.ABSENTEE_REQUEST_FORM,
            email=ballot_request.email,
            subscriber=ballot_request.subscriber,
        )
        mail_template, mail_pages = generate_pdf_template(
            ballot_request.state.code, enums.SubmissionType.PRINT_AND_FORWARD
        )
        mail_file_name = generate_name(
            ballot_request.state.code, ballot_request.last_name, suffix="mail"
        )
        fill_pdf_template(mail_template, form_data, mail_item, mail_file_name)
    else:
        mail_item = None

    return submission_method, mail_item


@tracer.wrap()
def queue_download_reminder(ballot_request: BallotRequest) -> None:
    # send a reminder the next day
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    when = datetime.datetime(
        tomorrow.year,
        tomorrow.month,
        tomorrow.day,
        17,
        0,
        0,  # 1700 UTC == 12pm ET == 9am PT == 6am HT
        tzinfo=datetime.timezone.utc,
    )
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)

    DelayedTask.schedule(
        when, "absentee.tasks.send_download_reminder", str(ballot_request.uuid),
    )


@tracer.wrap()
def process_ballot_request(
    ballot_request: BallotRequest, state_id_number: str, is_18_or_over: bool
):
    item = StorageItem(
        app=enums.FileType.ABSENTEE_REQUEST_FORM,
        email=ballot_request.email,
        subscriber=ballot_request.subscriber,
    )

    submission_method, item_mail = populate_storage_item(
        item, ballot_request, state_id_number, is_18_or_over
    )

    ballot_request.result_item = item
    ballot_request.result_item_mail = item_mail
    ballot_request.save(update_fields=["result_item", "result_item_mail"])

    if submission_method == enums.SubmissionType.LEO_EMAIL:
        send_ballotrequest_leo_email.delay(ballot_request.pk)
    elif submission_method == enums.SubmissionType.LEO_FAX:
        send_ballotrequest_leo_fax.delay(ballot_request.pk)
    else:
        # self-print and print-and-forward take same path
        send_ballotrequest_notification.delay(ballot_request.pk)

        queue_download_reminder(ballot_request)

    logger.info(f"New PDF Created: Ballot Request {item.pk}")
