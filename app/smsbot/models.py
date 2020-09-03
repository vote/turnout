import logging
import uuid

from django.conf import settings
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from twilio.rest import Client as TwilioClient

from common.apm import tracer
from common.enums import MessageDirectionType, SMSDeliveryStatus
from common.fields import TurnoutEnumField
from common.utils.models import TimestampModel, UUIDModel

logger = logging.getLogger("smsbot")

# we'll get an exception later if there are no twilio creds and turnout tries to send a message
if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
    twilio_client = TwilioClient(
        settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN
    )
else:
    twilio_client = None


class SMSMessage(UUIDModel, TimestampModel):
    phone = models.ForeignKey(
        null=True, on_delete=models.deletion.SET_NULL, to="smsbot.Number"
    )
    direction = TurnoutEnumField(MessageDirectionType)
    message = models.TextField(blank=True, null=True)
    status = TurnoutEnumField(SMSDeliveryStatus, null=True)
    status_time = models.DateTimeField(null=True)
    twilio_sid = models.TextField(null=True, db_index=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"SMSMessage - {self.phone_id} {self.direction}"

    def delivery_status_webhook(self):
        if settings.PRIMARY_ORIGIN.startswith("https"):
            return f"{settings.PRIMARY_ORIGIN}/v1/smsbot/twilio-message-status/{self.uuid}/"
        else:
            # twilio rejects http webhooks
            return None


class Number(TimestampModel):
    # deprecated key from old UUIDModel base class
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    phone = PhoneNumberField(primary_key=True)

    welcome_time = models.DateTimeField(null=True, blank=True)
    opt_out_time = models.DateTimeField(null=True, blank=True)
    opt_in_time = models.DateTimeField(null=True, blank=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Number - {self.phone}"

    def send_sms(self, text, ignore_opt_out=False):
        if self.opt_out_time and not ignore_opt_out:
            return
        if not twilio_client:
            logger.warning(f"No twilio credentials, not sending sms: {text}")
            return
        with tracer.trace("smsbot.number.send_sms", service="twilio"):
            msg = SMSMessage.objects.create(
                phone=self, direction=MessageDirectionType.OUT, message=text,
            )
            r = twilio_client.messages.create(
                to=str(self.phone),
                messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                body=text,
                status_callback=msg.delivery_status_webhook(),
            )
            msg.twilio_sid = r.sid
            msg.save()
