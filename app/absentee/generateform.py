import logging
from typing import IO, Any, Dict, Optional

from django.core.files import File
from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify
from PIL import Image

from common import enums
from common.analytics import statsd
from common.pdf.pdftemplate import PDFTemplate, PDFTemplateSection, SignatureBoundingBox
from common.utils.format import StringFormatter
from election.models import StateInformation
from storage.models import SecureUploadItem, StorageItem

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest
from .state_pdf_data import STATE_DATA
from .tasks import send_ballotrequest_leo_email, send_ballotrequest_notification

logger = logging.getLogger("absentee")

COVER_SHEET_PATH = "absentee/templates/pdf/cover.pdf"
ENVELOPE_PATH = "absentee/templates/pdf/envelope.pdf"


def generate_name(state_code: str, last_name: str):
    """
    Generates a name for the PDF
    """
    filename = slugify(f"{state_code} {last_name} ballotrequest").lower()
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
    form_data["address1_2_city"] = fmt.format("{address1_2}, {state}", **form_data)
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
            ] = "https://www.usvotefoundation.org/vote/eoddomestic.htm"
    else:
        form_data[
            "leo_contact_info"
        ] = "https://www.usvotefoundation.org/vote/eoddomestic.htm"

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
            else:
                raise RuntimeError(f"Invalid auto_field type: {auto_type}")

    return form_data


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


def load_signature_image(
    signature_attachment: Optional[SecureUploadItem],
) -> Optional[Image.Image]:
    if not signature_attachment:
        return None

    return Image.open(signature_attachment.file)


@statsd.timed("turnout.absentee.absentee_application_pdfgeneration")
def generate_pdf(
    form_data: Dict[str, Any],
    state_code: str,
    signature: Optional[Image.Image] = None,
    include_cover_sheet=True,
) -> IO:
    sections = [
        PDFTemplateSection(
            path=f"absentee/templates/pdf/states/{state_code}.pdf",
            is_form=True,
            flatten_form=False,
            signature_locations=get_signature_locations(state_code),
        ),
        PDFTemplateSection(path=ENVELOPE_PATH, is_form=True),
    ]

    if include_cover_sheet:
        sections.insert(0, PDFTemplateSection(path=COVER_SHEET_PATH, is_form=True))

    return PDFTemplate(sections).fill(form_data, signature=signature)


def ballot_request_is_emailable(ballot_request: BallotRequest):
    return ballot_request.state.code == "GA" and ballot_request.signature is not None


def process_ballot_request(
    ballot_request: BallotRequest, state_id_number: str, is_18_or_over: bool
):
    form_data = prepare_formdata(ballot_request, state_id_number, is_18_or_over)
    print(form_data)
    signature = load_signature_image(ballot_request.signature)
    is_emailable = ballot_request_is_emailable(ballot_request)

    with generate_pdf(
        form_data,
        ballot_request.state.code,
        signature,
        include_cover_sheet=not is_emailable,
    ) as filled_pdf:
        item = StorageItem(
            app=enums.FileType.ABSENTEE_REQUEST_FORM,
            email=ballot_request.email,
            subscriber=ballot_request.subscriber,
        )
        item.file.save(
            generate_name(ballot_request.state.code, ballot_request.last_name),
            File(filled_pdf),
            True,
        )

    ballot_request.result_item = item
    ballot_request.save(update_fields=["result_item"])

    if is_emailable:
        send_ballotrequest_leo_email.delay(ballot_request.pk)
    else:
        send_ballotrequest_notification.delay(ballot_request.pk)

    logger.info(f"New PDF Created: Ballot Request {item.pk}")
