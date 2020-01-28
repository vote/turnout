import logging

import requests
from django.conf import settings

logger = logging.getLogger("verifier")

TARGETSMART_ENDPOINT = "https://api.targetsmart.com/voter/voter-registration-check"


def query_targetsmart(serializer_data):
    # TS is pretty conservative, so we'll only pass in the bare minimum needed for a
    # match.
    query = {
        "first_name": serializer_data["first_name"],
        "last_name": serializer_data["last_name"],
        "state": serializer_data["state"],
        "zip_code": serializer_data["zipcode"],
        # only use year to match date_of_birth as some states have 1/1 for unknown dates
        "dob": serializer_data["date_of_birth"].strftime("%Y**"),
    }

    response = requests.get(
        TARGETSMART_ENDPOINT,
        params=query,
        headers={"x-api-key": settings.TARGETSMART_KEY},
    )

    if response.status_code != 200:
        return {"error": f"HTTP error {response.status_code}: {response.text}"}

    return response.json()
