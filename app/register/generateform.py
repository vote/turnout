import datetime
import logging

from django.forms.models import model_to_dict
from django.template.defaultfilters import slugify
from pdf_template import PDFTemplate, PDFTemplateSection

from common import enums
from common.apm import tracer
from common.models import DelayedTask
from common.pdf.pdftemplate import fill_pdf_template
from election.models import StateInformation
from storage.models import StorageItem

from .contactinfo import get_registration_contact_info
from .models import Registration
from .tasks import send_registration_notification

logger = logging.getLogger("register")


TEMPLATE_PATH = "register/templates/pdf/eac-nvra.pdf"
COVER_SHEET_PATH = "register/templates/pdf/cover.pdf"
PRINT_AND_FORWARD_COVER_SHEET_PATH = (
    "register/templates/pdf/print-and-forward-cover.pdf"
)

PDF_TEMPLATE = PDFTemplate(
    [
        PDFTemplateSection(path=COVER_SHEET_PATH, is_form=True),
        PDFTemplateSection(path=TEMPLATE_PATH, is_form=True, flatten_form=False),
    ]
)

PRINT_AND_FORWARD_PDF_TEMPLATE = PDFTemplate(
    [
        PDFTemplateSection(
            path=PRINT_AND_FORWARD_COVER_SHEET_PATH, is_form=True, flatten_form=True
        ),
        PDFTemplateSection(path=TEMPLATE_PATH, is_form=True, flatten_form=True),
    ]
)


def generate_name(registration, suffix=""):
    n = f"{registration.state.code} {registration.last_name} registrationform"
    if suffix:
        n += " {suffix}"
    filename = slugify(n).lower()
    return f"{filename}.pdf"


@tracer.wrap()
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

    # remove race_ethnicity, except for states which request it explicitly
    if registration.state.code not in ["AL", "FL", "GA", "NC", "PA", "SC"]:
        form_data["race_ethnicity"] = None

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

    # get mailto address from the region, falling back to the statewide address
    contact_info = get_registration_contact_info(registration)
    mailto_address = contact_info.address

    # split by linebreaks, because each line is a separate field in the PDF
    for num, line in enumerate(mailto_address.splitlines()):
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


@tracer.wrap()
def queue_registration_reminder(registration: Registration) -> None:
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
        when, "register.tasks.send_registration_reminder", str(registration.uuid),
    )


@tracer.wrap()
def process_registration(registration, state_id_number, is_18_or_over):
    form_data = extract_formdata(registration, state_id_number, is_18_or_over)

    if registration.request_mailing_address1:
        # print-and-forward, too!
        mail_item = StorageItem(
            app=enums.FileType.REGISTRATION_FORM,
            email=registration.email,
            subscriber=registration.subscriber,
        )
        fill_pdf_template(
            PRINT_AND_FORWARD_PDF_TEMPLATE,
            form_data,
            mail_item,
            generate_name(registration, "mail"),
        )
        registration.result_item_mail = mail_item

    item = StorageItem(
        app=enums.FileType.REGISTRATION_FORM,
        email=registration.email,
        subscriber=registration.subscriber,
    )

    fill_pdf_template(PDF_TEMPLATE, form_data, item, generate_name(registration))

    registration.result_item = item
    registration.save(update_fields=["result_item", "result_item_mail"])

    send_registration_notification.delay(registration.pk)

    queue_registration_reminder(registration)

    logger.info(f"New PDF Created: Registration {item.pk}")
