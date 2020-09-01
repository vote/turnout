import datetime
import logging
import random

import requests
import sentry_sdk
import tweepy
from django.conf import settings
from selenium import webdriver
from selenium.common.exceptions import (
    RemoteDriverServerException,
    SessionNotCreatedException,
    WebDriverException,
)

from common import enums
from common.apm import tracer
from common.rollouts import get_feature_bool
from election.models import StateInformation

from .models import Proxy, Site, SiteCheck, SiteDowntime

MONITORS = {
    "external_tool_polling_place": "Polling Place Lookup",
    "external_tool_ovr": "Online Voter Registration",
    "external_tool_verify_status": "Voter Registration Status Verifier",
    "external_tool_vbm_application": "Absentee Ballot Request",
    "external_tool_absentee_ballot_tracker": "Absentee Ballot Tracker",
}

# as downtime crosses each of these thresholds, we tweet (again)
TWEET_DOWNTIME_THRESHOLDS = [600, 3600, 6 * 3600, 24 * 3600, 7 * 24 * 3600]

DRIVER_TIMEOUT = 30
SENTINEL_SITE = "https://voteamerica.com/"


logger = logging.getLogger("leouptime")


class SeleniumError(Exception):
    pass


class NoProxyError(Exception):
    pass


class StaleProxyError(Exception):
    pass


def get_sentinel_site():
    site, _ = Site.objects.get_or_create(
        url=SENTINEL_SITE, description="uptime monitor sentinel site",
    )
    return site


@tracer.wrap()
def check_group(slug, down_sites=False):
    if down_sites:
        logger.info(f"Checking group {slug} (down sites only)")
    else:
        logger.info(f"Checking group {slug}")

    query = StateInformation.objects.filter(field_type__slug=slug)
    items = [i for i in query]
    random.shuffle(items)

    while True:
        try:
            drivers = get_drivers()
        except WebDriverException as e:
            logger.warning(f"Failed to start selenium worker: {e}")
            sentry_sdk.capture_exception(
                SeleniumError("Failed to start selenium worker")
            )
            return
        if not drivers:
            logger.error("No active proxies")
            sentry_sdk.capture_exception(NoProxyError("No active proxies"))
            return

        try:
            while items:
                item = items.pop()

                # some values are blank
                if not item.text:
                    continue
                desc = f"{item.state_id} {MONITORS[slug]}"
                site, _ = Site.objects.get_or_create(description=desc, url=item.text,)
                if down_sites and site.state_up:
                    continue

                check_site(drivers, site)
        except StaleProxyError:
            logger.info("Refreshing proxies...")
            for driver, proxy in drivers:
                try:
                    driver.quit()
                except WebDriverException as e:
                    logger.warning(f"Failed to quit selenium worker for {proxy}: {e}")
            continue

        break
    for driver, proxy in drivers:
        try:
            driver.quit()
        except WebDriverException as e:
            logger.warning(f"Failed to quit selenium worker for {proxy}: {e}")


@tracer.wrap()
def check_site(drivers, site):
    # first try primary proxy
    check = check_site_with_pos(drivers, 0, site)
    bad_proxy = False
    if not check.state_up:
        # try another proxy
        check2 = check_site_with_pos(drivers, 1, site)

        if check2.state_up:
            # new proxy is fine; ignore the failure
            check.ignore = True
            check.save()

            check3 = check_site_with_pos(drivers, 0, site)
            if check3.state_up:
                # call it intermittent; stick with original proxy
                check = check3
            else:
                # we've burned the proxy
                logger.warning(f"We've burned proxy {drivers[0][1]} on site {site}")
                drivers[0][1].failure_count += 1
                drivers[0][1].state = enums.ProxyStatus.BURNED
                drivers[0][1].save()

                check = check2

                check3.ignore = True
                check3.save()

                bad_proxy = True
        else:
            # verify sentinel site loads
            sentinel = get_sentinel_site()
            check4 = check_site_with_pos(drivers, 0, sentinel)
            if not check4.state_up:
                raise NoProxyError("cannot reach sentinel site with original proxy")
            check5 = check_site_with_pos(drivers, 1, sentinel)
            if not check5.state_up:
                raise NoProxyError("cannot reach sentinel site with backup proxy")

    if site.state_up != check.state_up:
        site.state_up = check.state_up
        site.state_changed_at = check.created_at
        if check.state_up:
            downtime = None
            for d in SiteDowntime.objects.filter(
                site=site, down_check=site.last_went_down_check
            ):
                downtime = d
                break
            if downtime:
                downtime.up_check = check
                downtime.save()
                site.last_went_up_check = check
        else:
            SiteDowntime.objects.create(
                site=site, down_check=check,
            )
            site.last_went_down_check = check

    site.calc_uptimes()
    site.save()

    if bad_proxy:
        raise StaleProxyError()


