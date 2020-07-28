from typing import Optional

from django.conf import settings

from ..models import Registration


def get_custom_ovr_link_co(
    registration: Optional[Registration] = None,
) -> Optional[str]:
    if settings.REGISTER_CO_VRD_ENABLED:
        url = f"https://www.sos.state.co.us/voter/pages/pub/olvr/verifyNewVoter.xhtml?vrdid={settings.REGISTER_CO_VRD_ID}"
        if registration:
            url += f"&campaign={registration.uuid}"
        return url
    else:
        return None
