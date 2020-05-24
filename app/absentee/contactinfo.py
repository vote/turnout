from dataclasses import asdict, dataclass
from typing import Optional

from official.models import Address

from .models import LeoContactOverride


@dataclass
class AbsenteeContactInfo:
    address: Optional[Address] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None

    @property
    def full_address(self):
        return self.address.full_address if self.address else None

    @property
    def address1(self):
        return self.address.address if self.address else None

    @property
    def address2(self):
        return self.address.address2 if self.address else None

    @property
    def address3(self):
        return self.address.address3 if self.address else None

    @property
    def city_state_zip(self):
        return (
            f"{self.address.city.title()}, {self.address.state.code} {self.address.zipcode}"
            if self.address
            else None
        )


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
    contact_info = AbsenteeContactInfo()

    try:
        override = LeoContactOverride.objects.get(pk=region_external_id)
        contact_info.email = override.email
        contact_info.fax = override.fax
        contact_info.phone = override.phone
    except LeoContactOverride.DoesNotExist:
        pass

    office_addresses = sorted(
        Address.objects.filter(office__region__external_id=region_external_id),
        key=absentee_address_score,
    )

    # Find contact info
    contact_info.address = next((addr for addr in office_addresses), None)

    if contact_info.email is None:
        contact_info.email = next(
            (addr.email for addr in office_addresses if addr.email), None
        )

    if contact_info.phone is None:
        contact_info.phone = next(
            (addr.phone for addr in office_addresses if addr.phone), None
        )

    if contact_info.fax is None:
        contact_info.fax = next(
            (addr.fax for addr in office_addresses if addr.fax), None
        )

    return contact_info
