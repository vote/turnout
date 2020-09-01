import logging
from typing import Dict, Tuple, Union

from absentee.models import BallotRequest
from common.rollouts import get_feature_bool
from leouptime.proxy import get_random_proxy
from leouptime.uptime import NoProxyError
from register.models import Registration
from reminder.models import ReminderRequest
from verifier.models import Lookup

logger = logging.getLogger("voter")


def lookup_wi(
    item: Union[BallotRequest, Registration, Lookup, ReminderRequest]
) -> Tuple[str, Dict[str, str]]:
    from ovrlib import wi

    # use random proxy (if available)
    try:
        proxy = get_random_proxy()
        proxy_str = f"socks5://{proxy.address}"
    except NoProxyError:
        proxy_str = None

    logger.debug(f"lookup up WI {item} with proxy_str {proxy_str}")

    voters = wi.lookup_voter(
        first_name=item.first_name,
        last_name=item.last_name,
        date_of_birth=item.date_of_birth,
        proxies={"https": proxy_str},
    )
    for v in voters:
        logger.info(v)
        if v.zipcode[0:5] == item.zipcode[0:5]:
            return v.voter_reg_number, v
    return None, None


def lookup_state(
    item: Union[BallotRequest, Registration, Lookup, ReminderRequest]
) -> Tuple[str, Dict[str, str]]:
    if item.state_id == "WI" and get_feature_bool("voter_state_api", item.state_id):
        return lookup_wi(item)
    return None, None
