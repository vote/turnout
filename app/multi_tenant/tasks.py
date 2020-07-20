import datetime
import logging

from celery import shared_task

from common.analytics import statsd

from .models import Client, SubscriptionInterval

logger = logging.getLogger("multi_tenant")


@shared_task
@statsd.timed("turnout.multi_tenant.invite_notification")
def send_invite_notification(invite_pk: str, subscriber_pk: str):
    from accounts.models import Invite
    from .notification import trigger_notification

    invite = Invite.objects.get(pk=invite_pk)
    subscriber = Client.objects.get(pk=subscriber_pk)

    trigger_notification(invite, subscriber)


@shared_task
def check_subscriptions():
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    for client in Client.objects.all():
        if client.active is None:
            # legacy case
            logger.info(
                f"Activating and creating SubscriptionInterval (starting now) for legacy {client}"
            )
            client.active_subscription = SubscriptionInterval.objects.create(
                subscriber=client, begin=now,
            )
            client.active = True
            client.save()
        elif (
            client.active_subscription
            and client.active_subscription.end
            and client.active_subscription.end < now
        ):
            logger.warning(
                f"Deactivating ended subscription ({client.active_subscription}) for {client}"
            )
            client.active_subscription = None
            client.active = False
            client.save()


@shared_task
def approve_lead(lead_id):
    from .leads import approve_lead
    from .models import SubscriberLead

    lead = SubscriberLead.objects.get(uuid=lead_id)
    approve_lead(lead)
