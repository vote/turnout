import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
import sentry_sdk
from django.conf import settings
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D  # ``D`` is a shortcut for ``Distance``

from common.analytics import statsd
from common.apm import tracer
from common.geocode import (
    al_jefferson_county_bessemer_division,
    geocode,
    ma_location_to_mcd,
    wi_location_to_mcd,
)

from .models import Address, Region

logger = logging.getLogger("official")


TARGETSMART_DISTRICT_API = "https://api.targetsmart.com/service/district"


class TargetSmartAPIError(Exception):
    pass


# weird, but the region name includes the county name
region_name_contains_county = [
    "MI",
    "WI",
]

# by county
county_method = [
    "DC",  # 1 item, matches county
    "WA",
    "OR",
    "CA",
    "AZ",
    "NM",
    "NV",
    "ID",
    "MT",
    "ND",
    "SD",
    "WY",
    "UT",
    "CO",
    "TX",
    "OK",
    "KS",
    "WY",
    "NE",
    "MN",
    "AR",
    "MS",
    "FL",
    "GA",
    "SC",
    "NC",
    "TN",
    "KY",
    "WV",
    "OH",
    "IN",
    "DE",
    "NJ",
    "LA",  # "Parish" instead of "County"
]

# NY is by county, except NYC is broken into "New York
# City: %s" for (Manhattan, Brooklyn, Staten Island,
# Queens, The Bronx).  Which are actually counties.
nyc_remap = {
    "new york county": "new york city: manhattan",
    "kings county": "new york city: brooklyn",
    "bronx county": "new york city: the bronx",
    "queens county": "new york city: queens",
    "richmond county": "new york city: staten island",
}


