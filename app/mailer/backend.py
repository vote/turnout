import uuid

from django.conf import settings
from django.core.cache import cache
from sendgrid_backend import SendgridBackend

from .tasks import send_sendgrid_mail


def push_to_sendgrid_task(message):
    key = f"email-{uuid.uuid4()}"
    # add a 600 second padding so the item never expires before the task is run,
    # even if there is a clock drift somewhere
    cache.set(key, message, settings.EMAIL_SEND_TIMEOUT + 600)
    send_sendgrid_mail.apply_async(args=(key,), expires=settings.EMAIL_SEND_TIMEOUT)


class TurnoutBackend(SendgridBackend):
    def __init__(self, *args, **kwargs):
        kwargs["api_key"] = settings.SENDGRID_API_KEY
        super().__init__(*args, **kwargs)

    def compile_message(self, email):
        mail = self._build_sg_mail(email)
        args_from_settings = {
            "env": settings.ENV,
            "build": settings.BUILD,
            "tag": settings.TAG,
        }
        mail["custom_args"] = {**args_from_settings, **mail.get("custom_args", {})}
        return mail

    def send_messages(self, emails):
        count = 0
        for email in emails:
            push_to_sendgrid_task(self.compile_message(email))
            count += 1
        return count
