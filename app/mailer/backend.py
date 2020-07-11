import json
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.mail.backends.smtp import EmailBackend


class TurnoutBackend(EmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(
            host="smtp.sendgrid.net",
            port=587,
            username="apikey",
            use_tls=True,
            password=settings.SENDGRID_API_KEY,
            timeout=settings.EMAIL_SEND_TIMEOUT,
        )

    def send_messages(self, emails):
        # Add Sendgrid Header
        payload = {
            "unique_args": {
                "env": settings.ENV,
                "build": settings.BUILD,
                "tag": settings.TAG,
            }
        }

        for email in emails:
            email.extra_headers["X-SMTPAPI"] = json.dumps(payload)

        super().send_messages(emails)
