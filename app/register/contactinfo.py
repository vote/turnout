from dataclasses import dataclass
from typing import Optional

from election.models import StateInformation
from official.models import Address

from .models import Registration


@dataclass
class RegisterContactInfo:
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None


def register_address_score(addr: Address) -> int:
    """
    Returns a "score" for selecting the optimal address to tell the user to
    contact for questions about their registration.

    1: This is an office that accepts registrations and is a physical address
    2: This is an office that accepts registrations
    3: All other offices

    We prioritize physical addresses over mailing addresses because the physical
    offices can always receive mail, and some kinds of mail (USPS express) can
    only be delivered to the physical addresses (the mailing addresses are
    typically PO boxes).
    """
    if addr.process_domestic_registrations and addr.is_physical:
        return 1
    elif addr.process_domestic_registrations:
        return 2
    else:
        return 3


def get_registration_contact_info(registration: Registration) -> RegisterContactInfo:
    contact_info = RegisterContactInfo()

    if not registration.region_id:
        # fallback to statewide address
        try:
            contact_info.address = (
                StateInformation.objects.only("field_type", "text")
                .get(
                    state=registration.state,
                    field_type__slug="registration_nvrf_submission_address",
                )
                .text
            )
        except StateInformation.DoesNotExist:
            contact_info.address = ""

        return contact_info

    office_addresses = sorted(
        Address.objects.filter(office__region__external_id=registration.region_id),
        key=register_address_score,
    )

    # Find contact info
    contact_info.address = next((addr.full_address for addr in office_addresses), None)

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
