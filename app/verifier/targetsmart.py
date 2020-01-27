import logging

import requests
from django.conf import settings

logger = logging.getLogger("verifier")

TARGETSMART_ENDPOINT = "https://api.targetsmart.com/voter/voter-registration-check"


def query_targetsmart(serializer_data):
    query = {
        "first_name": serializer_data["first_name"],
        "last_name": serializer_data["last_name"],
        "state": serializer_data["state"],
        "zip_code": serializer_data["zipcode"],
    }

    # only use year to match date_of_birth as some states have 1/1 for unknown dates
    if "date_of_birth" in serializer_data:
        query["dob"] = serializer_data["date_of_birth"].strftime("%Y**")

    logger.info(query)

    response = requests.get(
        TARGETSMART_ENDPOINT,
        params=query,
        headers={"x-api-key": settings.TARGETSMART_KEY},
    )

    logger.info(response.text)

    if response.status_code != 200:
        logger.error(f"Targetsmart error {response.status_code}: {response.text}")
        return {}

    return response.json()
