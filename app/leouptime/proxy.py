import datetime
import logging
import random
import tempfile
import time
import uuid

import paramiko
import requests
from django.conf import settings
from selenium.common.exceptions import WebDriverException

from common import enums
from common.rollouts import get_feature_int

from .models import Proxy
from .uptime import NoProxyError, check_site_with, get_driver, get_sentinel_site

PROXY_PORT_MIN = 2000
PROXY_PORT_MAX = 60000
PROXY_PREFIX = "proxy-"

REGIONS = [
    "nyc1",
    "nyc3",
    "sfo2",
    "sfo3",
]

CREATE_TEMPLATE = {
    "size": "s-1vcpu-1gb",
    "image": "ubuntu-18-04-x64",
    "ssh_keys": [settings.PROXY_SSH_KEY_ID],
    "backups": False,
    "ipv6": False,
}

DROPLET_ENDPOINT = "https://api.digitalocean.com/v2/droplets"

UNITFILE = """
[Unit]
Description=microsocks
After=network.target
[Service]
ExecStart=/root/microsocks/microsocks -p {port}
[Install]
WantedBy=multi-user.target
"""

SETUP = [
    "apt update",
    "apt install -y gcc make",
    "git clone https://github.com/rofl0r/microsocks",
    "cd microsocks && make",
    "systemctl enable microsocks.service",
    "systemctl start microsocks.service",
]


logger = logging.getLogger("leouptime")


def get_random_proxy():
    proxies = list(
        Proxy.objects.filter(state=enums.ProxyStatus.UP).order_by(
            "failure_count", "created_at"
        )
    )
    if len(proxies) < 1:
        logger.warning(f"no available proxies (only {len(proxies)})")
        raise NoProxyError(f"{len(proxies)} available (need at least 1)")

    random.shuffle(proxies)
    return proxies[0]


def get_proxies_by_name():
    r = {}
    nexturl = DROPLET_ENDPOINT
    while nexturl:
        response = requests.get(
            nexturl,
            headers={
                "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
            },
        )
        for droplet in response.json().get("droplets", []):
            if settings.PROXY_TAG in droplet["tags"]:
                r[droplet["name"]] = droplet
        nexturl = response.json().get("links", {}).get("pages", {}).get("next")
    return r


def create_proxy(region):
    proxy_uuid = uuid.uuid4()
    name = f"{PROXY_PREFIX}{region}-{str(proxy_uuid)}"

    logger.info(f"Creating {name}...")
    req = CREATE_TEMPLATE.copy()
    req["name"] = name
    req["region"] = region
    req["tags"] = [settings.PROXY_TAG]
    response = requests.post(
        DROPLET_ENDPOINT,
        headers={
            "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
            "Content-Type": "application/json",
        },
        json=req,
    )
    logger.info(response.json())
    droplet_id = response.json()["droplet"]["id"]

    # wait for IP address
    logger.info(f"Created {name} droplet_id {droplet_id}, waiting for IP...")
    ip = None
    while True:
        response = requests.get(
            f"{DROPLET_ENDPOINT}/{droplet_id}",
            headers={
                "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
                "Content-Type": "application/json",
            },
        )
        for v4 in response.json()["droplet"]["networks"].get("v4", []):
            ip = v4["ip_address"]
            break
        if ip:
            break
        logger.info("waiting for IP")
        time.sleep(1)

    port = random.randint(PROXY_PORT_MIN, PROXY_PORT_MAX)
    proxy = Proxy.objects.create(
        uuid=proxy_uuid,
        address=f"{ip}:{port}",
        description=name,
        state=enums.ProxyStatus.CREATING,
        failure_count=0,
    )

    with tempfile.NamedTemporaryFile() as tmp_key:
        tmp_key.write(settings.PROXY_SSH_KEY.replace("\\n", "\n").encode("utf-8"))
        tmp_key.flush()

        # logger.info(f"IP is {ip}, waiting for machine to come up...")
        # time.sleep(60)

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        while True:
            try:
                logger.info(f"Connecting to {ip} via SSH...")
                ssh.connect(ip, username="root", key_filename=tmp_key.name, timeout=10)
                break
            except:
                logger.info("Waiting a bit...")
                time.sleep(5)

        logger.info("Writing systemd unit...")
        stdin_, stdout_, stderr_ = ssh.exec_command(
            "cat >/etc/systemd/system/microsocks.service"
        )
        stdin_.write(UNITFILE.format(port=port))
        stdin_.close()
        stdout_.channel.recv_exit_status()

        for cmd in SETUP:
            stdin_, stdout_, stderr_ = ssh.exec_command(cmd)
            stdout_.channel.recv_exit_status()
            lines = stdout_.readlines()
            logger.info(f"{cmd}: {lines}")

    proxy.state = enums.ProxyStatus.UP
    proxy.save()
    logger.info(f"Created proxy {proxy}")
    return proxy


