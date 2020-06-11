from urllib.parse import urlencode

import pytest
import requests

API_URL = "http://localhost:9001/v1/official/address/"

# NOTE: these tests requires a functioning local stack, including a
# populated local database (i.e., usvf import has been run), and hit
# external APIs (geocodio, WI arcgis).

@pytest.mark.parametrize(
    "street,city,state,zipcode,expected",
    [
        # VA
        ("3004 Stony Point Rd", "Richmond", "VA", "23235", [{"name":"City of Richmond","external_id":432959}]),

        # OK
        ("21781 main st", "Howe", "OK", "74940", [{"name":"LeFlore County","external_id":432057}]),

        # TN
        ("101 sunnybrook dr", "Bristol", "TN", "37620", [{"name":"Sullivan County","external_id":432365}]),

        # FL
        ("319 S Brevard Ave", "Arcadia", "FL", "34266", [{"name":"De Soto County","external_id":430666}]),

        # MD
        ("6151 chevy chase dr", "Laurel", "MD", "20707", [{"name":"Prince Georges County","external_id":434812}]),

        # SD
        ("PO Box 1", "Kyle", "SD", "57752", [{"name":"Oglala Lakota County","external_id":434278}]),

        # HI
        ("1525 bernice st", "Honolulu", "HI", "96817", [{"name":"Honolulu, City and County","external_id":430725}]),
        ("1067 california ave", "Wahiawa", "HI", "96786", [{"name":"Honolulu, City and County","external_id":430725}]),

        # "La Foo" counties, which sometimes contract to "LaFoo", "De*" -> "De *"
        ("500 N Moon Mountain Ave", "Quartzsite", "AZ", "85346", [{"name":"La Paz County","external_id":430444}]),
        ("515 E College Dr", "Durango", "CO", "81301", [{'external_id': 430619, 'name': 'La Plata County'}]),
        ("345 Hupp Rd", "La Porte", "IN", "46350", [{'external_id': 431494, 'name': 'La Porte County'}]),
        ("6805 state road 101", "Saint Joe", "IN", "46785", [{"name":"De Kalb County","external_id":431464}]),
        ("1911 Ottawa Ave", "Ottawa", "IL", "61350", [{'external_id': 430825, 'name': 'La Salle County'}]),
        ("803 Pecos St", "Cotulla", "TX", "78014", [{'external_id': 432517, 'name': 'La Salle County'}]),

        # mo
        ("1200 Lynch St", "St. Louis", "MO", "63118", [{'external_id': 433919, 'name': 'Saint Louis City'}]),
        ("7733 Forsyth Blvd", "Clayton", "MO", "63105", [{'external_id': 433920, 'name': 'Saint Louis County'}]),
        ("4109 The Paseo", "Kansas City", "MO", "64110", [{'external_id': 433869, 'name': 'Kansas City'}]),
        ("8881 N Helena Ave", "Kansas City", "MO", "64154", [{'external_id': 433869, 'name': 'Kansas City'}]),
        ("27015 State Rte 92", "Platte City", "MO", "64079", [{'external_id': 433901, 'name': 'Platte County'}]),

        # IL
        ("2621 W 15th Pl", "Chicago", "IL", "60608", [{'external_id': 430783, 'name': 'City of Chicago'}]),
        ("619 Spruce St", "Aurora", "IL", "60506", [{'external_id': 430781, 'name': 'City of Aurora'}]),
        ("160 S Bloomingdale Rd", "Bloomingdale", "IL", "60108", [{'external_id': 430798, 'name': 'DuPage County'}]),
        ("718 S Eldorado Rd", "Bloomington", "IL", "61704", [{'external_id': 430782, 'name': 'City of Bloomington'}]),
        ("1001 N Collett St", "Danville", "IL", "61832", [{'external_id': 430784, 'name': 'City of Danville'}]),
        ("518 N 12th St", "East St Louis", "IL", "62201", [{'external_id': 430785, 'name': 'City of East Saint Louis'}]),
        ("275 S Academy St", "Galesburg", "IL", "61401", [{'external_id': 430786, 'name': 'City of Galesburg'}]),
        ("2305 Charles St", "Rockford", "IL", "61104", [{'external_id': 430787, 'name': 'City of Rockford'}]),

        # al
        ("3083 S Perkins Rd", "Memphis", "TN", "38118", [{'name': 'Shelby County', 'external_id': 432362}]),
        #  birmingham
        ("3530 Lorna Rd", "Hoover", "AL", "35216", [{'name': 'Jefferson County, Birmingham Division', 'external_id': 430406}]),
        ("7127 Shackleford Rd", "Quinton", "AL", "35130", [{'name': 'Jefferson County, Birmingham Division', 'external_id': 430406}]),
        #  bessemer
        ("2651 Laurel Oaks Dr", "Bessemer", "AL", "35022", [{'name': 'Jefferson County, Bessemer Division', 'external_id': 430405}]),
        ("650 Circle Heights Cir", "Bessemer", "AL", "35020", [{'name': 'Jefferson County, Bessemer Division', 'external_id': 430405}]),
        ("8739-8799 Smith Camp Rd", "Adger", "AL", "35006", [{'name': 'Jefferson County, Bessemer Division', 'external_id': 430405}]),
        ("301 Leaf Lake Pkwy", "Birmingham", "AL", "35211", [{'name': 'Jefferson County, Bessemer Division', 'external_id': 430405}]),

        # vt
        ("315 Bridge St", "Huntington", "VT", "05462", [{'name': 'Huntington', 'external_id': 432756}]),
        ("4416 Ethan Allen Hwy", "Georgia", "VT", "05478", [{'name': 'Georgia, Franklin County', 'external_id': 438339}]),
        ("321 Plains Rd", "Georgia", "VT", "05478", [{'name': 'Georgia, Franklin County', 'external_id': 438339}]),
        ("231 Musket Cir", "Milton", "VT", "05468", [{'name': 'Georgia, Franklin County', 'external_id': 438339}]),

        # ak
        ("4101 University Dr", "Anchorage", "AK", "99508", [{'name': 'Region II Elections Office: Anchorage Vicinity', 'external_id': 434823}]),
        ("21 Allakaket Rd", "Allakaket", "AK", "99720", [{'name': 'Regions III Elections Office: Fairbanks, Interior, Eastern Mat-Su & Valdez', 'external_id': 434825}]),
        ("217 Egan Dr", "Valdez", "AK", "99686", [{'name': 'Regions III Elections Office: Fairbanks, Interior, Eastern Mat-Su & Valdez', 'external_id': 434825}]),
        ("100 Main St", "White Mountain", "AK", "99784", [{'name': 'Regions IV Elections Office: Northern, Western & Southwest Alaska & Aleutian Chain', 'external_id': 434826}]),

        # wi
        ("FCHG+H2 Mayville", "Williamstown", "WI", "", [{'external_id': 438099, 'name': 'Village of Kekoskee, Dodge County'}]),
        ("521 Park Ave", "Brokaw", "WI", "54417", [{'external_id': 437323, 'name': 'Village of Maine, Marathon County'}]),
        ("3524 blackhawk dr", "madison", "WI", "53705", [{"name":"Village of Shorewood Hills, Dane County","external_id":438254}]),
        ("W512 County Rd R", "Mondovi", "WI", "54755", [{"name":"Town of Albany, Pepin County","external_id":436428}]),
        ("304 E Main St", "Albany", "WI", "53502", [{"name":"Village of Albany, Green County","external_id":437902}]),
        ("6490 Chippewa Rd", "Land O' Lakes", "WI", "54540", [{'external_id': 437244, 'name': "Town of Land O' Lakes, Vilas County"}]),
        ("14990 Superior St", "Drummond", "WI", "54832", [{'external_id': 436948, 'name': 'Town of Drummond , Bayfield County'}]),
        ("1100 co rd a", "Hudson", "WI", "54016", [{"name":"Town of Saint Joseph, Saint Croix County","external_id":437702}]),

        # or
        ("500 holly st", "ashland", "OR", "97530", [{'name': 'Jackson County', 'external_id': 432109}]),

        # ma
        ("11 saddle club dr", "lexington", "MA", "02420", [{'name': 'Town of Lexington', 'external_id': 431274}]),
        ("175 Grove St", "Cambridge", "MA", "02138", [{'name': 'City of Cambridge', 'external_id': 431101}]),
        ("180 Grove St", "Belmont", "MA", "02138", [{'name': 'Town of Belmont', 'external_id': 431161}]),
        ("16 beach st", "eastham", "ma", "", [{'name': 'Town of Eastham', 'external_id': 431215}]),
        ("85 Treadwell Hollow Rd", "Williamstown", "MA", "01267", [{'external_id': 431441, 'name': 'Town of Williamstown'}]),
        ("554 Sloan Rd", "Williamstown", "MA", "01267", [{'external_id': 431441, 'name': 'Town of Williamstown'}]),
        ("po box 1", "HOUSATONIC", "MA", "01236", [{'name': 'Town of West Stockbridge', 'external_id': 431427}]),
        ("69 pleasant st", "gardner", "MA", "01440", [{"name":"Ctiy of Gardner","external_id":431107}]),

        # mi
        ("301 S 5th St", "Grand Haven", "MI", "49417", [{'external_id': 435266, 'name': 'Grand Haven City, Ottawa County'}]),
        ("2101 168th Ave", "Grand Haven", "MI", "49417", [{'name': 'Grand Haven Township, Ottawa County', 'external_id': 435674}]),
        ("Agate Beach Rd", "Toivola", "MI", "49965", [{'name': 'Stanton Township, Houghton County', 'external_id': 436278}]),
        ("9879 Portage Rd", "Portage", "MI", "49002", [{'name': 'Portage City, Kalamazoo County', 'external_id': 435372}]),
        ("203 E Savidge St", "Spring Lake", "MI", "49456", [{'name': 'Spring Lake Township, Ottawa County', 'external_id': 436262}]),
        ("202 w exchange st", "gobles", "MI", "49055", [{'name': 'Gobles City, Van Buren County', 'external_id': 435264}]),
        ("N9450 Manistique Lakes Rd", "Curtis", "MI", "49820", [{'name': 'Portage Township, Mackinac County', 'external_id': 436124}]),
        ("N 727 Woods Rd", "St Ignace", "MI", "49781", [{'name': 'Moran Township, Mackinac County', 'external_id': 435994}]),
        ("17629 Bay Shore Rd", "Houghton", "MI", "49931", [{'name': 'Stanton Township, Houghton County', 'external_id': 436278}]),
        ("46640 Healy St", "Dodgeville", "MI", "49921", [{'name': 'Portage Township, Houghton County', 'external_id': 436123}]),

        # ny
        ("PO Box 1", "Queens Village", "NY", "11428", [{"name":"New York City: Queens","external_id":433319}]),
        ("20 W 34th St", "New York", "NY", "10001", [{'name': 'New York City: Manhattan', 'external_id': 433320}]),
        ("1050 Clove Rd", "Staten Island", "NY", "10301", [{'name': 'New York City: Staten Island', 'external_id': 433318}]),
        ("5800 20th Ave", "Brooklyn", "NY", "11204", [{'name': 'New York City: Brooklyn', 'external_id': 433317}]),
        ("1825 Eastchester Rd", "The Bronx", "NY", "10461", [{'name': 'New York City: The Bronx', 'external_id': 433316}]),
        ("71-01 Parsons Blvd", "Fresh Meadows", "NY", "11365", [{'name': 'New York City: Queens', 'external_id': 433319}]),
        ("535 Morgan Ave", "Brooklyn", "NY", "11222", [{'name': 'New York City: Brooklyn', 'external_id': 433317}]),
        ("11 Hazen St", "East Elmhurst", "NY", "11370", [{'name': 'New York City: The Bronx', 'external_id': 433316}]),
    ])
def test_full(street, city, state, zipcode, expected):
    r = requests.get(f"{API_URL}?{urlencode({'address1':street,'city': city,'state':state,'zipcode':zipcode})}")
    assert r.status_code == 200
    assert r.json() == expected
