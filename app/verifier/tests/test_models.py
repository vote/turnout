import pytest

from verifier import models


@pytest.mark.django_db
def test_lookup_str():
    lookup = models.Lookup(first_name="John", last_name="Hancock", state_id="MA")
    assert str(lookup) == "Verification - John Hancock, MA"
