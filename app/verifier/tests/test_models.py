import pytest

from verifier import models


@pytest.mark.django_db
def test_lookup_str():
    lookup = models.Lookup(first_name="John", last_name="Tyler", state_id="WI")
    assert str(lookup) == "John Tyler WI"
