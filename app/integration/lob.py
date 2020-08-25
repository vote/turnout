import datetime
import hashlib
import hmac
import logging
from typing import Any, Dict, Optional, Tuple, Union

import lob
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from absentee.models import BallotRequest
from common import enums
from common.apm import tracer
from register.models import Registration

from .models import Link

logger = logging.getLogger("integration")

COVER_SHEET_PATH = "absentee/templates/pdf/lob-cover.pdf"
COVER_SHEET_PERFORATED_PAGE = 1

FORM_CUSTOM = "absentee/templates/pdf/states/{state_id}-lob.pdf"
FORM_NORMAL = "absentee/templates/pdf/states/{state_id}.pdf"

lob.api_key = settings.LOB_KEY


def verify_address(
    address1: str, address2: Optional[str], city: str, state: str, zipcode: str
) -> Tuple[bool, Dict[str, Any]]:
    with tracer.trace("lob.verify_address", service="lob"):
        r = lob.USVerification.create(
            primary_line=address1,
            secondary_line=address2,
            city=city,
            state=state,
            zip_code=zipcode,
        )
    return r["deliverability"] == "deliverable", r["components"]


def check_deliverable(
    data: Dict[str, str], item: Union[BallotRequest, Registration], prefix: str
) -> None:
    # only re-evaluate deliverability if an address field is present
    if any(
        k in data
        for k in [
            f"{prefix}address1",
            f"{prefix}address2",
            f"{prefix}city",
            f"{prefix}state",
            f"{prefix}zipcode",
        ]
    ):
        # ...and if the address isn't blank
        if any(
            getattr(item, k)
            for k in [
                f"{prefix}address1",
                f"{prefix}address2",
                f"{prefix}city",
                f"{prefix}state_id",
                f"{prefix}zipcode",
            ]
        ):
            try:
                deliverable, _ = verify_address(
                    getattr(item, f"{prefix}address1"),
                    getattr(item, f"{prefix}address2"),
                    getattr(item, f"{prefix}city"),
                    getattr(item, f"{prefix}state_id"),
                    getattr(item, f"{prefix}zipcode"),
                )
            except Exception:
                deliverable = None
        else:
            deliverable = None

        if deliverable != getattr(item, f"{prefix}deliverable"):
            setattr(item, f"{prefix}deliverable", deliverable)
            item.save(update_fields=[f"{prefix}deliverable"])


def get_or_create_lob_address(
    internal_id: str,
    name: str,
    address1: str,
    address2: Optional[str],
    city: str,
    state: str,
    zipcode: str,
    country: str = "US",
) -> str:
    # check cache
    addr = cache.get(f"lob_addr_{internal_id}", None)
    if addr:
        return addr

    # lookup
    with tracer.trace("lob.address.list", service="lob"):
        for addr in lob.Address.list(metadata={"va_id": internal_id})["data"]:
            if (
                addr["name"] == name.upper()
                and addr["address_line1"] == address1.upper()
                and (addr["address_line2"] or "") == (address2 or "").upper()
                and addr["address_city"] == city.upper()
                and addr["address_state"] == state.upper()
                and addr["address_zip"][0 : len(zipcode)] == zipcode
            ):
                cache.set(f"lob_addr_{internal_id}", addr["id"])
                return addr["id"]

    # create
    with tracer.trace("lob.address.create", service="lob"):
        r = lob.Address.create(
            name=name,
            address_line1=address1,
            address_line2=address2,
            address_city=city,
            address_state=state,
            address_zip=zipcode,
            address_country=country,
            metadata={"va_id": internal_id},
        )
    cache.set(f"lob_addr_{internal_id}", r.id)
    return r.id


@tracer.wrap()
def send_letter(item: Union[BallotRequest, Registration]) -> datetime.datetime:
    # only do it once!
    try:
        link = Link.objects.get(
            action=item.action, external_tool=enums.ExternalToolType.LOB
        )
        logger.info(f"Already submitted lob letter {link.external_id} for {item}")
        return link.created_at
    except ObjectDoesNotExist:
        pass

    from_addr = get_or_create_lob_address(
        "va_return_addr",
        settings.RETURN_ADDRESS["name"],
        settings.RETURN_ADDRESS["address1"],
        None,
        settings.RETURN_ADDRESS["city"],
        settings.RETURN_ADDRESS["state"],
        settings.RETURN_ADDRESS["zipcode"],
    )

    to_addr = get_or_create_lob_address(
        str(item.uuid),
        item.full_name,
        item.address1,
        item.address2,
        item.city,
        item.state_id,
        item.zipcode,
    )

    with tracer.trace("lob.letter.create", service="lob"):
        letter = lob.Letter.create(
            description=f"{item} print-and-forward",
            to_address=to_addr,
            from_address=from_addr,
            file=item.result_item_mail.file,
            color=False,
            double_sided=True,
            address_placement="top_first_page",
            return_envelope=True,
            perforated_page=COVER_SHEET_PERFORATED_PAGE,
            metadata={"action_uuid": item.action.uuid},
        )
    link = Link.objects.create(
        action=item.action,
        subscriber=item.subscriber,
        external_tool=enums.ExternalToolType.LOB,
        external_id=letter["id"],
    )
    logger.info(f"Submitted lob letter for {item}")
    return link.created_at


def generate_lob_token(item: Union[BallotRequest, Registration]) -> str:
    # use the result_item_mail uuid here, which isn't shown to the frontend
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        str(item.result_item_mail.uuid).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
