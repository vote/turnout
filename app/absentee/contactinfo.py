from dataclasses import dataclass
from typing import Optional

from official.models import Address


@dataclass
class AbsenteeContactInfo:
    mailing_address: str
    email: Optional[str]
    phone: Optional[str]


class NoAbsenteeRequestMailingAddress(Exception):
    pass


def absentee_address_score(addr: Address) -> int:
    """
    Returns a "score" for how appropriate it is to talk to this Address about
    absentee ballots.

    1: This is an office that accept absentee ballot forms by mail
    2: This is an office that processes absentee ballot forms
    3: All other offices

    We will only tell users to mail to offices with a score of 1, but we may
    give them contact info for 2's and 3's if there are no 1's with contact
    info.
    """
    if addr.process_absentee_requests and addr.is_regular_mail:
        return 1
    elif addr.process_absentee_requests:
        return 2
    else:
        return 3


def get_absentee_contact_info(region_external_id: int) -> AbsenteeContactInfo:
    office_addresses = sorted(
        Address.objects.filter(office__region__external_id=region_external_id),
        key=absentee_address_score,
    )

    absentee_mailing_addresses = [
        addr for addr in office_addresses if absentee_address_score(addr) == 1
    ]

    if len(absentee_mailing_addresses) == 0:
        raise NoAbsenteeRequestMailingAddress(
            f"No absentee request mailing address for region {region_external_id}"
        )

    absentee_mailing_address = absentee_mailing_addresses[0]
    absentee_mailing_address_str = "\n".join(
        [
            line
            for line in [
                absentee_mailing_address.address,
                absentee_mailing_address.address2,
                absentee_mailing_address.address3,
                f"{absentee_mailing_address.city.title()}, {absentee_mailing_address.state.code} {absentee_mailing_address.zipcode}",
            ]
            if line is not None and len(line) > 0
        ]
    )

    # Find contact info
    email = next((addr.email for addr in office_addresses if addr.email), None)
    phone = next((addr.phone for addr in office_addresses if addr.phone), None)

    return AbsenteeContactInfo(
        mailing_address=absentee_mailing_address_str, email=email, phone=phone
    )
