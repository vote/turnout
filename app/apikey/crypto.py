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

from django.conf import settings

PEPPER = settings.API_KEY_PEPPER.encode()


def hash_key_secret(secret: str) -> str:
    return hmac.new(PEPPER, secret.encode(), hashlib.sha256).hexdigest()


def check_key_secret(key_secret: str, given_secret: str) -> bool:
    return hmac.compare_digest(hash_key_secret(key_secret), given_secret)
