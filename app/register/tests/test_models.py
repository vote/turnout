import pytest

from register import models


@pytest.mark.django_db
def test_registration_str():
    registration = models.Registration(
        first_name="John", last_name="Hancock", state_id="MA"
    )
    assert str(registration) == "Registration - John Hancock, MA"
