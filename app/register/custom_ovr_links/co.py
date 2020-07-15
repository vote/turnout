from typing import Optional

from django.conf import settings

from ..models import Registration


def get_custom_ovr_link_co(registration: Registration) -> Optional[str]:
    if settings.REGISTER_CO_VRD_ENABLED:
        return f"https://www.sos.state.co.us/voter/pages/pub/olvr/verifyNewVoter.xhtml?vrdid={settings.REGISTER_CO_VRD_ID}&campaign={registration.uuid}"
    else:
        return None
