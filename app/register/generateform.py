import io
import logging

from django.core.files import File
from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify

from common import enums
from common.analytics import statsd
from common.pdf import fill_form, join_files
from election.models import StateInformation
from storage.models import StorageItem

logger = logging.getLogger("register")


TEMPLATE_PATH = "register/templates/pdf/eac-nvra.pdf"
COVER_SHEET_PATH = "register/templates/pdf/cover.pdf"


def generate_name(registration):
    filename = slugify(
        f"{registration.state.code} {registration.last_name} registrationform"
    ).lower()
    return f"{filename}.pdf"


@statsd.timed("turnout.register.registration_submission_pdfgeneration")
def generate_pdf(form_data):
    # open file objects
    template_pdf = open(TEMPLATE_PATH, "rb")
    cover_pdf = open(COVER_SHEET_PATH, "rb")
    joined_pdf = io.BytesIO()
    filled_pdf = io.BytesIO()

    # join cover pages
    join_files([cover_pdf, template_pdf], joined_pdf)

    # reset buffer on joined_pdf
    joined_pdf.seek(0)

    # fill from dict
    fill_form(joined_pdf, filled_pdf, form_data)

    # Close files
    template_pdf.close()
    cover_pdf.close()
    joined_pdf.close()

    return filled_pdf


def extract_formdata(registration, state_id_number, is_18_or_over):
    # convert Registration to dict
    form_data = model_to_dict(registration)

    # some fields need to be converted to string representation
    # state, date_of_birth, enums
    form_data["state"] = registration.state.code
    if registration.previous_state:
        form_data["previous_state"] = registration.previous_state.code
    if registration.mailing_state:
        form_data["mailing_state"] = registration.mailing_state.code
    form_data["date_of_birth"] = registration.date_of_birth.strftime("%m/%d/%Y")
    form_data["is_18_or_over"] = is_18_or_over
    form_data["state_id_number"] = state_id_number

    if registration.title:
        title_field = registration.title.value.lower()
        form_data[f"title_{title_field}"] = True
    if registration.previous_title:
        title_field = registration.previous_title.value.lower()
        form_data[f"previous_title_{title_field}"] = True

    if registration.suffix:
        suffix_field = registration.suffix.replace(".", "").lower()
        form_data[f"suffix_{suffix_field}"] = True
    if registration.previous_suffix:
        suffix_field = registration.previous_suffix.replace(".", "").lower()
        form_data[f"previous_suffix_{suffix_field}"] = True

    # get mailto address from StateInformation
    # later this will be more complicated...
    try:
        state_mailto_address = (
            StateInformation.objects.only("field_type", "text")
            .get(
                state=registration.state,
                field_type__slug="registration_nvrf_submission_address",
            )
            .text
        )
    except StateInformation.DoesNotExist:
        state_mailto_address = ""
    # split by linebreaks, because each line is a separate field in the PDF
    for num, line in enumerate(state_mailto_address.splitlines()):
        form_data[f"mailto_line_{num+1}"] = line

    # get mailing deadline from StateInformation
    try:
        state_mail_deadline = (
            StateInformation.objects.only("field_type", "text")
            .get(
                state=registration.state, field_type__slug="registration_deadline_mail",
            )
            .text.lower()
        )
        if state_mail_deadline.split()[0] in ["postmarked", "received"]:
            state_deadline = f"Your form must be {state_mail_deadline}."
        else:
            state_deadline = f"Your form must arrive by {state_mail_deadline}."
    except StateInformation.DoesNotExist:
        state_deadline = "Mail your form as soon as possible."
    form_data["state_deadlines"] = state_deadline

    return form_data


def process_registration(registration, state_id_number, is_18_or_over):
    form_data = extract_formdata(registration, state_id_number, is_18_or_over)

    filled_pdf = generate_pdf(form_data)
    item = StorageItem(
        app=enums.FileType.REGISTRATION_FORM,
        email=registration.email,
        partner=registration.partner,
    )
    item.file.save(generate_name(registration), File(filled_pdf), True)

    registration.result_item = item
    registration.save(update_fields=["result_item"])

    logger.info(f"New PDF Created: Registration {item.pk}")

    # close file
    filled_pdf.close()
