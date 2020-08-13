import logging

import requests
from celery import shared_task
from django.conf import settings

from mailer.retry import EMAIL_RETRY_PROPS

from .notifications import trigger_rejection_notification, trigger_welcome_notification

logger = logging.getLogger("subscription")


@shared_task(**EMAIL_RETRY_PROPS)
def send_organization_welcome_notification(
    subscriber_pk: str, initial_user_email: str
) -> None:
    from multi_tenant.models import Client

    subscriber = Client.objects.get(pk=subscriber_pk)
    trigger_welcome_notification(subscriber, initial_user_email)


@shared_task(**EMAIL_RETRY_PROPS)
def send_organization_rejection_notification(email: str, reason: str) -> None:
    trigger_rejection_notification(email, reason)


@shared_task
def notify_slack_interest(interest_pk: str) -> None:
    from .models import Interest

    interest = Interest.objects.get(uuid=interest_pk)
    if settings.SLACK_SUBSCRIBER_INTEREST_ENABLED:
        try:
            message = f"New subscription interest: {interest.organization_name} {interest.website} ({interest.first_name} {interest.last_name} <{interest.email}>)"
            if interest.nonprofit:
                message += " (Non-profit)"
            r = requests.post(
                settings.SLACK_SUBSCRIBER_INTEREST_WEBHOOK, json={"text": message},
            )
            r.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to post warning to slack webhook: {e}")
