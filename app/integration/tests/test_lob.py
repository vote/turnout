import datetime

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from model_bakery import baker

from election.models import State
from integration.lob import get_or_create_lob_address, send_letter, verify_address

LOB_VERIFY_ENDPOINT = "https://api.lob.com/v1/us_verifications"


LOB_VERIFY_RESULT = {
    "id": "us_ver_c7cb63d68f8d6",
    "recipient": "LOB.COM",
    "primary_line": "185 BERRY ST STE 6100",
    "secondary_line": "",
    "urbanization": "",
    "last_line": "SAN FRANCISCO CA 94107-1728",
    "deliverability": "deliverable",
    "components": {
        "primary_number": "185",
        "street_predirection": "",
        "street_name": "BERRY",
        "street_suffix": "ST",
        "street_postdirection": "",
        "secondary_designator": "STE",
        "secondary_number": "6100",
        "pmb_designator": "",
        "pmb_number": "",
        "extra_secondary_designator": "",
        "extra_secondary_number": "",
        "city": "SAN FRANCISCO",
        "state": "CA",
        "zip_code": "94107",
        "zip_code_plus_4": "1728",
        "zip_code_type": "standard",
        "delivery_point_barcode": "941071728506",
        "address_type": "commercial",
        "record_type": "highrise",
        "default_building_address": False,
        "county": "SAN FRANCISCO",
        "county_fips": "06075",
        "carrier_route": "C001",
        "carrier_route_type": "city_delivery",
        "latitude": 37.77597542841264,
        "longitude": -122.3929557343685,
    },
    "deliverability_analysis": {
        "dpv_confirmation": "Y",
        "dpv_cmra": "N",
        "dpv_vacant": "N",
        "dpv_active": "Y",
        "dpv_footnotes": ["AA", "BB"],
        "ews_match": False,
        "lacs_indicator": "",
        "lacs_return_code": "",
        "suite_return_code": "",
    },
    "object": "us_verification",
}


LOB_LIST_RESULT = {
    "data": [
        {
            "id": "adr_e68217bd744d65c8",
            "description": "Harry - Office",
            "name": "HARRY ZHANG",
            "company": "LOB",
            "phone": "5555555555",
            "email": "harry@lob.com",
            "address_line1": "185 BERRY ST STE 6110",  # address mismatch!
            "address_line2": None,
            "address_city": "SAN FRANCISCO",
            "address_state": "CA",
            "address_zip": "94107-1741",
            "address_country": "UNITED STATES",
            "metadata": {"va_id": "27035bd3-37ef-410b-8968-cefdda42b017"},
            "date_created": "2019-08-12T00:16:00.361Z",
            "date_modified": "2019-08-12T00:16:00.361Z",
            "object": "address",
        },
        {
            "id": "adr_830bf0eabdaaa409",
            "description": "Harry - Office",
            "name": "HARRY ZHANG",
            "company": "LOB",
            "phone": "5555555555",
            "email": "harry@lob.com",
            "address_line1": "185 BERRY ST STE 6100",
            "address_line2": None,
            "address_city": "SAN FRANCISCO",
            "address_state": "CA",
            "address_zip": "94107-1741",
            "address_country": "UNITED STATES",
            "metadata": {"va_id": "27035bd3-37ef-410b-8968-cefdda42b017"},
            "date_created": "2019-08-07T21:59:46.764Z",
            "date_modified": "2019-08-07T21:59:46.764Z",
            "object": "address",
        },
        {
            "id": "adr_830bf0eadddaa409",
            "description": None,
            "name": settings.RETURN_ADDRESS["name"].upper(),
            "company": None,
            "address_line1": settings.RETURN_ADDRESS["address1"].upper(),
            "address_line2": None,
            "address_city": settings.RETURN_ADDRESS["city"].upper(),
            "address_state": settings.RETURN_ADDRESS["state"].upper(),
            "address_zip": settings.RETURN_ADDRESS["zipcode"].upper(),
            "address_country": "UNITED STATES",
            "metadata": {"va_id": "va_return_addr"},
            "date_created": "2019-08-07T21:59:46.764Z",
            "date_modified": "2019-08-07T21:59:46.764Z",
            "object": "address",
        },
    ],
    "object": "list",
    "next_url": None,
    "previous_url": None,
    "count": 2,
}

LOB_CREATE_RESULT = {
    "id": "adr_d3489cd64c791ab5",
    "name": "John Doe",
    "address_line1": "123 A ST",
    "address_line2": None,
    "address_city": "ANYTOWN",
    "address_state": "CA",
    "address_zip": "12345-1111",
    "address_country": "UNITED STATES",
    "metadata": {"va_id": "bar",},
    "date_created": "2017-09-05T17:47:53.767Z",
    "date_modified": "2017-09-05T17:47:53.767Z",
    "object": "address",
}

