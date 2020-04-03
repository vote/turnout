import logging

import sendgrid
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from common.analytics import statsd
from common.apm import tracer

logger = logging.getLogger("mailer")
sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)


@shared_task
@statsd.timed("turnout.mailer.sendgrid_send_task")
def send_sendgrid_mail(key):
    mail = cache.get(key)

    try:
        with tracer.trace("sg.mail.send", service="sendgridclient"):
            sg.client.mail.send.post(request_body=mail)
    except Exception:
        statsd.increment("turnout.mailer.sendgrid_send_task_server_error")
        raise
    finally:
        cache.delete(key)

    extra = {
        "subject": mail["subject"],
        "sent_from": mail["from"]["email"],
        "sent_to": [d["email"] for d in mail["personalizations"][0]["to"]],
    }
    logger.info(
        "Email Sent %(subject)s from %(sent_from)s to %(sent_to)s", extra, extra=extra
    )
    logger.debug(mail)
