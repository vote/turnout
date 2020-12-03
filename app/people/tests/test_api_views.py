from rest_framework.test import APIClient

UNSUB_API_ENDPOINT = "/v1/people/opt-out/"


def test_unsubscribe_email(mocker):
    unsub_phone = mocker.patch("people.api_views.unsubscribe_phone_from_actionnetwork")
    unsub_email = mocker.patch("people.api_views.unsubscribe_email_from_actionnetwork")

    client = APIClient()
    response = client.post(UNSUB_API_ENDPOINT, {"email": "foo@bar.com"})

    assert response.status_code == 200
    unsub_email.delay.assert_called_once_with("foo@bar.com")
    unsub_phone.delay.assert_not_called()


def test_unsubscribe_phone(mocker):
    unsub_phone = mocker.patch("people.api_views.unsubscribe_phone_from_actionnetwork")
    unsub_email = mocker.patch("people.api_views.unsubscribe_email_from_actionnetwork")

    client = APIClient()
    response = client.post(UNSUB_API_ENDPOINT, {"phone": "+19515551212"})

    assert response.status_code == 200
    unsub_email.delay.assert_not_called()
    unsub_phone.delay.assert_called_once_with("(951) 555-1212")


def test_unsubscribe_both(mocker):
    unsub_phone = mocker.patch("people.api_views.unsubscribe_phone_from_actionnetwork")
    unsub_email = mocker.patch("people.api_views.unsubscribe_email_from_actionnetwork")

    client = APIClient()
    response = client.post(
        UNSUB_API_ENDPOINT, {"email": "foo@bar.com", "phone": "+19515551212"}
    )

    assert response.status_code == 200
    unsub_email.delay.assert_called_once_with("foo@bar.com")
    unsub_phone.delay.assert_called_once_with("(951) 555-1212", "foo@bar.com")
