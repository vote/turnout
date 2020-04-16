import logging
from typing import IO, TYPE_CHECKING, Any, Dict, Optional

from django.core.files import File
from django.template.defaultfilters import slugify

from common import enums
from common.analytics import statsd
from common.pdf.pdftemplate import PDFTemplate, PDFTemplateSection
from election.models import StateInformation
from storage.models import StorageItem

from .contactinfo import get_absentee_contact_info
from .models import BallotRequest
from .tasks import send_ballotrequest_notification

logger = logging.getLogger("absentee")

COVER_SHEET_PATH = "absentee/templates/pdf/cover.pdf"


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


def prepare_formdata(region_external_id: int, state_code: str) -> Dict[str, Any]:
    """
    Assembles all the form data we need to fill out an absentee ballot request
    form.
    """
    form_data: Dict[str, Any] = {}

    # find the mailing address and contact info
    contact_info = get_absentee_contact_info(region_external_id)
    form_data["vbm_submission_address"] = contact_info.mailing_address

    if contact_info.email or contact_info.phone:
        contact_info_lines = []
        if contact_info.email:
            contact_info_lines.append(f"Email: {contact_info.email}")
        if contact_info.phone:
            contact_info_lines.append(f"Phone: {contact_info.phone}")

        form_data["vbm_contact_info"] = "\n".join(contact_info_lines)
    else:
        form_data[
            "vbm_contact_info"
        ] = "https://www.usvotefoundation.org/vote/eoddomestic.htm"

    # Find state-specific info
    form_data["vbm_deadline"] = (
        state_text_property(state_code, "vbm_deadline_mail", lower=True)
        or "As soon as possible."
    )

    # If we don't have data, make the most conservative assumption: 55 days before the election
    form_data["vbm_first_day_to_apply"] = (
        state_text_property(state_code, "vbm_first_day_to_apply", lower=True)
        or "At least 55 days before the election."
    )

    return form_data


@statsd.timed("turnout.absentee.absentee_application_pdfgeneration")
def generate_pdf(form_data: Dict[str, Any], state_code: str) -> IO:
    return PDFTemplate(
        [
            PDFTemplateSection(path=COVER_SHEET_PATH, is_form=True),
            PDFTemplateSection(path=f"absentee/templates/pdf/states/{state_code}.pdf"),
        ]
    ).fill(form_data)


def process_ballot_request(ballot_request: BallotRequest,):
    form_data = prepare_formdata(
        ballot_request.region.external_id, ballot_request.state.code
    )

    with generate_pdf(form_data, ballot_request.state.code) as filled_pdf:
        item = StorageItem(
            app=enums.FileType.ABSENTEE_REQUEST_FORM,
            email=ballot_request.email,
            partner=ballot_request.partner,
        )
        item.file.save(
            generate_name(ballot_request.state.code, ballot_request.last_name),
            File(filled_pdf),
            True,
        )

    ballot_request.result_item = item
    ballot_request.save(update_fields=["result_item"])

    send_ballotrequest_notification.delay(ballot_request.pk)

    logger.info(f"New PDF Created: Ballot Request {item.pk}")
