from dataclasses import asdict, dataclass
from typing import Optional

from official.models import Address


@dataclass
class AbsenteeContactInfo:
    address1: str
    city: str
    state: str
    zipcode: str
    address2: Optional[str] = None
    address3: Optional[str] = None
    full_address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def asdict(self):
        return asdict(self)


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

    absentee_mailing_addresses = [addr for addr in office_addresses]

    if len(absentee_mailing_addresses) == 0:
        raise NoAbsenteeRequestMailingAddress(
            f"No absentee request mailing address for region {region_external_id}"
        )

    # use first matching mailable address which processes absentee ballots
    absentee_mailing_address = absentee_mailing_addresses[0]

    # Find contact info
    email = next((addr.email for addr in office_addresses if addr.email), None)
    phone = next((addr.phone for addr in office_addresses if addr.phone), None)
    city = (
        absentee_mailing_address.city.title() if absentee_mailing_address.city else None
    )
    state = (
        absentee_mailing_address.state.code if absentee_mailing_address.state else None
    )

    return AbsenteeContactInfo(
        full_address=absentee_mailing_address.full_address,
        address1=absentee_mailing_address.address,
        address2=absentee_mailing_address.address2,
        address3=absentee_mailing_address.address3,
        city=city,
        state=state,
        zipcode=absentee_mailing_address.zipcode,
        email=email,
        phone=phone,
    )
