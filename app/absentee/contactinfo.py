from dataclasses import dataclass
from typing import Optional

from common import enums
from official.models import Address

from .models import LeoContactOverride


@dataclass
class AbsenteeContactInfo:
    address: Optional[Address] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    submission_method_override: Optional[enums.SubmissionType] = None

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
    Returns a "score" for selecting the optimal address to tell the user to
    contact for questions about their absentee ballot.

    1: This is an office that accept absentee ballot forms and is a physical address
    2: This is an office that processes absentee ballot forms
    3: All other offices

    We prioritize physical addresses over mailing addresses because the physical
    offices can always receive mail, and some kinds of mail (USPS express) can
    only be delivered to the physical addresses (the mailing addresses are
    typically PO boxes).
    """
    if addr.process_absentee_requests and addr.is_physical:
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
        contact_info.submission_method_override = override.submission_method
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