@tracer.wrap()
def match_region(
    city: str,
    county: str,
    state: str,
    location: Point = None,
    districts: Dict[str, Any] = None,
) -> Optional[List[Region]]:
    queryset = Region.visible.filter(state__code=state).order_by("name")

    if state in region_name_contains_county + county_method:
        # match any county in the address match list
        from django.db.models import Q

        q = Q(name__icontains=county)
        if county.startswith("La") or county.startswith("De"):
            county2 = county[0:2] + " " + county[2:]
            q = q | Q(name__icontains=county2)
        elif county.startswith("Le "):
            county2 = county[0:2] + county[3:]
            q = q | Q(name__icontains=county2)
        elif county.startswith("St. "):
            county2 = "Saint " + county[4:]
            q = q | Q(name__icontains=county2)
        elif county == "Shannon County":
            q = q | Q(name__icontains="oglala lakota county")
        elif county.endswith(" city"):
            county2 = "City of " + county[:-5]
            q = q | Q(name__icontains=county2)

        queryset = queryset.filter(q)

    ls = list(queryset)
    regions_by_name = {r.name.lower(): r for r in ls}

    city = city.lower()
    county = county.lower()

    if county.startswith("la") or county.startswith("de"):
        county2 = county[0:2] + " " + county[2:]
    elif county.startswith("le "):
        county2 = county[0:2] + county[3:]
    elif county.startswith("st. "):
        county2 = "saint " + county[4:]
    elif county == "honolulu county" and state == "HI":
        county2 = "honolulu, city and county"
    elif county == "shannon county" and state == "SD":
        county2 = "oglala lakota county"
    elif "'" in county:
        county2 = county.replace("'", "")
    elif county.endswith(" city"):
        county2 = "city of " + county[:-5]
    else:
        county2 = county

    if state == "MO":
        if city == "kansas city":
            return [regions_by_name["kansas city"]]
        if county == "st. louis city":
            return [regions_by_name["saint louis city"]]
        if county == "st. louis county":
            return [regions_by_name["saint louis county"]]

    if state == "AK":
        assert districts
        # Good grief!  These mostly follow state leg districts, except for several towns in
        # districts [37, 39, 40] are in region III instead of IV.
        #  http://www.elections.alaska.gov/Core/contactregionalelectionsoffices.php
        #  http://www.elections.alaska.gov/doc/forms/H32-Comm.pdf
        district = int(districts.get("house", {}).get("district_number", 0))
        key = None
        if district >= 29 and district <= 36:
            key = "Region I Elections Office: Southeast Alaska, Prince William Sound, Kodiak & Kenai Peninsula".lower()
        elif district >= 13 and district <= 28:
            key = "Region II Elections Office: Anchorage Vicinity".lower()
        elif district in [7, 8, 10, 11, 12]:
            key = "Region II Elections Office: Matanuska-Susitna Vicinity".lower()
        elif (
            (district >= 1 and district <= 6)
            or (district == 9)
            or (
                district in [37, 39, 40]
                and city
                in [
                    "alatna",
                    "allakaket",
                    "bettles",
                    "coldfoot",
                    "evansville",
                    "galena",
                    "grayling",
                    "holy cross",
                    "hughes",
                    "huslia",
                    "kaltag",
                    "koyukuk",
                    "lake minchumina",
                    "mcgrath",
                    "new Allakaket",
                    "nikolai",
                    "nulato",
                    "ruby",
                    "shageluk",
                    "takotna",
                    "wiseman",
                ]
            )
        ):
            key = "Regions III Elections Office: Fairbanks, Interior, Eastern Mat-Su & Valdez".lower()
        elif district in [37, 38, 39, 40]:
            key = "Regions IV Elections Office: Northern, Western & Southwest Alaska & Aleutian Chain".lower()
        if key and key in regions_by_name:
            return [regions_by_name[key]]

    # check against state GIS data?
    if state == "MA":
        assert location
        mcd = ma_location_to_mcd(location)
        if mcd:
            for typ in ["city", "town", "ctiy"]:
                key = "%s of %s" % (typ.lower(), mcd.lower())
                if key in regions_by_name:
                    return [regions_by_name[key]]
                if key in regions_by_name:
                    return [regions_by_name[key]]

    if state == "WI":
        assert location
        mcd = wi_location_to_mcd(location)
        if mcd:
            if mcd.startswith("St. "):
                mcd = "Saint " + mcd[4:]
            for typ in ["city", "village", "town"]:
                key = "%s of %s, %s" % (typ.lower(), mcd.lower(), county)
                if key in regions_by_name:
                    return [regions_by_name[key]]
                key = "%s of %s, %s" % (typ.lower(), mcd.lower(), county2)
                if key in regions_by_name:
                    return [regions_by_name[key]]
                if mcd == "drummond":
                    # USVF name may have a stray space before the comma
                    key = "%s of %s , %s" % (typ, mcd, county)
                elif mcd == "land o'lakes":
                    # WI GIS has no space after O'
                    key = "%s of land o' lakes, %s" % (typ, county)
                else:
                    continue
                if key in regions_by_name:
                    return [regions_by_name[key]]

    if state == "AL" and county.lower() == "jefferson county":
        assert location
        if al_jefferson_county_bessemer_division(location):
            return [regions_by_name["jefferson county, bessemer division"]]
        else:
            return [regions_by_name["jefferson county, birmingham division"]]

    # generic matches
    for fmt in [
        # generic city matches
        "City of {city}",
        "Town of {city}",
        "{city} Township",
        "{city}",
        # michigan-specific (try local office *before* county office--mail will get processed faster)
        "{city} City, {county}",
        "{city} City, {county} County",
        "{city} Township, {county}",
        "{city} Township, {county} County",
        # generic county
        "{county}",
        "{county} County",
        # La* -> La *, De* -> De *, Le * -> Le*
        "{county2}",
        "{county2} County",
    ]:
        key = fmt.format(city=city, county=county, county2=county2).lower()
        if key in regions_by_name:
            return [regions_by_name[key]]

    if state == "NY":
        key = nyc_remap.get(county, None)
        if key and key in regions_by_name:
            return [regions_by_name[key]]
        key = nyc_remap.get("%s county" % county, None)
        if key and key in regions_by_name:
            return [regions_by_name[key]]

    # Fall back to looking for nearby offices by lat/lng?
    if location:
        # how many "nearby" offices to return when searching by lat/lng
        max_by_distance = 4
        max_distance = D(mi=100)

        lq = Address.objects.filter(state__code=state)

        # narrow search to ~70 miles in each direction
        lq = lq.filter(location__distance_lte=(location, max_distance))

        # order by distance, limit
        aq = lq.annotate(distance=Distance("location", location)).order_by("distance")[
            :max_by_distance
        ]

        regions = []
        for office_addr in aq.select_related("office__region"):
            regions.append(office_addr.office.region)

        # unique regions only
        final = []
        for a in regions:
            if a not in final:
                final.append(a)
        return final

    return None


