import logging

import sendgrid
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from common.analytics import statsd

logger = logging.getLogger("mailer")
sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


@shared_task
@statsd.timed("turnout.mailer.sendgrid_send_task")
def send_sendgrid_mail(key):
    mail = cache.get(key)

    try:
        sg.client.mail.send.post(request_body=mail)
    except Exception:
        statsd.increment("turnout.mailer.sendgrid_send_task_server_error")
        raise
    finally:
        cache.delete(key)

    subject = mail["subject"]
    sent_from = mail["from"]["email"]
    sent_to = mail["personalizations"][0]["to"]
    logger.info(f"Email Sent {subject} from {sent_from} to {sent_to}")
    logger.debug(mail)
