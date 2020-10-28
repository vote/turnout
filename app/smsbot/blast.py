import logging
import math
import uuid
from typing import Optional
from urllib.parse import urlencode

import requests
from django.conf import settings

from common.apm import tracer
from common.aws import s3_client
from common.geocode import geocode
from common.i90 import shorten_url
from voter.models import Voter

from .models import Blast, Number, SMSMessage

DNC_API_ENDPOINT = "https://locator-api.voteamerica.com/lookup"

HIRES = True  # 512x512 or 256x256?

logger = logging.getLogger("smsbot")


def send_blast_sms(number: Number, blast: Blast) -> None:
    if SMSMessage.objects.filter(phone=number, blast=blast).exists():
        logger.info(f"Already sent {blast} to {number}")
        return

    number.send_sms(blast.content, blast=blast)


def send_voter_map_mms(voter: Voter, blast: Blast, destination: str) -> None:
    number = Number.objects.filter(phone=voter.phone).first()
    if not number:
        logger.info(f"No phone for {voter}")
        return
    if SMSMessage.objects.filter(phone=number, blast=blast).exists():
        logger.info(f"Already sent {blast} to {number}")
        return

    send_map_mms(number, blast=blast, voter=voter, destination=destination)


@tracer.wrap()
def send_map_mms(
    number: Number,
    blast: Blast = None,
    voter: Voter = None,
    address_full: str = None,
    destination: str = "pp",
) -> Optional[str]:
    # geocode home
    if voter:
        home = geocode(
            street=voter.address_full, city=voter.city, state=voter.state_id,
        )
        home_address = (
            f"{voter.address_full}, {voter.city}, {voter.state_id} {voter.zipcode}"
        )
        home_address_partial = voter.address_full
    else:
        home = geocode(q=address_full)
        home_address = address_full
        home_address_partial = address_full.split(",")[0]
    if not home:
        logger.info(f"Failed to geocode {voter} {address_full}")
        return f"Failed to geocode {voter} {address_full}"

    home_loc = f"{home[0]['location']['lng']},{home[0]['location']['lat']}"

    # geocode destination
    with tracer.trace("pollproxy.lookup", service="pollproxy"):
        response = requests.get(DNC_API_ENDPOINT, {"address": home_address})
    if destination == "pp":
        dest = response.json().get("data", {}).get("election_day_locations", [])
        if not dest:
            logger.info(f"No election day location for {voter} {address_full}")
            return f"No election day location for {voter} {address_full}"
        message = f"Tuesday, November 3rd is Election Day! If you are registered to vote at {home_address_partial.upper()} then your polling place is:"
        what = "polling place"
    elif destination == "ev":
        dest = response.json().get("data", {}).get("early_vote_locations", [])
        if not dest:
            logger.info(f"No early_vote location for {voter} {address_full}")
            return f"No early vote location for {voter} {address_full}"

        if dest[0]["state"] == "AL":
            message = "The last day of early voting is this Thursday, October 29th!"
        else:
            message = "You can vote early!"

        message = f"{message} If you are registered to vote at {home_address_partial.upper()} then your early voting location is:"
        what = "early voting location"
    else:
        return f"Unrecognized address type {destination}"

    dest = dest[0]
    dest_address = (
        f"{dest['address_line_1']}, {dest['city']}, {dest['state']} {dest['zip']}"
    )
    dest_loc = f"{dest['lon']},{dest['lat']}"

    # Pick a reasonable zoom level for the map, since mapbox pushes
    # the markers to the very edge of the map.
    #
    # mapbox zoom levels are 1-20, and go by power of 2: +1 zoom means
    # 1/4 of the map area.
    dx = abs(float(dest["lon"]) - float(home[0]["location"]["lng"]))
    dy = abs(float(dest["lat"]) - float(home[0]["location"]["lat"]))
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

    centerx = (float(dest["lon"]) + float(home[0]["location"]["lng"])) / 2
    centery = (float(dest["lat"]) + float(home[0]["location"]["lat"])) / 2
    map_loc = f"{centerx},{centery},{zoom}"

    # fetch map
    map_url = f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s-home+00f({home_loc}),pin-s-p+f00({dest_loc})/{map_loc}/{size}?access_token={settings.MAPBOX_KEY}"
    response = requests.get(map_url)
    if response.status_code != 200:
        logger.error(f"Failed to fetch map, got status code {response.status_code}")
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
        logger.warning(f"Unable to push {filename} to {settings.MMS_ATTACHMENT_BUCKET}")
        return "Unable to upload map"
    stored_map_url = (
        f"https://{settings.MMS_ATTACHMENT_BUCKET}.s3.amazonaws.com/{filename}"
    )

    # send
    locator_url = f"https://www.voteamerica.com/where-to-vote/?{urlencode({'address':home_address})}"
    if blast:
        locator_url += f"&utm_medium=mms&utm_source=turnout&utm_campaign={blast.campaign}&source=va_mms_turnout_{blast.campaign}"
    number.send_sms(
        f"""{shorten_url(locator_url)}

{message}

{dest['location_name'].upper()}
{dest_address.upper()}
{dest['dates_hours']}

If that is not your address, find your {what} at https://my.voteamerica.com/vote or reply HELPLINE with any questions about voting.
""",
        media_url=[stored_map_url],
        blast=blast,
    )
    logger.info(
        f"Sent {destination} map for {home_address_partial} (blast {blast}) to {number}"
    )
    return None
