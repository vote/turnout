import logging

import requests
from django.conf import settings

logger = logging.getLogger("i90")


CONCEIVE_ENDPOINT = f"{settings.I90_URL}/v1/conceive"
CLAIM_ENDPOINT = f"{settings.I90_URL}/v1/claim"
GET_ENDPOINT = f"{settings.I90_URL}/v1/redirect"


def get_shortened_url(token: str) -> bool:
    response = requests.get(
        f"{GET_ENDPOINT}/{token}", headers={"x-api-key": settings.I90_KEY},
    )
    if response.status_code != 200:
        return None
    return response.json()["destination"]


def shorten_url(url, token=None, app_name="turnout"):
    if token:
        response = requests.post(
            CLAIM_ENDPOINT,
            headers={"x-api-key": settings.I90_KEY, "content-type": "application/json"},
            json={"destination": url, "token": token, "_app_name": app_name},
        )
    else:
        response = requests.post(
            CONCEIVE_ENDPOINT,
            headers={"x-api-key": settings.I90_KEY, "content-type": "application/json"},
            json={"destination": url, "_app_name": app_name},
        )
    if response.status_code != 200:
        logger.error(
            f"Failed to shorten URL, status code {response.status_code}, {response.text}, original URL {url}"
        )
        return url
    return response.json()["short_url"]
