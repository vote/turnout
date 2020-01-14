import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger("verifier")


def audience_cachekey(audience):
    return f"catalist-audience-{audience}"


def fetch_catalist_token(audience=None):
    if not settings.CATALIST_ENABLED:
        raise Exception("Catalist not enabled")

    if not audience:
        audience = settings.CATALIST_AUDIENCE_VERIFY

    body = {
        "client_id": settings.CATALIST_ID,
        "client_secret": settings.CATALIST_SECRET,
        "audience": audience,
        "grant_type": "client_credentials",
    }

    result = requests.post(settings.CATALIST_URL_AUTH_TOKEN, json=body)

    if result.status_code != 200 or "access_token" not in result.json():
        logger.error(f"Error requesting Catalist access token: {result.text}")
        raise Exception(f"Error requesting Catalist access token: {result.text}")
    else:
        token = result.json().get("access_token")
        logger.info("Catalist access token acquired")
        return token


def catalist_token(audience=None):
    from .tasks import sync_catalist_token

    if not audience:
        audience = settings.CATALIST_AUDIENCE_VERIFY

    token = cache.get(audience_cachekey(audience))

    if not token:
        token = sync_catalist_token(return_token=True)

    return token
