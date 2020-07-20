import datetime
import logging

from accounts.models import Invite, User, expire_date_time
from common import enums

from .models import Client, SubscriberSlug, SubscriptionInterval
from .tasks import send_invite_notification

logger = logging.getLogger("multi_tenant")


def approve_lead(lead):
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    client = Client.objects.create(
        name=lead.name, url=lead.url, email=lead.email, active=True,
    )
    slug = SubscriberSlug.objects.create(slug=lead.slug, subscriber=client,)
    sub = SubscriptionInterval.objects.create(subscriber=client, begin=now,)
    client.default_slug = slug
    client.active_subscription = sub
    client.save()

    lead.subscriber = client
    lead.status = enums.SubscriberLeadStatus.APPROVED
    lead.save()
    logger.info(f"Created subscriber {client} from lead {lead}")

    # send invite
    try:
        existing_user = User.objects.get(email__iexact=lead.email)
        # If the existing user is client-less, make that user a member of this client
        if existing_user.active_client == None:
            existing_user.active_client = client
        # Add the user to this subscriber
        existing_user.clients.add(client)
        existing_user.save()

        extra = {
            "subscriber_uuid": client.pk,
            "user_uuid": existing_user.pk,
            "lead_uuid": lead.pk,
        }
        logger.info(
            "User Management: Approved lead %(lead_uuid), added %(user_uuid)s to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )

        # send email?

        return
    except User.DoesNotExist:
        pass

    # Handle a user with a pending invite in the system
    existing_invite = Invite.actives.filter(email__iexact=lead.email).first()
    if existing_invite:
        # Add the current subscriber. This will automatically dedupe
        existing_invite.clients.add(client)
        # Change the invite's primary subscriber to the current one.
        existing_invite.primary_client = client
        # Reset the expiration time
        existing_invite.expires = expire_date_time()
        existing_invite.save()

        extra = {
            "subscriber_uuid": client.pk,
            "invitee_email": existing_invite.email,
            "lead_uuid": lead.pk,
        }
        logger.info(
            "User Management: Lead %(lead_uuid)s approve, re-invited %(invitee_email)s to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )

        # send email?

        return

    # new user invite
    invite = Invite.objects.create(email=lead.email, primary_client=client,)
    invite.clients.add(client)
    invite.save()

    extra = {
        "subscriber_uuid": client.pk,
        "invitee_email": lead.email,
        "lead_uuid": lead.pk,
    }
    logger.info(
        "User Management: Lead %(lead_uuid)s approved, invited %(invitee_email)s to subscriber %(subscriber_uuid)s",
        extra,
        extra=extra,
    )

    send_invite_notification.delay(invite.pk, client.pk)


def deny_lead(lead):
    if lead.status in [
        enums.SubscriberLeadStatus.PENDING_C3_VERIFICATION,
        enums.SubscriberLeadStatus.PENDING_PAYMENT,
    ]:
        lead.status = enums.SubscriberLeadStatus.DENIED
        lead.save()
