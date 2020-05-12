import pytest
from model_bakery import baker

from absentee.contactinfo import (
    AbsenteeContactInfo,
    NoAbsenteeRequestMailingAddress,
    get_absentee_contact_info,
)
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS


@pytest.mark.django_db
def test_contact_info_all_in_one_address():
    office = baker.make_recipe("official.office")

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

    correct_addr = baker.make_recipe("official.absentee_ballot_address", office=office)

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        address1=correct_addr.address,
        address2=correct_addr.address2,
        address3=correct_addr.address3,
        city=correct_addr.city.title(),
        state=correct_addr.state.code,
        zipcode=correct_addr.zipcode,
        email=correct_addr.email,
        phone=correct_addr.phone,
        full_address=ABSENTEE_BALLOT_MAILING_ADDRESS,
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
        address1=first_priority.address,
        address2=first_priority.address2,
        address3=first_priority.address3,
        city=first_priority.city.title(),
        state=first_priority.state.code,
        zipcode=first_priority.zipcode,
        email=third_priority.email,
        phone=second_priority.phone,
        full_address=ABSENTEE_BALLOT_MAILING_ADDRESS,
    )


@pytest.mark.django_db
def test_contact_info_no_email_or_phone():
    office = baker.make_recipe("official.office")

    addr = baker.make_recipe(
        "official.absentee_ballot_address", office=office, email=None, phone=None
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        address1=addr.address,
        address2=addr.address2,
        address3=addr.address3,
        city=addr.city.title(),
        state=addr.state.code,
        zipcode=addr.zipcode,
        email=None,
        phone=None,
        full_address=ABSENTEE_BALLOT_MAILING_ADDRESS,
    )


@pytest.mark.django_db
def test_contact_info_no_mailing_address():
    office = baker.make_recipe("official.office")

    with pytest.raises(NoAbsenteeRequestMailingAddress):
        office.address_set.set([])

        get_absentee_contact_info(office.region.external_id)


@pytest.mark.django_db
def test_contact_info_address_lines_filtering():
    office = baker.make_recipe("official.office")

    addr = baker.make_recipe(
        "official.absentee_ballot_address", office=office, address3=None
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        address1=addr.address,
        address2=addr.address2,
        address3=None,
        city=addr.city.title(),
        state=addr.state.code,
        zipcode=addr.zipcode,
        email=addr.email,
        phone=addr.phone,
        full_address="Right Office\n123 Main Street\nFoo City, AA 12345",
    )
