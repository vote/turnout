from typing import Optional

from ..models import Registration
from .co import get_custom_ovr_link_co
from .wa import get_custom_ovr_link_wa


def get_custom_ovr_link(
    state: str, registration: Optional[Registration]=None
) -> Optional[str]:
    if state == "CO":
        return get_custom_ovr_link_co(registration)

    if state == "WA":
        return get_custom_ovr_link_wa(registration)

    return None
