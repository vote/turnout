import logging
import math
import uuid
from typing import Dict, Optional
from urllib.parse import urlencode

import requests
from django.conf import settings

from common.apm import tracer
from common.aws import s3_client
from common.geocode import geocode
from common.i90 import shorten_url
from common.rollouts import get_feature_bool

from .models import Blast, Number, SMSMessage

DNC_API_ENDPOINT = "https://locator-api.voteamerica.com/lookup"
CIVIC_API_ENDPOINT = "https://www.googleapis.com/civicinfo/v2/voterinfo"

HIRES = True  # 512x512 or 256x256?

logger = logging.getLogger("smsbot")


@tracer.wrap()
def send_blast_sms(blast: Blast, number: Number, force_dup: bool = False) -> None:
    if not force_dup and SMSMessage.objects.filter(phone=number, blast=blast).exists():
        logger.info(f"Already sent {blast} to {number}")
        return

    number.send_sms(blast.content, blast=blast)


@tracer.wrap()
def send_blast_mms_map(
    blast: Blast,
    number: Number,
    map_type: str,
    address_full: str,
    force_dup: bool = False,
) -> None:
    if not force_dup and SMSMessage.objects.filter(phone=number, blast=blast).exists():
        logger.info(f"Already sent {blast} to {number}")
        return

    if force_dup:
        # do not link the test MMS to the blast (since blast queries
        # may/should exclude numbers that have already been texted for
        # this blast as part of the query).
        send_map_mms(number, map_type, address_full, blast.content)
    else:
        send_map_mms(number, map_type, address_full, blast.content, blast=blast)


@tracer.wrap()
def send_map_mms(
    number: Number,
    map_type: str,  # 'pp' or 'ev'
    address_full: str,
    content: str = None,
    blast: Blast = None,
) -> Optional[str]:
    formdata: Dict[str, str] = {}

    # geocode home
    home = geocode(q=address_full)
    home_address = address_full
    if not home:
        logger.info(f"{number}: Failed to geocode {address_full}")
        return f"Failed to geocode {address_full}"
    formdata["home_address_short"] = address_full.split(",")[0].upper()

    home_loc = f"{home[0]['location']['lng']},{home[0]['location']['lat']}"

    # geocode destination
    if get_feature_bool("locate_use_dnc_data", home[0]["address_components"]["state"]):
        # pollproxy
        with tracer.trace("pollproxy.lookup", service="pollproxy"):
            response = requests.get(DNC_API_ENDPOINT, {"address": home_address})
        if map_type == "pp":
            dest = response.json().get("data", {}).get("election_day_locations", [])
            if not dest:
                logger.info(f"{number}: No election day location for {address_full}")
                return f"No election day location for {address_full}"
            dest = dest[0]
        elif map_type == "ev":
            dest = response.json().get("data", {}).get("early_vote_locations", [])
            if not dest:
                logger.info(f"{number}: No early_vote location for {address_full}")
                return f"No early vote location for {address_full}"
            dest = dest[0]
        else:
            return f"Unrecognized address type {map_type}"

        dest_lon = dest["lon"]
        dest_lat = dest["lat"]
        dest_name = dest["location_name"]
        dest_address = (
            f"{dest['address_line_1']}, {dest['city']}, {dest['state']} {dest['zip']}"
        )
        dest_hours = dest["dates_hours"]
    else:
        # civic
        with tracer.trace("civicapi.voterlookup", service="google"):
            response = requests.get(
                CIVIC_API_ENDPOINT,
                {
                    "address": home_address,
                    "electionId": 7000,
                    "key": settings.CIVIC_KEY,
                },
            )
        if map_type == "pp":
            dest = response.json().get("pollingLocations", [])
            if not dest:
                logger.info(f"{number}: No election day location for {address_full}")
                return f"No election day location for {address_full}"
            dest = dest[0]
        elif map_type == "ev":
            dest = response.json().get("earlyVoteSites", [])
            if not dest:
                logger.info(f"{number}: No early_vote location for {address_full}")
                return f"No early vote location for {address_full}"
            dest = dest[0]
        else:
            return f"Unrecognized address type {map_type}"

        dest_lon = dest["longitude"]
        dest_lat = dest["latitude"]
        dest_name = dest["address"]["locationName"]
        dest_address = f"{dest['address']['line1']}, {dest['address']['city']}, {dest['address']['state']} {dest['address']['zip']}"
        dest_hours = dest["pollingHours"]

    formdata["dest_name"] = dest_name.upper()
    formdata["dest_address"] = dest_address.upper()
    formdata["dest_hours"] = dest_hours

    # Pick a reasonable zoom level for the map, since mapbox pushes
    # the markers to the very edge of the map.
    #
    # mapbox zoom levels are 1-20, and go by power of 2: +1 zoom means
    # 1/4 of the map area.
    dx = abs(float(dest_lon) - float(home[0]["location"]["lng"]))
    dy = abs(float(dest_lat) - float(home[0]["location"]["lat"]))
    if dx > dy:
        d = dx
    else:
        d = dy
    logd = math.log2(1.0 / d)
    zoom = logd + 7.5

    if HIRES:
        size = "512x512"
    else:
        size = "256x256"
        zoom -= 1.0

    centerx = (float(dest_lon) + float(home[0]["location"]["lng"])) / 2
    centery = (float(dest_lat) + float(home[0]["location"]["lat"])) / 2
    map_loc = f"{centerx},{centery},{zoom}"

    # fetch map
    map_url = f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s-home+00f({home_loc}),pin-s-p+f00({dest_lon},{dest_lat})/{map_loc}/{size}?access_token={settings.MAPBOX_KEY}"
    response = requests.get(map_url)
    if response.status_code != 200:
        logger.error(
            f"{number}: Failed to fetch map, got status code {response.status_code}"
        )
        return "Failed to fetch map"
    map_image = response.content
    map_image_type = response.headers["content-type"]

    # store map in s3
    filename = str(uuid.uuid4()) + "." + map_image_type.split("/")[-1]
    upload = s3_client.put_object(
        Bucket=settings.MMS_ATTACHMENT_BUCKET,
        Key=filename,
        ContentType=map_image_type,
        ACL="public-read",
        Body=map_image,
    )
    if upload.get("ResponseMetadata", {}).get("HTTPStatusCode") != 200:
        logger.warning(
            f"{number}: Unable to push {filename} to {settings.MMS_ATTACHMENT_BUCKET}"
        )
        return "Unable to upload map"
    stored_map_url = (
        f"https://{settings.MMS_ATTACHMENT_BUCKET}.s3.amazonaws.com/{filename}"
    )

    # locator link
    locator_url = f"https://www.voteamerica.com/where-to-vote/?{urlencode({'address':home_address})}"
    if blast:
        locator_url += f"&utm_medium=mms&utm_source=turnout&utm_campaign={blast.campaign}&source=va_mms_turnout_{blast.campaign}"
    formdata["locator_url"] = shorten_url(locator_url)

    # send
    number.send_sms(
        content.format(**formdata), media_url=[stored_map_url], blast=blast,
    )
    logger.info(
        f"Sent {map_type} map for {formdata['home_address_short']} (blast {blast}) to {number}"
    )
    return None
