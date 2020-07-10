import pytest
from model_bakery import baker

from official.models import Region


@pytest.fixture
def florida_regions():
    florida = baker.make_recipe("election.state", code="FL")

    regions = [
        Region(
            external_id=430654, name="Alachua County", county="Alachua", state=florida
        ),
        Region(external_id=430655, name="Baker County", county="Baker", state=florida),
        Region(external_id=430656, name="Bay County", county="Bay", state=florida),
        Region(
            external_id=430657, name="Bradford County", county="Bradford", state=florida
        ),
        Region(
            external_id=430658, name="Brevard County", county="Brevard", state=florida
        ),
        Region(
            external_id=430659, name="Broward County", county="Broward", state=florida
        ),
        Region(
            external_id=430660, name="Calhoun County", county="Calhoun", state=florida
        ),
        Region(
            external_id=430661,
            name="Charlotte County",
            county="Charlotte",
            state=florida,
        ),
        Region(
            external_id=430662, name="Citrus County", county="Citrus", state=florida
        ),
        Region(external_id=430663, name="Clay County", county="Clay", state=florida),
        Region(
            external_id=430664, name="Collier County", county="Collier", state=florida
        ),
        Region(
            external_id=430665, name="Columbia County", county="Columbia", state=florida
        ),
        Region(
            external_id=430666, name="De Soto County", county="De Soto", state=florida
        ),
        Region(external_id=430667, name="Dixie County", county="Dixie", state=florida),
        Region(external_id=430668, name="Duval County", county="Duval", state=florida),
        Region(
            external_id=430669, name="Escambia County", county="Escambia", state=florida
        ),
        Region(
            external_id=430670, name="Flagler County", county="Flagler", state=florida
        ),
        Region(
            external_id=430671, name="Franklin County", county="Franklin", state=florida
        ),
        Region(
            external_id=430672, name="Gadsden County", county="Gadsden", state=florida
        ),
        Region(
            external_id=430673,
            name="Gilchrist County",
            county="Gilchrist",
            state=florida,
        ),
        Region(
            external_id=430674, name="Glades County", county="Glades", state=florida
        ),
        Region(external_id=430675, name="Gulf County", county="Gulf", state=florida),
        Region(
            external_id=430676, name="Hamilton County", county="Hamilton", state=florida
        ),
        Region(
            external_id=430677, name="Hardee County", county="Hardee", state=florida
        ),
        Region(
            external_id=430678, name="Hendry County", county="Hendry", state=florida
        ),
        Region(
            external_id=430679, name="Hernando County", county="Hernando", state=florida
        ),
        Region(
            external_id=430680,
            name="Highlands County",
            county="Highlands",
            state=florida,
        ),
        Region(
            external_id=430681,
            name="Hillsborough County",
            county="Hillsborough",
            state=florida,
        ),
        Region(
            external_id=430682, name="Holmes County", county="Holmes", state=florida
        ),
        Region(
            external_id=430683,
            name="Indian River County",
            county="Indian River",
            state=florida,
        ),
        Region(
            external_id=430684, name="Jackson County", county="Jackson", state=florida
        ),
        Region(
            external_id=430685,
            name="Jefferson County",
            county="Jefferson",
            state=florida,
        ),
        Region(
            external_id=430686,
            name="Lafayette County",
            county="Lafayette",
            state=florida,
        ),
        Region(external_id=430687, name="Lake County", county="Lake", state=florida),
        Region(external_id=430688, name="Lee County", county="Lee", state=florida),
        Region(external_id=430689, name="Leon County", county="Leon", state=florida),
        Region(external_id=430690, name="Levy County", county="Levy", state=florida),
        Region(
            external_id=430691, name="Liberty County", county="Liberty", state=florida
        ),
        Region(
            external_id=430692, name="Madison County", county="Madison", state=florida
        ),
        Region(
            external_id=430693, name="Manatee County", county="Manatee", state=florida
        ),
        Region(
            external_id=430694, name="Marion County", county="Marion", state=florida
        ),
        Region(
            external_id=430695, name="Martin County", county="Martin", state=florida
        ),
        Region(
            external_id=430696,
            name="Miami-Dade County",
            county="Miami-Dade",
            state=florida,
        ),
        Region(
            external_id=430697, name="Monroe County", county="Monroe", state=florida
        ),
        Region(
            external_id=430698, name="Nassau County", county="Nassau", state=florida
        ),
        Region(
            external_id=430699, name="Okaloosa County", county="Okaloosa", state=florida
        ),
        Region(
            external_id=430700,
            name="Okeechobee County",
            county="Okeechobee",
            state=florida,
        ),
        Region(
            external_id=430701, name="Orange County", county="Orange", state=florida
        ),
        Region(
            external_id=430702, name="Osceola County", county="Osceola", state=florida
        ),
        Region(
            external_id=430703,
            name="Palm Beach County",
            county="Palm Beach",
            state=florida,
        ),
        Region(external_id=430704, name="Pasco County", county="Pasco", state=florida),
        Region(
            external_id=430705, name="Pinellas County", county="Pinellas", state=florida
        ),
        Region(external_id=430706, name="Polk County", county="Polk", state=florida),
        Region(
            external_id=430707, name="Putnam County", county="Putnam", state=florida
        ),
        Region(
            external_id=430708,
            name="Santa Rosa County",
            county="Santa Rosa",
            state=florida,
        ),
        Region(
            external_id=430709, name="Sarasota County", county="Sarasota", state=florida
        ),
        Region(
            external_id=430710, name="Seminole County", county="Seminole", state=florida
        ),
        Region(
            external_id=430711,
            name="Saint Johns County",
            county="Saint Johns",
            state=florida,
        ),
        Region(
            external_id=430712,
            name="Saint Lucie County",
            county="Saint Lucie",
            state=florida,
        ),
        Region(
            external_id=430713, name="Sumter County", county="Sumter", state=florida
        ),
        Region(
            external_id=430714, name="Suwannee County", county="Suwannee", state=florida
        ),
        Region(
            external_id=430715, name="Taylor County", county="Taylor", state=florida
        ),
        Region(external_id=430716, name="Union County", county="Union", state=florida),
        Region(
            external_id=430717, name="Volusia County", county="Volusia", state=florida
        ),
        Region(
            external_id=430718, name="Wakulla County", county="Wakulla", state=florida
        ),
        Region(
            external_id=430719, name="Walton County", county="Walton", state=florida
        ),
        Region(
            external_id=430720,
            name="Washington County",
            county="Washington",
            state=florida,
        ),
    ]

    Region.objects.bulk_create(regions)

    return regions
