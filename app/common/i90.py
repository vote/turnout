import logging

import requests
from django.conf import settings

logger = logging.getLogger("i90")


POST_ENDPOINT = f"{settings.I90_URL}/v1/conceive"


def shorten_url(url, app_name="turnout"):
    response = requests.post(
        POST_ENDPOINT,
        headers={"x-api-key": settings.I90_KEY, "content-type": "application/json"},
        json={"destination": url, "_app_name": app_name},
    )
    if response.status_code != 200:
        logger.error(
            f"Failed to shorten URL, status code {response.status_code}, {response.text}, original URL {url}"
        )
        return url
    return response.json()["short_url"]
