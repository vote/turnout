from model_bakery.recipe import Recipe, foreign_key

from election.models import State

from .models import Address, Office, Region

region = Recipe(Region)
office = Recipe(Office, region=foreign_key(region))
address = Recipe(
    Address, phone="+16175551234", fax="+16175555678", office=foreign_key(office)
)

absentee_ballot_address = Recipe(
    Address,
    phone="+16175551234",
    fax="+16175555678",
    office=foreign_key(office),
    process_absentee_requests=True,
    is_regular_mail=True,
    email="right@example.com",
    address="Right Office",
    address2="123 Main Street",
    address3="Ste. 123",
    city="FOO CITY",
    state=foreign_key(Recipe(State, code="AA")),
    zipcode="12345",
)

ABSENTEE_BALLOT_MAILING_ADDRESS = (
    "Right Office\n123 Main Street\nSte. 123\nFoo City, AA 12345"
)

ABSENTEE_BALLOT_MAILING_CITY_STATE_ZIP = "Foo City, AA 12345"
