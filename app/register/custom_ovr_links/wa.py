from typing import Optional

from django.conf import settings

from ..models import Registration


def get_custom_ovr_link_wa(
    registration: Optional[Registration] = None,
) -> Optional[str]:
    if settings.REGISTER_WA_VRD_ENABLED:
        return f"https://olvr.votewa.gov/default.aspx?Org={settings.REGISTER_WA_VRD_ID}"
    else:
        return None
