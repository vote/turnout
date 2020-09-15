import logging

import requests
from django.conf import settings

from common.apm import tracer
from common.utils.format import remove_special_characters

# targetsmart says they only allow alphanumerics, but we should still include address punctuation
# they will throw an error if we include parentheses or apostrophes


logger = logging.getLogger("verifier")

TARGETSMART_ENDPOINT = "https://api.targetsmart.com/voter/voter-registration-check"


def get_session():
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

    session = requests.Session()
    session.headers["x-api-key"] = settings.TARGETSMART_KEY
    session.mount(
        "https://",
        HTTPAdapter(
            max_retries=Retry(
                total=1,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
                method_whitelist=["HEAD", "GET"],
            )
        ),
    )
    return session


def query_targetsmart(serializer_data):
    # TS is pretty conservative, so we'll only pass in the bare minimum needed for a
    # match.
    address2 = serializer_data.get("address2", "")
    address_line = f'{serializer_data["address1"]} {address2}'.strip()
    full_address = (
        f'{address_line}, {serializer_data["city"]}, {serializer_data["state"]} '
        f'{serializer_data["zipcode"]}'
    )

    query = {
        "first_name": remove_special_characters(serializer_data["first_name"]),
        "last_name": remove_special_characters(serializer_data["last_name"]),
        "state": serializer_data["state"],
        "zip_code": serializer_data["zipcode"],
        "unparsed_full_address": remove_special_characters(full_address),
        # only use year to match date_of_birth as some states have 1/1 for unknown dates
        "dob": serializer_data["date_of_birth"].strftime("%Y*"),
    }

    session = get_session()
    with tracer.trace("ts.registration_check", service="targetsmartapi"):
        response = session.get(TARGETSMART_ENDPOINT, params=query,)

    if response.status_code != 200:
        return {"error": f"HTTP error {response.status_code}: {response.text}"}

    return response.json()
