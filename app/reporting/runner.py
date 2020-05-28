import csv
from io import StringIO
from operator import attrgetter
from typing import Any, List, Tuple

from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify
from django.utils.timezone import now

from absentee.models import BallotRequest
from common import enums
from register.models import Registration
from storage.models import StorageItem
from verifier.models import Lookup

from .models import Report

ABSENTEE_FIELDS: List[Tuple[str, str]] = [
    ("uuid", "ID"),
    ("subscriber.name", "Subscriber"),
    ("created_at", "Time Started (UTC)"),
    ("first_name", "First Name"),
    ("middle_name", "Middle Name"),
    ("last_name", "Last Name"),
    ("suffix", "Suffix"),
    ("date_of_birth", "Date of Birth"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("address1", "Address 1"),
    ("address2", "Address 2"),
    ("city", "City"),
    ("zipcode", "Zipcode"),
    ("state_id", "State"),
    ("mailing_address1", "Mailing Address 1"),
    ("mailing_address2", "Mailing Address 2"),
    ("mailing_city", "Mailing City"),
    ("mailing_state_id", "Mailing State"),
    ("mailing_zipcode", "Mailing Zipcode"),
    ("sms_opt_in", "VoteAmerica SMS Opt In"),
    ("sms_opt_in_subscriber", "Subscriber SMS Opt In"),
    ("action.details.finished", "Completed"),
    ("action.details.self_print", "Self Print Created"),
    ("action.details.finished_external_service", "Visited State Website"),
    ("action.details.leo_message_sent", "Submitted to LEO"),
    ("action.details.total_downloads", "Total Self Print Downloads"),
    ("source", "source"),
    ("utm_source", "utm_source"),
    ("utm_medium", "utm_medium"),
    ("utm_campaign", "utm_campaign"),
    ("utm_content", "utm_content"),
    ("utm_term", "utm_term"),
]

REGISTER_FIELDS: List[Tuple[str, str]] = [
    ("uuid", "ID"),
    ("subscriber.name", "Subscriber"),
    ("created_at", "Time Started (UTC)"),
    ("previous_title", "Previous Title"),
    ("previous_first_name", "Previous First Name"),
    ("previous_middle_name", "Previous Middle Name"),
    ("previous_last_name", "Previous Last Name"),
    ("previous_suffix", "Previous Suffix"),
    ("title", "Title"),
    ("first_name", "First Name"),
    ("middle_name", "Middle Name"),
    ("last_name", "Last Name"),
    ("suffix", "Suffix"),
    ("date_of_birth", "Date of Birth"),
    ("gender", "Gender"),
    ("race_ethnicity", "Race-Ethnicity"),
    ("us_citizen", "US Citizen"),
    ("party", "Party"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("address1", "Address 1"),
    ("address2", "Address 2"),
    ("city", "City"),
    ("zipcode", "Zipcode"),
    ("state_id", "State"),
    ("previous_address1", "Previous Address 1"),
    ("previous_address2", "Previous Address 2"),
    ("previous_city", "Previous City"),
    ("previous_state_id", "Previous State"),
    ("previous_zipcode", "Previous Zipcode"),
    ("mailing_address1", "Mailing Address 1"),
    ("mailing_address2", "Mailing Address 2"),
    ("mailing_city", "Mailing City"),
    ("mailing_state_id", "Mailing State"),
    ("mailing_zipcode", "Mailing Zipcode"),
    ("sms_opt_in", "VoteAmerica SMS Opt In"),
    ("sms_opt_in_subscriber", "Subscriber SMS Opt In"),
    ("action.details.finished", "Completed"),
    ("action.details.self_print", "Self Print Created"),
    ("action.details.finished_external_service", "Visited State Website"),
    ("action.details.leo_message_sent", "Submitted to LEO"),
    ("action.details.total_downloads", "Total Self Print Downloads"),
    ("source", "source"),
    ("utm_source", "utm_source"),
    ("utm_medium", "utm_medium"),
    ("utm_campaign", "utm_campaign"),
    ("utm_content", "utm_content"),
    ("utm_term", "utm_term"),
    ("referring_tool", "Referring Tool"),
]

VERIFIER_FIELDS: List[Tuple[str, str]] = [
    ("uuid", "ID"),
    ("subscriber.name", "Subscriber"),
    ("created_at", "Time Started (UTC)"),
    ("first_name", "First Name"),
    ("last_name", "Last Name"),
    ("date_of_birth", "Date of Birth"),
    ("email", "Email"),
    ("phone", "Phone"),
    ("address1", "Address 1"),
    ("address2", "Address 2"),
    ("city", "City"),
    ("zipcode", "Zipcode"),
    ("state_id", "State"),
    ("sms_opt_in", "VoteAmerica SMS Opt In"),
    ("sms_opt_in_subscriber", "Subscriber SMS Opt In"),
    ("registered", "Registered"),
    ("source", "source"),
    ("utm_source", "utm_source"),
    ("utm_medium", "utm_medium"),
    ("utm_campaign", "utm_campaign"),
    ("utm_content", "utm_content"),
    ("utm_term", "utm_term"),
]


def generate_name(report: Report):
    if report.subscriber:
        filename = slugify(
            f'{now().strftime("%Y%m%d%H%M")}_{report.subscriber.slug}_{report.type.label}_export'
        ).lower()
    else:
        filename = slugify(
            f'{now().strftime("%Y%m%d%H%M")}_fullprogram_{report.type.label}_export'
        )
    return f"{filename}.csv"


def report_runner(report: Report):
    model: Any = None
    if report.type == enums.ReportType.ABSENTEE:
        model = BallotRequest
        fields = ABSENTEE_FIELDS
    elif report.type == enums.ReportType.REGISTER:
        model = Registration
        fields = REGISTER_FIELDS
    elif report.type == enums.ReportType.VERIFY:
        model = Lookup
        fields = VERIFIER_FIELDS
    else:
        raise Exception("Invalid Report Type")

    objects = model.objects.select_related(
        "subscriber", "subscriber__default_slug", "action", "action__details"
    ).exclude(action__isnull=True)

    if report.subscriber:
        objects = objects.filter(subscriber=report.subscriber)

    new_file = StringIO()
    reportwriter = csv.writer(new_file)
    reportwriter.writerow([field[1] for field in fields])

    for object in objects:
        new_row = []
        for field in fields:
            new_row.append(attrgetter(field[0])(object))
        reportwriter.writerow(new_row)

    encoded_file_content = new_file.getvalue().encode("utf-8")

    item = StorageItem(
        app=enums.FileType.REPORT,
        email=report.author.email,
        subscriber=report.subscriber,
    )
    item.file.save(
        generate_name(report), ContentFile(encoded_file_content), True,
    )
    report.result_item = item
    report.status = enums.ReportStatus.COMPLETE
    report.save(update_fields=["result_item", "status"])
