import logging
from typing import Optional

import ovrlib
from django.conf import settings

from common.enums import (
    EventType,
    PoliticalParties,
    RegistrationGender,
    TurnoutActionStatus,
)
from official.match import geocode_to_regions
from official.models import Region
from storage.models import SecureUploadItem

from .models import Registration
from .tasks import send_registration_state_confirmation

logger = logging.getLogger("register")


def pa_fill_region(registration: Registration):
    regions = geocode_to_regions(
        street=registration.address1,
        city=registration.city,
        state="PA",
        zipcode=registration.zipcode,
    )
    if not regions:
        regions = []
        for region in Region.visible.filter(state__code="PA").order_by("name"):
            regions.append(region)
    if not registration.state_api_result:
        registration.state_api_result = {}
    registration.state_api_result["regions"] = [
        {"external_id": region.external_id, "name": region.name,} for region in regions
    ]


def process_pa_registration(
    registration: Registration,
    state_id_number: Optional[str],
    state_id_number_2: Optional[str],
    is_18_or_over: bool,
) -> bool:
    state_fields = registration.state_fields

    # prepare
    r = {
        k: getattr(registration, k)
        for k in [
            "first_name",
            "last_name",
            "address1",
            "address2",
            "city",
            "zipcode",
            "date_of_birth",
            "email",
            "suffix",
            "phone",
            "previous_first_name",
            "previous_middle_name",
            "previous_last_name",
            "previous_city",
            "previous_state",
            "previous_zipcode",
            "mailing_city",
            "mailing_state",
            "mailing_zipcode",
        ]
    }
    if state_id_number:
        r["dl_number"] = state_id_number
    if state_id_number_2:
        r["ssn4"] = state_id_number

    if state_fields.get("signature"):
        upload = SecureUploadItem.objects.get(pk=state_fields.get("signature"))
        r["signature"] = upload.file.read()
        sig_type = upload.content_type.split("/")[1]
        if sig_type == "jpeg":
            sig_type = "jpg"
        r["signature_type"] = sig_type
    elif "dl_number" not in r:
        registration.state_api_result = {
            "status": "failure",
            "error": "no_dl_or_signature",
        }
        return False

    # derive county/city from region
    region = Region.objects.get(external_id=state_fields.get("region_id"))
    if not region:
        registration.state_api_result = {
            "status": "failure",
            "error": "invalid_region_id",
        }
        return False
    if region.name.startswith("City of "):
        r["county"] = region.name[8:]
    elif region.name.endswith(" County"):
        r["county"] = region.name[:-7]
    else:
        registration.state_api_result = {
            "status": "failure",
            "error": "invalid_region_name",
        }
        return False

    # pass through some state_fields
    for k in [
        "mailin_ballot_request",
        "mailin_ballot_to_registration_address",
        "mailin_ballot_to_mailing_address",
        "mailin_ballot_address",
        "mailin_ballot_city",
        "mailin_ballot_state",
        "mailin_ballot_zipcode",
    ]:
        if k in state_fields:
            r[k] = state_fields[k]

    is_new = (
        not registration.previous_address1
        and not registration.previous_first_name
        and not state_fields.get("party_change", False)
    )

    # attempt registration
    def combine_addr(a, b):
        if b is None:
            return a
        return a + " " + b

    if registration.gender in [RegistrationGender.MALE, RegistrationGender.FEMALE]:
        gender = str(registration.gender).lower()
    else:
        gender = "unknown"

    party = str(registration.party)
    if party == PoliticalParties.OTHER:
        party = state_fields.get("party_other")

    session = ovrlib.pa.PAOVRSession(
        api_key=settings.PA_OVR_KEY, staging=settings.PA_OVR_STAGING
    )
    req = ovrlib.pa.PAOVRRequest(
        **r,
        gender=gender,
        party=party,
        mailing_address=combine_addr(
            registration.mailing_address1, registration.mailing_address2
        ),
        previous_address=combine_addr(
            registration.previous_address1, registration.previous_address2
        ),
        federal_voter=state_fields.get("federal_voter", False),
        eighteen_on_election_day=is_18_or_over,
        united_states_citizen=registration.us_citizen,
        declaration=state_fields.get("declaration"),
        is_new=is_new,
    )
    logger.debug(req)
    try:
        res = session.register(req)
        logger.debug(res)
        registration.state_api_result = {
            "status": "success",
            "application_id": res.application_id,
            "signature_source": res.signature_source,
        }
        registration.status = TurnoutActionStatus.PENDING
        registration.action.track_event(EventType.FINISH_EXTERNAL_API)
        send_registration_state_confirmation.delay(registration.pk)
        return True
    except ovrlib.exceptions.InvalidDLError as e:
        registration.state_api_result = {
            "status": "failure",
            "error": "dl_invalid",
            "exception": str(e),
        }
    except ovrlib.exceptions.InvalidSignatureError as e:
        registration.state_api_result = {
            "status": "failure",
            "error": "signature_invalid",
            "exception": str(e),
        }
    except Exception as e:
        logger.warning(f"PA API failure: {str(e)}")
        registration.state_api_result = {
            "status": "failure",
            "error": "unknown_error",
            "exception": str(e),
        }
    if "error" in registration.state_api_result:
        logger.warning(
            "PA OVR status %(status)s, error %(error)s, exception %(exception)s",
            registration.state_api_result,
            extra=registration.state_api_result,
        )
    return False
