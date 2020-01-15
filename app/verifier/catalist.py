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
        audience = settings.CATALIST_AUDIENCE_MATCH

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
        audience = settings.CATALIST_AUDIENCE_MATCH

    token = cache.get(audience_cachekey(audience))

    if not token:
        logger.info("Catalist token not found in cache")
        token = sync_catalist_token(return_token=True)

    return token


def catalist_match(search_data):
    search_data["token"] = catalist_token(audience=settings.CATALIST_AUDIENCE_MATCH)
    return requests.get(settings.CATALIST_URL_API_MATCH, params=search_data)


def query_catalist(serializer_data):
    logger.info(serializer_data)
    query = {
        "first": serializer_data["first_name"],
        "last": serializer_data["last_name"],
        "state": serializer_data["state"],
        "zip": serializer_data["zipcode"],
    }

    if "middle" in serializer_data:
        query["middle"] = serializer_data["middle"]

    if "gender" in serializer_data:
        query["gender"] = serializer_data["gender"].value

    if "date_of_birth" in serializer_data:
        query["birthdate"] = serializer_data["date_of_birth"].strftime("%Y%m%d")

    if "address1" in serializer_data:
        query[
            "address"
        ] = f"{serializer_data.get('address1', '')} {serializer_data.get('address2', '')}".strip()

    if "city" in serializer_data:
        query["city"] = serializer_data["city"]

    if "county" in serializer_data:
        query["county"] = serializer_data["county"]

    if "phone" in serializer_data:
        query["phone"] = serializer_data["phone"].as_e164[2:]

    if "email" in serializer_data:
        query["email"] = serializer_data["email"]

    logger.info(query)

    response = catalist_match(query)

    logger.info(response.text)

    if response.status_code != 200:
        logger.error(f"Catalist error {response.status_code}: {response.text}")
        return {}

    return response.json()
