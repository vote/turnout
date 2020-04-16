import pytest
from django.forms.models import model_to_dict
from model_bakery import baker

from absentee.contactinfo import (AbsenteeContactInfo,
                                  NoAbsenteeRequestMailingAddress,
                                  get_absentee_contact_info)
from absentee.models import BallotRequest
from common import enums
from event_tracking.models import Event
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS


@pytest.mark.django_db
def test_contact_info_all_in_one_address():
    office = baker.make_recipe("official.office")

    correct_addr = baker.make_recipe("official.absentee_ballot_address", office=office)

    wrong_addr = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=True,
        is_regular_mail=False,
    )

    wrong_addr2 = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=False,
        is_regular_mail=True,
    )

    wrong_addr3 = baker.make_recipe(
        "official.address", process_absentee_requests=True, is_regular_mail=True,
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        mailing_address=ABSENTEE_BALLOT_MAILING_ADDRESS,
        email=correct_addr.email,
        phone=correct_addr.phone,
    )


@pytest.mark.django_db
def test_contact_info_fallback():
    office = baker.make_recipe("official.office")

    first_priority = baker.make_recipe(
        "official.absentee_ballot_address", office=office, email=None, phone=None
    )

    second_priority = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=True,
        is_regular_mail=False,
        email=None,
        phone="+16175552222",
    )

    third_priority = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=False,
        is_regular_mail=False,
        email="test@example.com",
        phone="+16175553333",
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        mailing_address=ABSENTEE_BALLOT_MAILING_ADDRESS,
        email=third_priority.email,
        phone=second_priority.phone,
    )


@pytest.mark.django_db
def test_contact_info_no_email_or_phone():
    office = baker.make_recipe("official.office")

    baker.make_recipe(
        "official.absentee_ballot_address", office=office, email=None, phone=None
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        mailing_address="Right Office\n123 Main Street\nSte. 123\nFoo City, AA 12345",
        email=None,
        phone=None,
    )


@pytest.mark.django_db
def test_contact_info_no_mailing_address():
    office = baker.make_recipe("official.office")

    with pytest.raises(NoAbsenteeRequestMailingAddress):
        wrong_addr1 = baker.make_recipe(
            "official.address",
            office=office,
            process_absentee_requests=True,
            is_regular_mail=False,
        )

        wrong_addr2 = baker.make_recipe(
            "official.address",
            office=office,
            process_absentee_requests=False,
            is_regular_mail=True,
        )

        get_absentee_contact_info(office.region.external_id)


@pytest.mark.django_db
def test_contact_info_address_lines_filtering():
    office = baker.make_recipe("official.office")

    addr = baker.make_recipe(
        "official.absentee_ballot_address", office=office, address3=None
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        mailing_address=f"{addr.address}\n{addr.address2}\n{addr.city.title()}, {addr.state.code} {addr.zipcode}",
        email=addr.email,
        phone=addr.phone,
    )
