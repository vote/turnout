import pytest
from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient

from common.geocode import API_ENDPOINT, al_jefferson_county_bessemer_division, geocode


def test_well_formed_request(requests_mock):
    settings.GEOCODIO_KEY = "foobar"

    APIClient()
    geocodio_call = requests_mock.register_uri(
        "GET",
        API_ENDPOINT,
        json={
            "input": {
                "address_components": {"zip": "90024", "country": "US"},
                "formatted_address": "90024",
            },
            "results": [
                {
                    "address_components": {
                        "city": "Los Angeles",
                        "county": "Los Angeles County",
                        "state": "CA",
                        "zip": "90024",
                        "country": "US",
                    },
                    "formatted_address": "Los Angeles, CA 90024",
                    "location": {"lat": 34.065729, "lng": -118.434999},
                    "accuracy": 1,
                    "accuracy_type": "place",
                    "source": "TIGER\/Line\u00ae dataset from the US Census Bureau",
                }
            ],
        },
    )

    r = geocode(q="90024")

    assert geocodio_call.called
    assert geocodio_call.last_request.qs == {
        "api_key": [settings.GEOCODIO_KEY],
        "q": ["90024"],
    }
    assert r == [
        {
            "address_components": {
                "city": "Los Angeles",
                "county": "Los Angeles County",
                "state": "CA",
                "zip": "90024",
                "country": "US",
            },
            "formatted_address": "Los Angeles, CA 90024",
            "location": {"lat": 34.065729, "lng": -118.434999},
            "accuracy": 1,
            "accuracy_type": "place",
            "source": "TIGER\/Line\u00ae dataset from the US Census Bureau",
        }
    ]


@pytest.mark.parametrize(
    "location,inside",
    [
        (Point(-86.791934, 33.386778), False),
        (Point(-87.080543, 33.637441), False),
        (Point(-86.889002, 33.362958), True),
        (Point(-86.977017, 33.394062), True),
    ],
)
def test_al_jefferson_county_bessemer_division(location, inside):
    assert al_jefferson_county_bessemer_division(location) == inside
