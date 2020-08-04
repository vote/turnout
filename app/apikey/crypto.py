# The API key secrets we provide to users are a combination of the secret
# stored in the DB, and a global salt (aka a "pepper") stored in the Django
# configuration.
#
# We apply this pepper because we sync our database in a couple places for
# analysis and reporting, so we want to provide an extra level of protection
# against a threat model where an attacker has read-only access to a portion of
# our database.

import hashlib
import hmac
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import jwt
from django.conf import settings
from django.utils.encoding import force_str

PEPPER = settings.API_KEY_PEPPER.encode()
JWT_EXPIRATION_LEEWAY_SECONDS = 30
SECRET_KEY = force_str(settings.SECRET_KEY)
JWT_ISSUER = settings.PRIMARY_ORIGIN

logger = logging.getLogger("apikey")


def hash_key_secret(secret: str) -> str:
    return hmac.new(PEPPER, secret.encode(), hashlib.sha256).hexdigest()


def check_key_secret(key_secret: str, given_secret: str) -> bool:
    return hmac.compare_digest(hash_key_secret(key_secret), given_secret)


def make_action_jwt(
    action_id: str, action_type: str, expiration: timedelta
) -> Tuple[str, datetime]:
    exp = datetime.now(tz=timezone.utc) + expiration

    return (
        force_str(
            jwt.encode(
                {
                    "iss": JWT_ISSUER,
                    "exp": exp,
                    "action_type": action_type,
                    "action_id": action_id,
                },
                SECRET_KEY,
                algorithm="HS256",
            )
        ),
        exp,
    )


def verify_action_jwt(token: str, action_type: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            leeway=JWT_EXPIRATION_LEEWAY_SECONDS,
        )
    except jwt.InvalidTokenError as e:
        logger.warn("Invalid token", exc_info=e)
        return None

    if payload.get("action_type", None) != action_type:
        logger.warn(
            f"Mismatched action type: expected {action_type}, got {payload.get('action_type', None)}"
        )
        return None

    return payload["action_id"]
