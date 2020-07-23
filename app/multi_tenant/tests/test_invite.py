import pytest
from model_bakery import baker

from accounts.models import Invite, User
from multi_tenant.invite import invite_user


@pytest.mark.django_db
def test_invite_new_user(mocker):
    patched_notification = mocker.patch("multi_tenant.invite.send_invite_notification")
    client = baker.make_recipe("multi_tenant.client")

    assert Invite.objects.count() == 0

    invite_user("test@cool.com", client)

    invite = Invite.objects.first()
    assert invite.email == "test@cool.com"
    assert invite.primary_client == client
    assert invite.clients.count() == 1
    assert invite.clients.first() == client

    patched_notification.delay.assert_called_once_with(invite.pk, client.pk)


@pytest.mark.django_db
def test_invite_new_user_existing_invite(mocker):
    patched_notification = mocker.patch("multi_tenant.invite.send_invite_notification")
    client1 = baker.make_recipe("multi_tenant.client")
    client2 = baker.make_recipe("multi_tenant.client")

    assert Invite.objects.count() == 0
    invite_user("test2@cool.com", client1)

    invite = Invite.objects.first()
    assert invite.email == "test2@cool.com"
    assert invite.primary_client == client1
    assert invite.clients.count() == 1

    invite_user("test2@cool.com", client2)

    assert Invite.objects.count() == 1
    refreshed_invite = Invite.objects.first()
    assert refreshed_invite.primary_client == client2
    assert refreshed_invite.clients.count() == 2

    assert patched_notification.delay.call_count == 1


@pytest.mark.django_db
def test_invite_existing_user(mocker):
    patched_notification = mocker.patch("multi_tenant.invite.send_invite_notification")
    client = baker.make_recipe("multi_tenant.client")
    user = baker.make_recipe("accounts.user")

    assert user.active_client == None
    assert user.clients.count() == 0

    invite_user(user.email, client)

    refreshed_user = User.objects.get(pk=user.pk)

    assert refreshed_user.active_client == client
    assert refreshed_user.clients.count() == 1
    assert refreshed_user.clients.first() == client

    assert not patched_notification.delay.called