@tracer.wrap()
def geocode_to_regions(street, city, state, zipcode):

    addrs = geocode(
        street=street, city=city, state=state, zipcode=zipcode, fields="stateleg",
    )
    if not addrs:
        logger.warning(
            f"address: Unable to geocode ({street}, {city}, {state} {zipcode})"
        )
        statsd.increment("turnout.official.address.failed_geocode")
        return None

    # use the first/best match
    addr = addrs[0]

    county = addr["address_components"].get("county")
    if not county:
        return None
    city = addr["address_components"].get("city")
    location = Point(addr["location"]["lng"], addr["location"]["lat"])

    state_code = addr["address_components"].get("state")
    if state_code != state:
        # if the address match gets the state wrong, return *no* result
        logger.warning(
            f"User-provided state {state} does not match geocoded state in {addr['address_components']}"
        )
        return None

    return match_region(
        city,
        county,
        state,
        location=location,
        districts=addr.get("fields", {}).get("state_legislative_districts", {}),
    )


@tracer.wrap()
def ts_to_region(
    street=None, city=None, state=None, zipcode=None, latitude=None, longitude=None
):
    if latitude and longitude:
        args = {
            "search_type": "point",
            "latitude": latitude,
            "longitude": longitude,
        }
    else:
        args = {
            "search_type": "address",
            "address": f"{street}, {city}, {state} {zipcode}",
            "state": state,
            "zip5": zipcode,
        }
    url = f"{TARGETSMART_DISTRICT_API}?{urlencode({**args})}"
    with tracer.trace("ts.district", service="targetsmartapi"):
        r = requests.get(url, headers={"x-api-key": settings.TARGETSMART_KEY})
    if r.status_code != 200:
        extra = {"url": url, "status_code": r.status_code}
        logger.error(
            "Error querying TS district %{url}s, status code %{status_code}s",
            extra,
            extra=extra,
        )
        sentry_sdk.capture_exception(
            TargetSmartAPIError(f"Error querying {url}, status code {r.status_code}")
        )
        return None
    try:
        match_data = r.json()["match_data"]
        if not match_data:
            return None
        state_code = match_data["vb.vf_reg_cass_state"]
        if state_code != state:
            # if the address match gets the state wrong, return *no* result.
            logger.warning(
                f"User-provided state {state} does not match geocoded state in {match_data}"
            )
            return None
        county = match_data["vb.vf_county_name"].lower()
        city = (
            match_data["vb.vf_municipal_district"].lower()
            or match_data["vb.vf_township"].lower()
        )
    except KeyError:
        extra = {"url": url, "response": r.json()}
        logger.error(
            "Malformed result from TS district %(url)s, response %(response)s",
            extra,
            extra=extra,
        )
        sentry_sdk.capture_exception(
            TargetSmartAPIError(f"Malformed response from {url}, response {r.json()}")
        )
        return None

    queryset = Region.visible.filter(state__code=state_code).order_by("name")

    if state_code in region_name_contains_county + county_method:
        queryset = queryset.filter(name__icontains=county)

    ls = list(queryset)
    regions_by_name = {r.name.lower(): r for r in ls}

    if state_code == "WI":
        # land o' lakes
        city = city.replace("o'", "o' ")

    if state_code == "AL" and county == "Jefferson":
        # warning: I think this isn't super precise since the lat/lng
        # comes from the zip?
        location = Point(
            r.json()["match_data"]["z9_longitude"],
            r.json()["match_data"]["z9_latitude"],
        )
        if al_jefferson_county_bessemer_division(location):
            return [regions_by_name["jefferson county, bessemer division"]]
        else:
            return [regions_by_name["jefferson county, birmingham division"]]

    if state_code == "NY":
        key = nyc_remap.get(county, None)
        if key and key in regions_by_name:
            return [regions_by_name[key]]

    if state_code == "MO":
        if city in ["kansas city", "dist kansas city"]:
            return [regions_by_name["kansas city"]]
        if county == "st louis city":
            return [regions_by_name["saint louis city"]]
        if county == "st louis":
            return [regions_by_name["saint louis county"]]

    if state_code == "IL":
        if county == "city of east st louis":
            county = "city of east saint louis"

    for fmt in [
        # generic city matches
        "City of {city}",
        "Town of {city}",
        "{city} Township",
        "{city}, {county} County",
        "{city}",
        # michigan-specific (try local office *before* county office--mail will get processed faster)
        "{city}, {county} County",
        "{city} Township, {county}",
        "{city} Township, {county} County",
        "{city} City, {county}",
        "{city} City, {county} County",
        # wi
        "City of {city}, {county} County",
        "Town of {city}, {county} County",
        "Village of {city}, {county} County",
        # generic county
        "{county}",
        "{county} County",
    ]:
        key = fmt.format(city=city, county=county).lower()
        if key in regions_by_name:
            return [regions_by_name[key]]
    return []


