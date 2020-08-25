import urllib.parse
from datetime import date

import pytest
from model_bakery import baker

from absentee.region_links import (
    MOVOTE_BASE_URL,
    MOVOTE_PARAM_ADDR3,
    MOVOTE_PARAM_ADDR12,
    MOVOTE_PARAM_DOB_D,
    MOVOTE_PARAM_DOB_M,
    MOVOTE_PARAM_DOB_Y,
    MOVOTE_PARAM_EMAIL,
    MOVOTE_PARAM_FULL_NAME,
    MOVOTE_PARAM_PHONE,
    build_movote_url,
)

base_url_parsed = urllib.parse.urlparse(MOVOTE_BASE_URL)


def parse_movote_url(url):
    url_parsed = urllib.parse.urlparse(url)

    assert url_parsed.scheme == base_url_parsed.scheme
    assert url_parsed.netloc == base_url_parsed.netloc
    assert url_parsed.path == base_url_parsed.path

    return {k: v for k, v in urllib.parse.parse_qsl(url_parsed.query)}


@pytest.mark.django_db
def test_movote_full():
    assert parse_movote_url(
        build_movote_url(
            baker.make_recipe(
                "absentee.ballot_request",
                first_name="John",
                last_name="Hancock",
                address1="30 Beacon Street",
                address2="#1776",
                city="Boston",
                state=baker.make_recipe("election.state", code="MA"),
                zipcode="02108",
                email="john@hancock.local",
                date_of_birth=date(1737, 1, 23),
                phone="+16175557890",
            )
        )
    ) == {
        MOVOTE_PARAM_FULL_NAME: "John Hancock",
        MOVOTE_PARAM_DOB_M: "1",
        MOVOTE_PARAM_DOB_D: "23",
        MOVOTE_PARAM_DOB_Y: "37",
        MOVOTE_PARAM_ADDR12: "30 Beacon Street #1776",
        MOVOTE_PARAM_ADDR3: "Boston, MA 02108",
        MOVOTE_PARAM_PHONE: "(617) 555-7890",
        MOVOTE_PARAM_EMAIL: "john@hancock.local",
    }


@pytest.mark.django_db
def test_movote_no_addr2():
    assert parse_movote_url(
        build_movote_url(
            baker.make_recipe(
                "absentee.ballot_request",
                first_name="John",
                last_name="Hancock",
                address1="30 Beacon Street",
                address2=None,
                city="Boston",
                state=baker.make_recipe("election.state", code="MA"),
                zipcode="02108",
                email="john@hancock.local",
                date_of_birth=date(1737, 1, 23),
                phone="+16175557890",
            )
        )
    ) == {
        MOVOTE_PARAM_FULL_NAME: "John Hancock",
        MOVOTE_PARAM_DOB_M: "1",
        MOVOTE_PARAM_DOB_D: "23",
        MOVOTE_PARAM_DOB_Y: "37",
        MOVOTE_PARAM_ADDR12: "30 Beacon Street",
        MOVOTE_PARAM_ADDR3: "Boston, MA 02108",
        MOVOTE_PARAM_PHONE: "(617) 555-7890",
        MOVOTE_PARAM_EMAIL: "john@hancock.local",
    }


@pytest.mark.django_db
def test_movote_no_phone():
    assert parse_movote_url(
        build_movote_url(
            baker.make_recipe(
                "absentee.ballot_request",
                first_name="John",
                last_name="Hancock",
                address1="30 Beacon Street",
                address2="#1776",
                city="Boston",
                state=baker.make_recipe("election.state", code="MA"),
                zipcode="02108",
                email="john@hancock.local",
                date_of_birth=date(1737, 1, 23),
                phone=None,
            )
        )
    ) == {
        MOVOTE_PARAM_FULL_NAME: "John Hancock",
        MOVOTE_PARAM_DOB_M: "1",
        MOVOTE_PARAM_DOB_D: "23",
        MOVOTE_PARAM_DOB_Y: "37",
        MOVOTE_PARAM_ADDR12: "30 Beacon Street #1776",
        MOVOTE_PARAM_ADDR3: "Boston, MA 02108",
        MOVOTE_PARAM_EMAIL: "john@hancock.local",
    }


@pytest.mark.django_db
def test_movote_no_mailing():
    assert parse_movote_url(
        build_movote_url(
            baker.make_recipe(
                "absentee.ballot_request",
                first_name="John",
                last_name="Hancock",
                address1="30 Beacon Street",
                address2="#1776",
                city="Boston",
                state=baker.make_recipe("election.state", code="MA"),
                zipcode="02108",
                email="john@hancock.local",
                date_of_birth=date(1737, 1, 23),
                phone="+16175557890",
            )
        )
    ) == {
        MOVOTE_PARAM_FULL_NAME: "John Hancock",
        MOVOTE_PARAM_DOB_M: "1",
        MOVOTE_PARAM_DOB_D: "23",
        MOVOTE_PARAM_DOB_Y: "37",
        MOVOTE_PARAM_ADDR12: "30 Beacon Street #1776",
        MOVOTE_PARAM_ADDR3: "Boston, MA 02108",
        MOVOTE_PARAM_PHONE: "(617) 555-7890",
        MOVOTE_PARAM_EMAIL: "john@hancock.local",
    }
