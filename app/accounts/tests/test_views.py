from datetime import timedelta

import pytest
from django.utils.timezone import now
from model_bakery import baker


@pytest.mark.django_db
def test_thanks_visibility(client):
    invite = baker.make("accounts.Invite", expires=now() + timedelta(days=1))
    non_consumed_response = client.get(f"/account/register/{invite.token}/success/")
    assert non_consumed_response.status_code == 404

    invite.user = baker.make("accounts.User")
    invite.save()
    consumed_response = client.get(f"/account/register/{invite.token}/success/")
    assert consumed_response.status_code == 200


@pytest.mark.django_db
def test_expired_post(client):
    invite = baker.make("accounts.Invite", expires=now() - timedelta(days=1))
    assert invite.expired == True
    expired_response = client.post(f"/account/register/{invite.token}/", {})
    assert expired_response.status_code == 404