def remove_proxy(droplet_id):
    response = requests.delete(
        f"{DROPLET_ENDPOINT}/{droplet_id}/destroy_with_associated_resources/dangerous",
        headers={
            "Authorization": f"Bearer {settings.DIGITALOCEAN_KEY}",
            "Content-Type": "application/json",
            "X-Dangerous": "true",
        },
    )


def check_proxies():
    stray = get_proxies_by_name()
    up = 0
    creating_cutoff = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(minutes=10)

    bad_proxies = []
    for proxy in Proxy.objects.all():
        if proxy.description in stray:
            logger.info(f"Have proxy {proxy}")
            if proxy.state == enums.ProxyStatus.BURNED:
                # we should delete this
                proxy.state = enums.ProxyStatus.DOWN
                proxy.save()
            elif proxy.state == enums.ProxyStatus.DOWN:
                # we should delete this
                pass
            elif (
                proxy.state == enums.ProxyStatus.CREATING
                and proxy.modified_at < creating_cutoff
            ):
                # delete
                logger.info(f"Proxy {proxy} has been CREATING for too long")
                proxy.delete()
            else:
                # not stray
                if proxy.state == enums.ProxyStatus.UP:
                    up += 1

                    # get a selenium driver
                    tries = 0
                    while True:
                        try:
                            driver = get_driver(proxy)
                            break
                        except WebDriverException as e:
                            logger.warning(
                                f"Failed to start selenium worker, tries {tries}: {e}"
                            )
                            tries += 1
                            if tries > 2:
                                logger.warning(
                                    f"Failed to start selenium worker; we'll check proxies later: {e}"
                                )
                                # just bail out here completely; we'll check our proxies again in a bit
                                return

                    # make sure the proxy is actually working
                    site = get_sentinel_site()
                    check = check_site_with(driver, proxy, site)
                    if not check.state_up:
                        logger.info(f"Proxy {proxy} can't reach sentinel site {site}")
                        bad_proxies.append((proxy, check))
                    try:
                        driver.quit()
                    except WebDriverException as e:
                        logger.warning(
                            f"Failed to quit selenium worker for {proxy}: {e}"
                        )

                del stray[proxy.description]
        else:
            if proxy.state != enums.ProxyStatus.DOWN:
                logger.info(f"No droplet for proxy {proxy}")
                proxy.state = enums.ProxyStatus.DOWN
                proxy.save()

    for name, info in stray.items():
        if not name.startswith(PROXY_PREFIX):
            continue
        logger.info(f"Removing stray droplet {info['id']}")
        remove_proxy(info["id"])

    if bad_proxies:
        if len(bad_proxies) == up:
            logger.warning(
                "All proxies appear to be failing--the sentinel is probably down?"
            )
        else:
            for proxy, check in bad_proxies:
                logger.warning(
                    f"Marking proxy {proxy} BURNED (due to sentinel check failure)"
                )
                check.ignore = True
                check.save()
                proxy.state = enums.ProxyStatus.BURNED
                proxy.save()
                up -= 1

    proxy_count = get_feature_int("leouptime", "proxy_count") or settings.PROXY_COUNT
    logger.info(f"proxy_count {proxy_count}")
    while up < proxy_count:
        create_proxy(random.choice(REGIONS))
        up += 1
