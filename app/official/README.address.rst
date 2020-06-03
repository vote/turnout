

/v1/official/address
====================

We need to map an address to a LEO 'region' (per USVF record
terminology).


By county
---------

These states have LEOs associated with each county (or, in LA's case, "Parish").

AR, AZ, CA, CO, DC, DE, FL, GA, ID, IN, KS, KY, LA, MN, MS, MT, NC, ND, NE, NJ, NM, NV, OH, OK, OR, SC, SD, TN, TX, UT, WA, WV, WY, WY


County with city outliers
-------------------------

MD, PA
------

These are mostly by county, with a few city outliers, so we need to check for 'City of %s' etc first.

IL
--

There are 6 cities that have their own county (named "City of %s").

AK
--

5 regions.  These mostly map to state leg districts, except for certain towns that
would be in IV but are in III instead.  See

  http://www.elections.alaska.gov/Core/contactregionalelectionsoffices.php
  http://www.elections.alaska.gov/doc/forms/H32-Comm.pdf

AL
--

Mostly by county, except that Jefferson county has two divisions: Bessemer and Birmingham.  The
dividing line is described by

  https://gis.jccal.org/arcgis/rest/services/Political/BessemerCutOff/MapServer/0/query

CT
--

"Town of %s"

MO
--

By county, with two city outliers:

* Kansas City has its own region, regardless of which county the address is in.
* St Louis has is a city (with its own region) and a county (with its own region).

RI
--

"Town of %s" and "City of %s"

NH
--

"Town of %s" and "City of %s"

MA
--

"Town of %s" and "City of %s"

NY
--

County, except NYC burrough names are used instead of county names.

                "New York County": "New York City: Manhattan",
                "Kings County": "New York City: Brooklyn",
                "Bronx County": "New York City: The Bronx",
                "Queens County": "New York City: Queens",
                "Richmond County": "New York City: Staten Island",

MI
--

There are two layers of election offices: by county ("%s County"), and
by city ("City of %s, %s County") or township ("%s Township, %s
County").  I called a random LEO and they said that the forms are
processed by the local office.  Forms sent to the county office will
be forwarded to the town office, but as a result it will take longer
for them to be processed.

WI
--

Any of "City of %s, %s County", "Town of %s, %s County", "Village of %s, %s County".

Unfortunately this can't simply be matched by the mailing address returned by geocod.io because in some
cases villages or towns are embedded inside a city.  We can use a state API at

  https://data-ltsb.opendata.arcgis.com/datasets/wi-cities-towns-and-villages-january-2020/geoservice

to get the legal MCD designation and match that.

Also note that in some cases there are multiple instances of the same town/village/city in different counties,
so the county portion of the region name must be matched as well.


VT
--

Bare names that appear to be a mix of city/town or county names.


ME
--

Bare names, also "%s Township".



Fallback to lat/lng
===================

If we aren't able to find a good match against a county or city name
or using some external API, we can use the lat/lng of the address to
find the closest LEOs and let the user choose.  This appears to only
be necessary in a few outlier states in New England, and only when the
address it outside of a larger city or town.


Other sources of data
=====================

In 2011 the census had a project to collect all voting district boundaries ("VTDs").  Shapefiles are available at 

  https://www2.census.gov/geo/tiger/TIGER2012/VTD/
  https://catalog.data.gov/dataset/tiger-line-shapefile-2012-series-information-file-for-the-2010-census-voting-district-state-bas1c9a6

The main problem with this data is it may not be up to date.  In MA's case, for example, we have

  https://docs.digital.mass.gov/dataset/massgis-data-wards-and-precincts

The other challenge is just that the shapefiles are for individual
precincts that would need to be merged and mapped to regions.  From
looking at just the WI data, I found a huge number of typos and other
minor problems with the data (e.g., Villages that have merged into
neighboring Villages)--the WI API is more accurate and is up to date.

In principle, these shapefiles could be gathered, cleaned up, and
carefully mapped to the USVF data set, but it would be a lot of work
and only really help for very rural New England addresses.
