from datetime import datetime

import pytest
import pytz
from model_bakery import baker

from election import models, tasks


@pytest.mark.django_db
def test_cron_trigger_no_webhooks_not_called(mocker):
    netlify_trigger = mocker.patch("election.tasks.trigger_netlify")
    tasks.trigger_netlify_if_updates()
    assert not netlify_trigger.apply_async.called


@pytest.mark.django_db
def test_cron_trigger_trigger_not_previously_called(mocker, freezer):
    # We have to use freezer.move_to so that we can set the StateInformation modified_at field
    freezer.move_to("2009-01-20 11:30:00")
    baker.make_recipe("election.markdown_information")
    webhook = baker.make_recipe("election.netlify_webhook", last_triggered=None)
    netlify_trigger = mocker.patch("election.tasks.trigger_netlify")
    tasks.trigger_netlify_if_updates()
    netlify_trigger.apply_async.assert_called_once_with(
        args=(webhook.pk,), expires=3600
    )


@pytest.mark.django_db
def test_cron_trigger_update_older_than_webhook_last_triggered(mocker, freezer):
    freezer.move_to("2009-01-20 10:30:00")
    baker.make_recipe("election.markdown_information")
    baker.make_recipe(
        "election.netlify_webhook", last_triggered="2009-01-20 11:00:00-0000"
    )
    netlify_trigger = mocker.patch("election.tasks.trigger_netlify")
    tasks.trigger_netlify_if_updates()
    assert not netlify_trigger.apply_async.called


@pytest.mark.django_db
def test_cron_trigger_update_newer_than_webhook_last_triggered(mocker, freezer):
    freezer.move_to("2009-01-20 11:30:00")
    baker.make_recipe("election.markdown_information")
    webhook = baker.make_recipe(
        "election.netlify_webhook", last_triggered="2009-01-20 11:00:00-0000"
    )
    netlify_trigger = mocker.patch("election.tasks.trigger_netlify")
    tasks.trigger_netlify_if_updates()
    netlify_trigger.apply_async.assert_called_once_with(
        args=(webhook.pk,), expires=3600
    )


@pytest.mark.django_db
def test_cron_trigger_inactive_webhook(mocker, freezer):
    freezer.move_to("2009-01-20 11:30:00")
    baker.make_recipe("election.markdown_information")
    webhook = baker.make_recipe(
        "election.netlify_webhook", last_triggered=None, active=False
    )
    netlify_trigger = mocker.patch("election.tasks.trigger_netlify")
    tasks.trigger_netlify_if_updates()
    assert not netlify_trigger.apply_async.called


@pytest.mark.django_db
def test_trigger_netlify(requests_mock, freezer):
    freezer.move_to("2009-01-20 12:00:00")
    trigger_request = requests_mock.register_uri(
        "POST", "http://test.local/test_the_call"
    )
    webhook = baker.make_recipe(
        "election.netlify_webhook",
        trigger_url="http://test.local/test_the_call",
        last_triggered="2009-01-20 11:00:00-0000",
    )
    tasks.trigger_netlify(webhook.uuid)
    new_webhook = models.UpdateNotificationWebhook.objects.get(pk=webhook.pk)
    assert new_webhook.last_triggered == datetime(2009, 1, 20, 12, tzinfo=pytz.utc)
    assert trigger_request.last_request.url == "http://test.local/test_the_call"
    assert trigger_request.last_request.body == None
