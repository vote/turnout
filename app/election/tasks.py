import logging

import requests
from celery import shared_task
from django.db.models import Q
from django.utils.timezone import now

from common.analytics import statsd
from common.enums import NotificationWebhookTypes

from .models import StateInformation, UpdateNotificationWebhook

logger = logging.getLogger("election")


@shared_task
@statsd.timed("turnout.election.trigger_netlify_webhook")
def trigger_netlify(webhook_pk):
    webhook = UpdateNotificationWebhook.objects.get(pk=webhook_pk)
    result = requests.post(webhook.trigger_url, data={})
    logger.info(f"Netlify Trigger: {webhook} triggered, status {result.status_code}")
    webhook.last_triggered = now()
    webhook.save()


@shared_task
@statsd.timed("turnout.election.check_for_updates_cron")
def trigger_netlify_if_updates():
    if not StateInformation.objects.exists():
        logger.info("Netlify Trigger: State Information API Empty")
        return

    last_updated = StateInformation.objects.latest("modified_at").modified_at

    logger.info(f"Netlify Trigger: Last Updated {last_updated}")

    todo_webhooks = UpdateNotificationWebhook.objects.filter(
        active=True, type=NotificationWebhookTypes.NETLIFY,
    ).filter(Q(last_triggered__isnull=True) | Q(last_triggered__lte=last_updated))

    logger.info(
        f"Netlify Trigger: Found {todo_webhooks.count()} Netlify webhooks to trigger"
    )

    timeout = 60 * 60
    for webhook in todo_webhooks:
        res = trigger_netlify.apply_async(args=(webhook.pk,), expires=timeout)


@shared_task
def publish_external_tool_redirects():
    from .external_redirects import publish

    publish()