def check_site_with_pos(drivers, pos, site):
    def reset_selenium():
        reset_tries = 0
        while True:
            reset_tries += 1
            logger.info(f"Reset driver pos {pos} attempt {reset_tries}")
            try:
                drivers[pos][0].quit()
            except WebDriverException as e:
                logger.warning(
                    f"Failed to quit selenium worker for {drivers[pos][1]}: {e}"
                )
            try:
                drivers[pos][0] = get_driver(drivers[pos][1])
                break
            except WebDriverException as e:
                logger.warning(
                    f"Failed to reset driver for {drivers[pos][1]}, reset tries {reset_tries}: {e}"
                )
                if reset_tries > 2:
                    logger.warning(
                        f"Failed to reset driver for {drivers[pos][1]}, reset tries {reset_tries}, giving up"
                    )
                    raise e

    tries = 0
    while True:
        try:
            tries += 1
            check = check_site_with(drivers[pos][0], drivers[pos][1], site)
            if check.error and "timeout" in check.error:
                reset_selenium()
            break
        except SeleniumError as e:
            logger.info(f"Selenium error on try {tries}: {e}")
            if tries > 2:
                raise e
            reset_selenium()

    return check


@tracer.wrap()
def check_site_with(driver, proxy, site):
    logger.debug(f"Checking {site.url} with {proxy}")
    error = None
    timeout = None
    title = ""
    content = ""
    before = datetime.datetime.utcnow()
    try:
        driver.get(site.url)
        up = True
        title = driver.title
        content = driver.page_source
    except SessionNotCreatedException as e:
        raise e
    except RemoteDriverServerException as e:
        raise e
    except Exception as e:
        if "Timed out receiving message from renderer: -" in str(e):
            # if we get a negatime timeout it's because the worker is broken
            raise SeleniumError(f"Problem talking to selenium worker: {e}")
        if "establishing a connection" in str(e):
            raise e
        if "marionette" in str(e):
            raise e
        if "timeout" in str(e):
            # we may tolerate timeout in some cases; see below
            timeout = str(e)
            up = True
        else:
            up = False
            error = str(e)
    after = datetime.datetime.utcnow()
    dur = after - before

    # the trick is determining if this loaded the real page or some sort of error/404 page.
    for item in ["404", "not found", "error"]:
        if item in title.lower():
            up = False
            error = f"'{item}' in page title"

    REQUIRED_STRINGS = [
        "vote",
        "Vote",
        "Poll",
        "poll",
        "Absentee",
        "Please enable JavaScript to view the page content.",  # for CT
        "application/pdf",  # for WY
    ]
    have_any = False
    for item in REQUIRED_STRINGS:
        if item in content:
            have_any = True
    if not have_any:
        up = False
        if timeout:
            error = timeout
        else:
            error = f"Cannot find any of {REQUIRED_STRINGS} not in page content"
            logger.info(content)

    check = SiteCheck.objects.create(
        site=site,
        state_up=up,
        load_time=dur.total_seconds(),
        error=error,
        proxy=proxy,
        ignore=False,
        title=title,
        content=content if not up else None,
    )

    if not up:
        logger.info(
            f"DOWN: {site.description} {site.url} ({error}) duration {dur} proxy {proxy}"
        )
    else:
        logger.info(
            f"UP: {site.description} {site.url} ({error}) duration {dur} proxy {proxy}"
        )
    return check


def get_driver(proxy):
    options = webdriver.ChromeOptions()
    options.add_argument(f"--proxy-server=socks5://{proxy.address}")

    # https://stackoverflow.com/questions/48450594/selenium-timed-out-receiving-message-from-renderer
    options.add_argument("--disable-gpu")
    options.add_argument("enable-automation")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    options.add_argument(
        "--disable-browser-side-navigation"
    )  # https://stackoverflow.com/a/49123152/1689770

    caps = webdriver.DesiredCapabilities.CHROME.copy()
    caps["pageLoadStrategy"] = "normal"

    driver = webdriver.Remote(
        command_executor=settings.SELENIUM_URL,
        desired_capabilities=caps,
        options=options,
    )
    driver.set_page_load_timeout(DRIVER_TIMEOUT)
    return driver


