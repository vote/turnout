import pytest
from model_bakery import baker

from absentee.contactinfo import AbsenteeContactInfo, get_absentee_contact_info
from official.baker_recipes import ABSENTEE_BALLOT_MAILING_ADDRESS


@pytest.mark.django_db
def test_contact_info_all_in_one_address():
    office = baker.make_recipe("official.office")

    wrong_addr = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=True,
        is_physical=False,
    )

    wrong_addr2 = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=False,
        is_physical=True,
    )

    wrong_addr3 = baker.make_recipe(
        "official.address", process_absentee_requests=True, is_physical=True,
    )

    correct_addr = baker.make_recipe(
        "official.absentee_ballot_address", office=office, is_physical=True
    )

    contact_info = get_absentee_contact_info(office.region.external_id)

    assert contact_info == AbsenteeContactInfo(
        address=correct_addr,
        email=correct_addr.email,
        phone=correct_addr.phone,
        fax=correct_addr.fax,
    )

    assert contact_info.full_address == ABSENTEE_BALLOT_MAILING_ADDRESS
    assert contact_info.address1 == correct_addr.address
    assert contact_info.address2 == correct_addr.address2
    assert contact_info.address3 == correct_addr.address3
    assert (
        contact_info.city_state_zip
        == f"{correct_addr.city.title()}, {correct_addr.state.code} {correct_addr.zipcode}"
    )


@pytest.mark.django_db
def test_contact_info_fallback():
    office = baker.make_recipe("official.office")

    first_priority = baker.make_recipe(
        "official.absentee_ballot_address",
        office=office,
        email=None,
        phone=None,
        fax=None,
        is_physical=True,
    )

    second_priority = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=True,
        is_physical=False,
        email=None,
        phone="+16175552222",
        fax=None,
    )

    third_priority = baker.make_recipe(
        "official.address",
        office=office,
        process_absentee_requests=False,
        is_physical=False,
        email="test@example.com",
        phone="+16175553333",
        fax="+16175554444",
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        address=first_priority,
        email=third_priority.email,
        phone=second_priority.phone,
        fax=third_priority.fax,
    )


@pytest.mark.django_db
def test_contact_info_no_email_or_phone():
    office = baker.make_recipe("official.office")

    addr = baker.make_recipe(
        "official.absentee_ballot_address",
        office=office,
        email=None,
        phone=None,
        fax=None,
    )

    assert get_absentee_contact_info(office.region.external_id) == AbsenteeContactInfo(
        address=addr, email=None, phone=None, fax=None
    )


@pytest.mark.django_db
def test_contact_info_no_mailing_address():
    office = baker.make_recipe("official.office")
    office.address_set.set([])

    contact_info = get_absentee_contact_info(office.region.external_id)
    assert contact_info == AbsenteeContactInfo(
        address=None, email=None, phone=None, fax=None
    )

    assert contact_info.full_address is None
    assert contact_info.address1 is None
    assert contact_info.address2 is None
    assert contact_info.address3 is None
    assert contact_info.city_state_zip is None


@pytest.mark.django_db
def test_contact_info_address_lines_filtering():
    office = baker.make_recipe("official.office")

    addr = baker.make_recipe(
        "official.absentee_ballot_address", office=office, address3=None
    )

    assert (
        get_absentee_contact_info(office.region.external_id).full_address
        == "Right Office\n123 Main Street\nFoo City, AA 12345"
    )
