import logging

import requests
from django.conf import settings

from common.apm import tracer

logger = logging.getLogger("verifier")

ALLOY_ENDPOINT = "https://api.alloy.us/v1/verify"

ALLOY_STATES_QUARTERLY = ["AL", "CA", "DC", "IN", "KY", "MN", "SC"]
ALLOY_STATES_MONTHLY = [
    "AK",
    "AZ",
    "AR",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "ID",
    "KS",
    "LA",
    "MD",
    "MI",
    "MS",
    "MO",
    "NE",
    "NJ",
    "NM",
    "NY",
    "OK",
    "OR",
    "RI",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "WV",
    "WI",
    "WY",
]
ALLOY_STATES_WEEKLY = ["IA", "MT", "NV", "NC", "OH", "PA", "WA"]
ALLOY_STATES_ENABLED = ALLOY_STATES_MONTHLY + ALLOY_STATES_WEEKLY
# update frequencies per https://alloy.us/verify/details/


def query_alloy(serializer_data):
    address2 = serializer_data.get("address2", "")
    address_line = f"{serializer_data['address1']} {address2}".strip()

    query = {
        "first_name": serializer_data["first_name"],
        "last_name": serializer_data["last_name"],
        "address": address_line,
        "city": serializer_data["city"],
        "state": serializer_data["state"],
        "zip": serializer_data["zipcode"],
        # need full DOB here YYYY-MM-DD
        "birth_date": serializer_data["date_of_birth"].strftime("%Y-%m-%d"),
    }

    with tracer.trace("alloy.verify", service="alloyapi"):
        response = requests.get(
            ALLOY_ENDPOINT,
            params=query,
            auth=requests.auth.HTTPBasicAuth(settings.ALLOY_KEY, settings.ALLOY_SECRET),
        )

    if response.status_code != 200:
        return {"error": f"HTTP error {response.status_code}: {response.text}"}

    return response.json()
