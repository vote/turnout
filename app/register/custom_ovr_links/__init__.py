from typing import Optional

from ..models import Registration
from .co import get_custom_ovr_link_co
from .wa import get_custom_ovr_link_wa


def get_custom_ovr_link(registration: Registration) -> Optional[str]:
    if registration.state.code == "CO":
        return get_custom_ovr_link_co(registration)

    if registration.state.code == "WA":
        return get_custom_ovr_link_wa(registration)

    return None
