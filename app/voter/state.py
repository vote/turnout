import logging
from typing import Dict, Tuple, Union

import sentry_sdk

from absentee.models import BallotRequest
from common.rollouts import get_feature_bool
from leouptime.proxy import get_random_proxy
from leouptime.uptime import NoProxyError
from register.models import Registration
from reminder.models import ReminderRequest
from verifier.models import Lookup

logger = logging.getLogger("voter")


def get_random_proxy_str():
    # use random proxy (if available)
    try:
        proxy = get_random_proxy()
        return f"socks5://{proxy.address}"
    except NoProxyError:
        return None


def lookup_wi(
    item: Union[BallotRequest, Registration, Lookup, ReminderRequest]
) -> Tuple[str, Dict[str, str]]:
    from ovrlib import wi

    proxy_str = get_random_proxy_str()
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


def lookup_ga(
    item: Union[BallotRequest, Registration, Lookup, ReminderRequest]
) -> Tuple[str, Dict[str, str]]:
    from ovrlib import ga
    from common.geocode import geocode

    # geocode to a county
    addrs = geocode(
        street=item.address1, city=item.city, state="GA", zipcode=item.zipcode,
    )
    if not addrs:
        logger.warning(
            f"Unable to geocode {item} ({item.street1}, {item.city}, GA {item.zipcode})"
        )
        return None, None

    county = None
    for addr in addrs:
        county = addr.get("address_components", {}).get("county", "").upper()
        if county.endswith(" COUNTY"):
            county = county[0:-7]
        if county:
            break
    if not county:
        logger.warning(f"Unable to geocode county for {item}: addrs {addrs}")
        return None, None

    proxy_str = get_random_proxy_str()
    logger.debug(f"lookup up GA {item} with proxy_str {proxy_str}")
    voter = ga.lookup_voter(
        first_name=item.first_name,
        last_name=item.last_name,
        date_of_birth=item.date_of_birth,
        county=county,
        proxies={"https": proxy_str},
    )
    if not voter:
        return None, None

    return voter.voter_reg_number, voter


def lookup_state(
    item: Union[BallotRequest, Registration, Lookup, ReminderRequest]
) -> Tuple[str, Dict[str, str]]:
    try:
        if item.state_id == "WI" and get_feature_bool("voter_state_api", item.state_id):
            return lookup_wi(item)
        if item.state_id == "GA" and get_feature_bool("voter_state_api", item.state_id):
            return lookup_ga(item)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Hit exception doing state lookup on {item}: {e}")
    return None, None
