import pytest

from mailer.tasks import send_sendgrid_mail

TEST_MAIL = {
    "from": {"name": "Abraham", "email": "abraham@turnout.local"},
    "subject": "Vital Message",
    "personalizations": [
        {
            "to": [{"name": "Richard", "email": "richard@turnout.local"}],
            "subject": "Vital Message",
        }
    ],
    "content": [{"type": "text/plain", "value": "Here is the message"}],
    "mail_settings": {"sandbox_mode": {"enable": False}},
    "tracking_settings": {
        "click_tracking": {"enable": True, "enable_text": True},
        "open_tracking": {"enable": True},
    },
}


def test_sendgrid_mail(mocker):
    cache = mocker.patch("mailer.tasks.cache")
    sendgrid_client = mocker.patch("mailer.tasks.sg")

    cache.get.return_value = TEST_MAIL
    send_sendgrid_mail("abcd123")
    sendgrid_client.client.mail.send.post.assert_called_once_with(
        request_body=TEST_MAIL
    )
    cache.get.assert_called_once_with("abcd123")
    cache.delete.assert_called_once_with("abcd123")


def test_sendgrid_exception(mocker):
    cache = mocker.patch("mailer.tasks.cache")
    sendgrid_client = mocker.patch("mailer.tasks.sg")

    cache.get.return_value = TEST_MAIL
    sendgrid_client.client.mail.send.post.side_effect = Exception()

    with pytest.raises(Exception):
        send_sendgrid_mail("efgh456")
    sendgrid_client.client.mail.send.post.assert_called_once_with(
        request_body=TEST_MAIL
    )
    cache.get.assert_called_once_with("efgh456")
    cache.delete.assert_called_once_with("efgh456")