LOB_LETTER_CREATE_RESULT = {
    "id": "ltr_4868c3b754655f90",
    "description": "Demo Letter",
    "metadata": {},
    "to": {
        "id": "adr_bae820679f3f536b",
        "description": None,
        "name": "HARRY ZHANG",
        "company": None,
        "phone": None,
        "email": None,
        "address_line1": "185 BERRY ST STE 6100",
        "address_line2": None,
        "address_city": "SAN FRANCISCO",
        "address_state": "CA",
        "address_zip": "94107-1741",
        "address_country": "UNITED STATES",
        "metadata": {},
        "date_created": "2017-09-05T15:54:53.264Z",
        "date_modified": "2017-09-05T15:54:53.264Z",
        "deleted": True,
        "object": "address",
    },
    "from": {
        "id": "adr_210a8d4b0b76d77b",
        "description": None,
        "name": "LEORE AVIDAR",
        "company": None,
        "phone": None,
        "email": None,
        "address_line1": "185 BERRY ST STE 6100",
        "address_line2": None,
        "address_city": "SAN FRANCISCO",
        "address_state": "CA",
        "address_zip": "94107-1741",
        "address_country": "UNITED STATES",
        "metadata": {},
        "date_created": "2017-09-05T15:54:53.264Z",
        "date_modified": "2017-09-05T15:54:53.264Z",
        "deleted": True,
        "object": "address",
    },
    "color": True,
    "double_sided": True,
    "address_placement": "top_first_page",
    "return_envelope": False,
    "perforated_page": None,
    "custom_envelope": None,
    "extra_service": None,
    "mail_type": "usps_first_class",
    "url": "https://lob-assets.com/letters/ltr_4868c3b754655f90.pdf?expires=1540372221&signature=qjatwPv3jPJlQayBYQeIm42qtavaP7q",
    "template_id": None,
    "carrier": "USPS",
    "tracking_number": None,
    "tracking_events": [],
    "thumbnails": [
        {
            "small": "https://lob-assets.com/letters/ltr_4868c3b754655f90_thumb_small_1.png?expires=1540372221&signature=GgFjpAduYT13yFYAJWVCAp8YRMRD7m1",
            "medium": "https://lob-assets.com/letters/ltr_4868c3b754655f90_thumb_medium_1.png?expires=1540372221&signature=0avnWJxyfhZ8Ccfd9m0ERYG1kSCJ0W2",
            "large": "https://lob-assets.com/letters/ltr_4868c3b754655f90_thumb_large_1.png?expires=1540372221&signature=T8EwlE6P7QIKt3GIHU1Z1xrArNDZOkf",
        }
    ],
    "merge_variables": {"name": "Harry"},
    "expected_delivery_date": "2017-09-12",
    "date_created": "2017-09-05T15:54:53.346Z",
    "date_modified": "2017-09-05T15:54:53.346Z",
    "send_date": "2017-09-05T15:54:53.346Z",
    "object": "letter",
}


@pytest.fixture
def mock_cache(mocker):
    mocker.patch("integration.lob.cache.get", return_value=None)
    mocker.patch("integration.lob.cache.set", return_value=None)


def test_verify_address(requests_mock):
    lob_call = requests_mock.register_uri(
        "POST", LOB_VERIFY_ENDPOINT, json=LOB_VERIFY_RESULT,
    )

    deliverable, canonical = verify_address(
        address1="185 Berry St",
        address2="Ste 6100",
        city="San Francisco",
        state="CA",
        zipcode="94107-1728",
    )
    assert deliverable == True
    assert canonical == LOB_VERIFY_RESULT["components"]


def test_new_lob_address(requests_mock, mock_cache):
    lob_call = requests_mock.register_uri(
        "GET",
        "https://api.lob.com/v1/addresses?metadata%5Bva_id%5D=bar",
        json=LOB_LIST_RESULT,
    )
    lob_call2 = requests_mock.register_uri(
        "POST", "https://api.lob.com/v1/addresses", json=LOB_CREATE_RESULT,
    )
    r = get_or_create_lob_address(
        "bar", "John Doe", "123 A St", None, "Anytown", "CA", "12345"
    )
    assert r == "adr_d3489cd64c791ab5"


def test_existing_lob_address(requests_mock, mock_cache):
    lob_call = requests_mock.register_uri(
        "GET",
        "https://api.lob.com/v1/addresses?metadata%5Bva_id%5D=27035bd3-37ef-410b-8968-cefdda42b017",
        json=LOB_LIST_RESULT,
    )
    r = get_or_create_lob_address(
        "27035bd3-37ef-410b-8968-cefdda42b017",
        "Harry Zhang",
        "185 Berry St Ste 6100",
        None,
        "San Francisco",
        "CA",
        "94107-1741",
    )
    assert r == "adr_830bf0eabdaaa409"


@pytest.mark.django_db
def test_send_letter(requests_mock, mock_cache):
    pdf = baker.make_recipe(
        "storage.ballot_request_form",
        file=SimpleUploadedFile("foo.pdf", b"these are the file contents!",),
    )
    ballot_request = baker.make_recipe(
        "absentee.ballot_request",
        first_name="Harry",
        middle_name=None,
        last_name="Zhang",
        address1="123 A St",
        address2=None,
        city="San Francisco",
        state=State(code="CA"),
        zipcode="94107",
        request_mailing_address1="185 Berry St Ste 6100",
        request_mailing_address2=None,
        request_mailing_city="San Francisco",
        request_mailing_state=State(code="CA"),
        request_mailing_zipcode="94107",
        uuid="27035bd3-37ef-410b-8968-cefdda42b017",
        result_item_mail=pdf,
    )

    requests_mock.register_uri(
        "GET",
        "https://api.lob.com/v1/addresses?metadata%5Bva_id%5D=va_return_addr",
        json=LOB_LIST_RESULT,
    )
    requests_mock.register_uri(
        "GET",
        f"https://api.lob.com/v1/addresses?metadata%5Bva_id%5D={ballot_request.uuid}",
        json=LOB_LIST_RESULT,
    )
    requests_mock.register_uri(
        "POST", "https://api.lob.com/v1/letters", json=LOB_CREATE_RESULT,
    )

    before = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    send_date = send_letter(ballot_request)
    after = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    assert send_date > before
    assert send_date < after
