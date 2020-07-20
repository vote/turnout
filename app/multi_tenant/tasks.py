from celery import shared_task

from common.analytics import statsd


@shared_task
@statsd.timed("turnout.multi_tenant.invite_notification")
def send_invite_notification(invite_pk: str, subscriber_pk: str):
    from accounts.models import Invite
    from .notification import trigger_notification

    invite = Invite.objects.get(pk=invite_pk)
    subscriber = Client.objects.get(pk=subscriber_pk)

    trigger_notification(invite, subscriber)
