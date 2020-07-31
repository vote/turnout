from datetime import datetime, timedelta, timezone

import jwt as jwtlib
from django.utils.encoding import force_str

from apikey.crypto import JWT_ISSUER, make_action_jwt, verify_action_jwt


def test_jwt(freezer):
    freezer.move_to("2009-01-20T11:30:00Z")
    jwt, exp = make_action_jwt(
        action_id="someid", action_type="sometype", expiration=timedelta(hours=1)
    )

    assert exp == datetime(2009, 1, 20, 12, 30, 0, tzinfo=timezone.utc)

    assert verify_action_jwt(jwt, action_type="sometype") == "someid"


def test_jwt_bad_iss(mocker):
    jwt, _ = make_action_jwt(
        action_id="someid", action_type="sometype", expiration=timedelta(hours=1)
    )

    mocker.patch("apikey.crypto.JWT_ISSUER", "different")

    assert verify_action_jwt(jwt, action_type="sometype") == None


def test_jwt_expired():
    jwt, _ = make_action_jwt(
        action_id="someid", action_type="sometype", expiration=timedelta(hours=-1)
    )

    assert verify_action_jwt(jwt, action_type="sometype") == None


def test_jwt_bad_action_type():
    jwt, _ = make_action_jwt(
        action_id="someid", action_type="sometype", expiration=timedelta(hours=1)
    )

    assert verify_action_jwt(jwt, action_type="different") == None


def test_jwt_bad_secret(mocker):
    jwt, _ = make_action_jwt(
        action_id="someid", action_type="sometype", expiration=timedelta(hours=1)
    )

    mocker.patch("apikey.crypto.SECRET_KEY", "different")

    assert verify_action_jwt(jwt, action_type="sometype") == None


def test_jwt_unsigned():
    jwt = force_str(
        jwtlib.encode(
            {
                "iss": JWT_ISSUER,
                "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
                "action_type": "sometype",
                "action_id": "someid",
            },
            None,
            algorithm=None,
        )
    )

    assert verify_action_jwt(jwt, action_type="sometype") == None
