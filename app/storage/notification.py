from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from common.apm import tracer

from .models import StorageItem

NOTIFICATION_TEMPLATE = "storage/email/refresh_notification.html"


@tracer.wrap()
def compile_email(storage_item: StorageItem) -> str:
    recipient = {
        "email": storage_item.email,
    }
    context = {
        "storage_item": storage_item,
        "subscriber": storage_item.subscriber,
        "recipient": recipient,
        "download_url": storage_item.download_url,
    }

    return render_to_string(NOTIFICATION_TEMPLATE, context)


def send_email(storage_item: StorageItem, content: str) -> None:
    from_email = settings.MANAGEMENT_NOTIFICATION_FROM
    if storage_item.subscriber:
        from_email = storage_item.subscriber.full_email_address

    msg = EmailMessage(
        "Your new download link", content, from_email, [storage_item.email],
    )
    msg.content_subtype = "html"
    msg.send()


def trigger_notification(storage_item: StorageItem) -> None:
    content = compile_email(storage_item)
    send_email(storage_item, content)