def get_drivers():
    drivers = []

    proxies = list(
        Proxy.objects.filter(state=enums.ProxyStatus.UP).order_by(
            "failure_count", "created_at"
        )
    )

    if len(proxies) < 2:
        logger.warning(f"not enough available proxies (only {len(proxies)})")
        raise NoProxyError(f"{len(proxies)} available (need at least 2)")

    # always try to keep a fresh proxy in reserve, if we can
    if len(proxies) > 2:
        reserve = proxies.pop()
        logger.debug(f"reserve {reserve}")

    # use one as a backup, and a random one as primary
    backup = proxies.pop()
    primary = random.choice(proxies)
    logger.debug(f"backup {backup}")
    logger.debug(f"primary {primary}")
    drivers.append([get_driver(primary), primary])
    drivers.append([get_driver(backup), backup])

    return drivers


@tracer.wrap()
def check_all():
    for slug in MONITORS.keys():
        check_group(slug)


def tweet(message):
    auth = tweepy.OAuthHandler(
        settings.UPTIME_TWITTER_CONSUMER_KEY, settings.UPTIME_TWITTER_CONSUMER_SECRET
    )
    auth.set_access_token(
        settings.UPTIME_TWITTER_ACCESS_TOKEN,
        settings.UPTIME_TWITTER_ACCESS_TOKEN_SECRET,
    )

    # Create API object
    api = tweepy.API(auth)

    # Create a tweet
    logger.info(f"Tweet: {message}")
    api.update_status(message)


def to_pretty_timedelta(n):
    if n < datetime.timedelta(seconds=120):
        return str(int(n.total_seconds())) + "s"
    if n < datetime.timedelta(minutes=120):
        return str(int(n.total_seconds() // 60)) + "m"
    if n < datetime.timedelta(hours=48):
        return str(int(n.total_seconds() // 3600)) + "h"
    if n < datetime.timedelta(days=14):
        return str(int(n.total_seconds() // (24 * 3600))) + "d"
    if n < datetime.timedelta(days=7 * 12):
        return str(int(n.total_seconds() // (24 * 3600 * 7))) + "w"
    if n < datetime.timedelta(days=365 * 2):
        return str(int(n.total_seconds() // (24 * 3600 * 30))) + "M"
    return str(int(n.total_seconds() // (24 * 3600 * 365))) + "y"


@tracer.wrap()
def tweet_site_status(site):
    message = None
    now = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)

    if site.state_up:
        if (
            site.last_tweet_at
            and site.last_went_down_check
            and site.last_went_up_check
            and site.last_tweet_at > site.last_went_down_check.created_at
            and site.last_tweet_at < site.last_went_up_check.created_at
        ):
            message = f"{site.description} is now back up"
    elif site.state_changed_at:
        # complain about being down after crossing several thresholds
        for seconds in TWEET_DOWNTIME_THRESHOLDS:
            cutoff = site.state_changed_at + datetime.timedelta(seconds=seconds)
            if now > cutoff and (not site.last_tweet_at or site.last_tweet_at < cutoff):
                actual_delta = now - site.state_changed_at
                logger.info(
                    f"cutoff {cutoff} {seconds} change at {site.state_changed_at} tweet_at {site.last_tweet_at}"
                )
                message = f"{site.description} has been down for {to_pretty_timedelta(actual_delta)}"
                break

    if message:
        uptimes = []
        for period, v in {
            "day": (24 * 3600, site.uptime_day),
            "week": (7 * 24 * 3600, site.uptime_week),
            "month": (30 * 24 * 3600, site.uptime_month),
            "quarter": (91 * 24 * 3600, site.uptime_quarter),
        }.items():
            seconds, uptime = v
            if uptime and uptime < 1.0:
                down_seconds = (1.0 - uptime) * seconds
                uptimes.append(
                    f"{to_pretty_timedelta(datetime.timedelta(seconds=down_seconds))} over last {period} ({'%.3f' % (uptime*100)}% uptime)"
                )
        if uptimes:
            message += ". Overall, down " + ", ".join(uptimes)
        message += " " + site.url

        site.last_tweet_at = now
        site.save()

        if settings.SLACK_UPTIME_WEBHOOK:
            down_check_url = f"{settings.WWW_ORIGIN}/v1/leouptime/checks/{site.last_went_down_check.pk}/"
            slack_message = f"{message} (failing check {check_url})"
            r = requests.post(settings.SLACK_UPTIME_WEBHOOK, json={"text": slack_message})

        if not get_feature_bool("leouptime", "tweet"):
            logger.info(f"tweet=false via optimizely; would have sent: {message}")
        else:
            tweet(message)


@tracer.wrap()
def tweet_all_sites():
    for site in Site.objects.all():
        tweet_site_status(site)
