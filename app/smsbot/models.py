import logging
import time
import uuid

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import connections, models
from phonenumber_field.modelfields import PhoneNumberField
from requests.exceptions import ConnectionError
from twilio.rest import Client as TwilioClient

from common.apm import tracer
from common.enums import BlastType, MessageDirectionType, SMSDeliveryStatus
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

    @tracer.wrap()
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
    description = models.CharField(max_length=100, null=True)
    content = models.TextField(null=True)
    sql = models.TextField(null=True)
    campaign = models.CharField(max_length=100, null=True)
    blast_type = TurnoutEnumField(BlastType, null=True)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"Blast - {self.description} - {self.blast_type} ({self.uuid})"

    @tracer.wrap()
    def count(self):
        with connections["readonly"].cursor() as cursor:
            cursor.execute(
                f"SELECT count(*) FROM ({self.sql.format(blast_id=str(self.uuid),)}) a"
            )
            return cursor.fetchall()[0][0]

    @tracer.wrap()
    def enqueue(self, test_phone: str = None):
        from .tasks import trigger_blast_sms, trigger_blast_mms_map

        if self.blast_type == BlastType.SMS and test_phone:
            trigger_blast_sms.delay(self.pk, test_phone, force_dup=True)
            return

        with connections["readonly"].cursor() as cursor:
            cursor.execute(self.sql.format(blast_id=str(self.uuid),))
            columns = [col[0] for col in cursor.description]
            if test_phone:
                logger.info(f"Enqueueing test message for {self} to {test_phone}")
            else:
                logger.info(f"Enqueueing {cursor.rowcount} messages for {self}")
            for row in cursor.fetchall():
                r = dict(zip(columns, row))
                if self.blast_type == BlastType.SMS:
                    trigger_blast_sms.delay(self.pk, r["phone"])  # type: ignore
                elif self.blast_type == BlastType.MMS_MAP:
                    if test_phone:
                        trigger_blast_mms_map.delay(
                            self.pk,
                            test_phone,
                            r["map_type"],  # type: ignore
                            r["address_full"],  # type: ignore
                            force_dup=True,
                        )
                    else:
                        trigger_blast_mms_map.delay(
                            self.pk, r["phone"], r["map_type"], r["address_full"]  # type: ignore
                        )
                else:
                    logger.error(
                        f"unrecognized blast_type {self.blast_type} for {self}"
                    )
                if test_phone:
                    break
            if not test_phone:
                logger.info(f"Done enqueueing {cursor.rowcount} messages for {self}")
