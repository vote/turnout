import pytest
from model_bakery import baker

from election.models import State


@pytest.mark.django_db
def test_state_count():
    assert State.objects.count() == 51