def get_region_for_address(street, city, state, zipcode, county):
    from django.core.cache import cache

    state = state.upper() if state else state

    if county and state in county_method + ["NY"]:
        # cache county mappings
        cache_key = f"county_to_region_{county}"
        region_id = cache.get(cache_key)
        if region_id:
            region = Region.objects.filter(external_id=region_id).first()
            if region:
                return region
            logger.warning(
                f"Cache had {region_id} for {cache_key} but region DNE; falling back to lookup"
            )

        if not county.endswith(" County"):
            county += " County"

        regions = match_region(city, county, state)
        if regions:
            region_id = regions[0].external_id
            cache.set(cache_key, region_id)
            return regions[0]

        return None

    regions, _ = get_regions_for_address(street, city, state, zipcode)
    if regions:
        return regions[0]
    return None


# Returns (regions, was_geocode_error).
#
# regions maybe None, which indicates we weren't able to narrow down the regions
# at all (and the user probably has to pick their region manually)
@tracer.wrap()
def get_regions_for_address(street, city, state, zipcode):
    state = state.upper() if state else state

    regions = []

    # avoid TS for "easy" addresses, since the geocod.io latency (esp
    # long tail) *seems* to be better.  Also specifically avoid it for AL and AK,
    # where we do matches based on lat/lng or state leg district.  TS
    # works well other "problem" states, though!
    # avoid TS for MA too since I've seen at least one problematic address
    # on a city boundary for which TS returns the wrong municipality/region, whereas
    # geocod.io gets it right.

    # a few states do better with targetsmart.  for the others, we get
    # better results from geocodio.
    prefer_ts = ["VT", "MI"]

    if state not in prefer_ts:
        regions = geocode_to_regions(street, city, state, zipcode)
    if not regions or len(regions) != 1:
        # try targetsmart
        r = ts_to_region(street, city, state, zipcode)
        if r and len(r) == 1:
            regions = r
    if not regions and state in prefer_ts:
        regions = geocode_to_regions(street, city, state, zipcode)

    if not regions:
        logger.warning(f"address: No match for ({street}, {city}, {state} {zipcode})")
        statsd.increment("turnout.official.address.no_region_match")
    elif len(regions) > 1:
        logger.warning(
            f"address: Multiple results for ({street}, {city}, {state} {zipcode}): {regions}"
        )
        statsd.increment("turnout.official.address.multiple_region_matches")

    return (regions, False)
