import logging
import time
import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from requests.exceptions import ConnectionError
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
    kwargs = JSONField(null=True)
    blast = models.ForeignKey(
        null=True, on_delete=models.deletion.SET_NULL, to="smsbot.Blast"
    )

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

    def send_sms(self, text, ignore_opt_out=False, blast=None, **kwargs):
        if self.opt_out_time and not ignore_opt_out:
            return
        if not twilio_client:
            logger.warning(f"No twilio credentials, not sending sms: {text}")
            return
        with tracer.trace("smsbot.number.send_sms", service="twilio"):
            msg = SMSMessage.objects.create(
                phone=self,
                direction=MessageDirectionType.OUT,
                message=text,
                blast=blast,
                kwargs=kwargs,
            )
            max_tries = 2
            tries = 0
            while True:
                tries += 1
                if tries > max_tries:
                    logger.warning(
                        f"Gave up sending to twilio after {max_tries} tries: {msg}"
                    )
                    break
                try:
                    r = twilio_client.messages.create(
                        to=str(self.phone),
                        messaging_service_sid=settings.TWILIO_MESSAGING_SERVICE_SID,
                        body=text,
                        status_callback=msg.delivery_status_webhook(),
                        **kwargs,
                    )
                    msg.twilio_sid = r.sid
                    msg.save()
                    break
                except ConnectionError as e:
                    logger.info(
                        f"Failed to send via twilio (attempt {tries}): {e} ({msg})"
                    )
                    time.sleep(tries)


class Blast(TimestampModel, UUIDModel):
    description = models.TextField(null=True)
    content = models.TextField(null=True)
    sql = models.TextField(null=True)
    campaign = models.TextField(null=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Blast - {self.description} ({self.uuid})"

    def enqueue_sms_blast(self, limit: int = None):
        from .tasks import trigger_blast_sms

        logger.info(f"Enqueueing {self}")
        num = 0
        for n in Number.objects.raw(self.sql)[0:limit]:
            trigger_blast_sms.delay(str(n.pk), self.pk)
            num += 1
        logger.info(f"Enqueued {self} with {num} messages")

    def enqueue_voter_map_mms_blast(self, destination: str, limit: int = None):
        from voter.models import Voter
        from .tasks import trigger_voter_map_mms

        logger.info(f"Enqueueing {self}")
        num = 0
        for voter in Voter.objects.raw(self.sql)[0:limit]:
            trigger_voter_map_mms.delay(voter.uuid, self.uuid, destination)
            num += 1
        logger.info(f"Enqueued {self} with {num} messages")
