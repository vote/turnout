import logging
from typing import TYPE_CHECKING

from accounts.models import Invite, User, expire_date_time
from common.apm import tracer

from .tasks import send_invite_notification

if TYPE_CHECKING:
    from multi_tenant.models import Client


logger = logging.getLogger("multi_tenant")


@tracer.wrap()
def invite_user(email: str, subscriber: "Client") -> None:
    try:
        existing_user = User.objects.get(email__iexact=email)
        # If the existing user is client-less, make that user a member of this client
        if existing_user.active_client == None:
            existing_user.active_client = subscriber
        # Add the user to this subscriber
        existing_user.clients.add(subscriber)
        existing_user.save()

        extra = {
            "subscriber_uuid": subscriber.pk,
            "user_uuid": existing_user.pk,
            "email": existing_user.email,
        }
        logger.info(
            "Added %(email)s (existing user %(user_uuid)s) to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )
        return
    except User.DoesNotExist:
        pass

    # Handle a user with a pending invite in the system
    try:
        existing_invite = Invite.actives.get(email__iexact=email)
        existing_invite.clients.add(subscriber)
        existing_invite.primary_client = subscriber
        existing_invite.expires = expire_date_time()
        existing_invite.save()

        extra = {
            "subscriber_uuid": subscriber.pk,
            "email": existing_invite.email,
        }
        logger.info(
            "Re-invited %(email)s to subscriber %(subscriber_uuid)s",
            extra,
            extra=extra,
        )
        return
    except Invite.DoesNotExist:
        pass

    invite = Invite.objects.create(email=email, primary_client=subscriber)
    invite.clients.add(subscriber)

    extra = {
        "subscriber_uuid": subscriber.pk,
        "email": email,
    }
    logger.info(
        "Invited %(email)s to subscriber %(subscriber_uuid)s", extra, extra=extra,
    )

    send_invite_notification.delay(invite.pk, subscriber.pk)
