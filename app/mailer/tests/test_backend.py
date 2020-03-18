from mailer.backend import TurnoutBackend, push_to_sendgrid_task


def test_push_to_sendgrid(mocker, settings):
    settings.EMAIL_SEND_TIMEOUT = 100
    cache = mocker.patch("mailer.backend.cache")
    task = mocker.patch("mailer.backend.send_sendgrid_mail")
    uuid = mocker.patch("mailer.backend.uuid")
    uuid.uuid4.return_value = "abcd123"

    push_to_sendgrid_task({"hey": "yeah"})
    cache.set.assert_called_once_with("email-abcd123", {"hey": "yeah"}, 700)
    task.apply_async.assert_called_once_with(args=("email-abcd123",), expires=100)


def test_compile_message(mocker, settings):
    settings.ENV = "test"
    settings.BUILD = "1000"
    settings.TAG = "100.100.100"
    build_sg = mocker.patch.object(TurnoutBackend, "_build_sg_mail")
    build_sg.return_value = {"custom_args": {"hey": "yeah"}}
    example_email = mocker.Mock()

    backend = TurnoutBackend()
    result = backend.compile_message(example_email)
    assert result["custom_args"] == {
        "env": "test",
        "build": "1000",
        "tag": "100.100.100",
        "hey": "yeah",
    }
    build_sg.assert_called_once_with(example_email)


def test_send_messages(mocker):
    compile_message = mocker.patch.object(TurnoutBackend, "compile_message")
    push_to_task = mocker.patch("mailer.backend.push_to_sendgrid_task")
    example_email = mocker.Mock()
    example_compiled_message = mocker.Mock()
    compile_message.return_value = example_compiled_message

    backend = TurnoutBackend()
    result = backend.send_messages([example_email])
    assert result == 1
    compile_message.assert_called_once_with(example_email)
    push_to_task.assert_called_once_with(example_compiled_message)
