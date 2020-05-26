from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.analytics import statsd

from .models import Report

NOTIFICATION_TEMPLATE = "reporting/email/report_notification.html"


@statsd.timed("turnout.reporting.compile_email")
def compile_email(report: Report) -> str:

    preheader_text = f"A new {report.type.label} has been successfully generated"
    recipient = {
        "first_name": report.author.first_name,
        "last_name": report.author.last_name,
        "email": report.author.email,
    }
    context = {
        "report": report,
        "subscriber": report.subscriber,
        "recipient": recipient,
        "download_url": report.result_item.download_url,
        "preheader_text": preheader_text,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(report: Report, content: str) -> None:
    msg = EmailMessage(
        f"Your {report.type.label}",
        content,
        report.subscriber.full_email_address,
        [report.author.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(report: Report) -> None:
    content = compile_email(report)
    send_email(report, content)
