import logging
from urllib.parse import urlencode

import requests
import sentry_sdk
from django.conf import settings
from django.db import utils
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from common.analytics import statsd
from common.apm import tracer
from official.models import RegionGeomMA, RegionGeomWI

API_ENDPOINT = "https://api.geocod.io/v1.5/geocode"


logger = logging.getLogger("official")


class GeocodioAPIError(Exception):
    pass


class GISDataError(Exception):
    pass


def geocode(**kwargs):
    RETRIES = 2
    TIMEOUT = 2.0

    args = {}
    for k in ["street", "city", "state", "q", "fields"]:
        if k in kwargs:
            args[k] = kwargs[k]
    if "zipcode" in kwargs:
        args["postal_code"] = kwargs["zipcode"]
    url = f"{API_ENDPOINT}?{urlencode({**args, 'api_key': settings.GEOCODIO_KEY})}"
    with statsd.timed("turnout.common.geocode.geocode", sample_rate=0.2):
        retries = Retry(
            total=RETRIES, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
        http = requests.Session()
        http.mount("https://", HTTPAdapter(max_retries=retries))
        try:
            with tracer.trace("geocode", service="geocodioclient"):
                r = http.get(url, timeout=TIMEOUT)
        except Exception as e:
            extra = {"url": API_ENDPOINT, "api_args": str(args), "exception": str(e)}
            logger.warning(
                "Error querying geocodio %(url)s, exception %(exception)s",
                extra,
                extra=extra,
            )
            sentry_sdk.capture_exception(
                GeocodioAPIError(
                    f"Error querying {API_ENDPOINT}, args {args}, exception {str(e)}"
                )
            )
            return None
    if r.status_code != 200:
        extra = {
            "url": API_ENDPOINT,
            "api_args": str(args),
            "status_code": r.status_code,
        }
        logger.warning(
            "Error querying geocodio %(url)s, args %(args)s, status code %(status_code)s",
            extra,
            extra=extra,
        )
        sentry_sdk.capture_exception(
            GeocodioAPIError(
                f"Error querying {API_ENDPOINT}, args {args}, status code {r.status_code}"
            )
        )
        return None
    return r.json().get("results", None)


def wi_location_to_mcd(location):
    """
    query API with official WI state data as of jan 2020
    see: https://data-ltsb.opendata.arcgis.com/datasets/wi-cities-towns-and-villages-january-2020/geoservice

    This same data set can be imported; see scripts/import_region_geom.sh
    """
    try:
        mcds = list(RegionGeomWI.objects.filter(geom__intersects=location))
        if mcds:
            return mcds[0].mcd_name.title()
    except utils.ProgrammingError:
        # table doesn't exist; fall back to querying the API below
        logger.warning(f"Table official_region_geom_wi does not exist")
        sentry_sdk.capture_exception(
            GISDataError(f"Table official_region_geom_wi does not exist")
        )
    return None


def ma_location_to_mcd(location):
    """
    query API with official MA state data as of fall 2018
    see:
      https://www.arcgis.com/home/item.html?id=e847265dcae6420f97b9eb55730a81df
      https://services.arcgis.com/40CMVGZPtmu7aNof/arcgis/rest/services/Massachusetts_Wards_and_Precincts/FeatureServer/0

    This same data set can be imported; see scripts/import_region_geom.sh
    """
    try:
        precincts = list(RegionGeomMA.objects.filter(geom__intersects=location))
        if precincts:
            return precincts[0].town.title()
    except utils.ProgrammingError:
        # table doesn't exist; fall back to querying the API below
        logger.warning(f"Table official_region_geom_ma does not exist")
        sentry_sdk.capture_exception(
            GISDataError(f"Table official_region_geom_ma does not exist")
        )
    return None


def al_jefferson_county_bessemer_division(location):
    """
    Given a point that is within Jefferson county, True if Bessemer division, False if Birmingham division.
    """
    from shapely.geometry import Point, Polygon

    # bessemer cutoff from https://gis.jccal.org/arcgis/rest/services/Political/BessemerCutOff/MapServer/0/query
    bessemer_cutoff = [
        (-87.202590939145551, 33.570360872366507),
        (-87.197031114413534, 33.570403784258737),
        (-87.179598771244613, 33.570114693254951),
        (-87.170204761542934, 33.570028514834412),
        (-87.162295364843828, 33.56993103713922),
        (-87.153303858487689, 33.569940850545869),
        (-87.144483504998163, 33.569923694535859),
        (-87.135671512539616, 33.569772027969861),
        (-87.126883755627532, 33.569583834911398),
        (-87.118161631599037, 33.569361663546978),
        (-87.109523609191967, 33.569162538748586),
        (-87.10037005449233, 33.569168477701766),
        (-87.091259779060223, 33.569278776214226),
        (-87.082779706580894, 33.569170581515152),
        (-87.074222319946514, 33.569040197270745),
        (-87.065284864026367, 33.568999198811333),
        (-87.057168408316528, 33.568958720611533),
        (-87.048510700313244, 33.568785869410156),
        (-87.040045152463563, 33.568699192772172),
        (-87.031014865927133, 33.568537660327742),
        (-87.022010207594164, 33.568298522555672),
        (-87.012939367665908, 33.568294455034177),
        (-87.003927241239964, 33.568140933903287),
        (-86.995493787913475, 33.568151207601581),
        (-86.987027808583903, 33.568077872243272),
        (-86.978315968017483, 33.567975986870252),
        (-86.969618415110105, 33.567869749097916),
        (-86.969679885252305, 33.56061672718392),
        (-86.969736642795297, 33.55335751916305),
        (-86.961059790077357, 33.553283455325094),
        (-86.952337113296238, 33.553096592473075),
        (-86.943582795401326, 33.552918956264008),
        (-86.934868537495305, 33.552762819021488),
        (-86.934853192376664, 33.545533787574314),
        (-86.934822864080246, 33.538290641617039),
        (-86.934984053212247, 33.531024990894892),
        (-86.935048139690551, 33.523786448386836),
        (-86.935118542304338, 33.516120877646443),
        (-86.935133632512532, 33.508501406009096),
        (-86.935198790309116, 33.501229014835779),
        (-86.935276061943327, 33.493888695021582),
        (-86.926563057526394, 33.493802310163971),
        (-86.917888040428551, 33.493727797575389),
        (-86.917363435795977, 33.493720433237741),
        (-86.916222831480127, 33.495181253688372),
        (-86.915309014297918, 33.49632397631909),
        (-86.91226392088744, 33.500125824934287),
        (-86.911918824963223, 33.500587260043382),
        (-86.911283513111883, 33.500309073226262),
        (-86.910753339418619, 33.500125516820461),
        (-86.910301938487265, 33.499936834884082),
        (-86.909245985038481, 33.499529874463924),
        (-86.905899236814548, 33.497732684105948),
        (-86.904814425315692, 33.497716480854557),
        (-86.904800409414875, 33.493771684060356),
        (-86.904860159760204, 33.493187973533132),
        (-86.90486463677459, 33.492533573271125),
        (-86.90489986904592, 33.491459188567092),
        (-86.904909618299428, 33.490033934905846),
        (-86.904915532338649, 33.489169306239909),
        (-86.904921925410576, 33.488234601653772),
        (-86.904925280490104, 33.487744052047141),
        (-86.904987273962576, 33.486832976870033),
        (-86.905020735158672, 33.486015533881904),
        (-86.905028244416286, 33.484917306086565),
        (-86.905040065284425, 33.483188384856845),
        (-86.905047733144443, 33.482066803795199),
        (-86.905029288479355, 33.4806881288279),
        (-86.905061149129764, 33.480104292175234),
        (-86.905123594944968, 33.479006327023257),
        (-86.902812616612209, 33.478987426664595),
        (-86.900674009874038, 33.478973125152393),
        (-86.90057231471377, 33.471724903598947),
        (-86.900466377703296, 33.464465960628772),
        (-86.900511718130474, 33.457164571752323),
        (-86.900353549337098, 33.451028975813102),
        (-86.900341199280959, 33.449984728356355),
        (-86.896997967953524, 33.449855689284405),
        (-86.895860016367735, 33.449786600487933),
        (-86.891582623961412, 33.44961452330466),
        (-86.882782729367818, 33.449312550450294),
        (-86.873909058685456, 33.449093054823372),
        (-86.865009137890368, 33.448767710776124),
        (-86.865164400489874, 33.441632530176399),
        (-86.865078633436696, 33.434160933392391),
        (-86.865351523054116, 33.427123283557329),
        (-86.865289116692153, 33.419710238082644),
        (-86.864967444608126, 33.412533873053299),
        (-86.864909473861132, 33.407044227648875),
        (-86.864900594744668, 33.405194903491356),
        (-86.856196321375322, 33.404989100039622),
        (-86.847485989811929, 33.404770178900087),
        (-86.843921346062871, 33.404653851390492),
        (-86.838827087835554, 33.404582982117233),
        (-86.830125351957591, 33.404416564481018),
        (-86.821536487890455, 33.404182093857962),
        (-86.817127538403582, 33.404097397393031),
        (-86.814108689582767, 33.404087765376993),
        (-86.812880806187934, 33.404069653599237),
        (-86.81289856075162, 33.396764279624463),
        (-86.812951709601862, 33.389483655493748),
        (-86.812962656890093, 33.382227013276108),
        (-86.812954385943414, 33.374994379043308),
        (-86.813045944762663, 33.367701162733489),
        (-86.813111523708713, 33.360390613941547),
    ]

    # make an ugly polygon that contains all of bessemer division but none of
    # birmingham division.
    bessemer_poly = Polygon(
        [
            # start at east endpoint
            (-86.813111523708713, 33.360390613941547),
            # then go way south
            (-86.813111523708713, 30),
            # then way west
            (-90, 30),
            # then north
            (-90, 33.570360872366507),
            # ...and continue at west endpoint
        ]
        + bessemer_cutoff
    )
    p = Point(location.x, location.y)
    if p.within(bessemer_poly):
        return True
    return False
