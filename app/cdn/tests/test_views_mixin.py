import pytest
from rest_framework.test import APIClient

from election.api_views import StateViewSet


@pytest.mark.django_db
def test_mixin_single_object():
    client = APIClient()
    response = client.get("/v1/election/state/IL/")

    header_tags = response.get("Cache-Tag").split(",")
    response_tags = response.cache_tags

    assert "topytestil" in header_tags
    assert "IL" in response_tags
    assert "topytestwi" not in header_tags
    assert "WI" not in response_tags

    assert "topytestelection" in header_tags
    assert "election" in response_tags
    assert "topyteststate" in header_tags
    assert "state" in response_tags
    assert "topytestelectionapi_views" in header_tags
    assert "election.api_views" in response_tags


@pytest.mark.django_db
def test_mixin_multiple_objects():
    client = APIClient()
    response = client.get("/v1/election/state/")

    header_tags = response.get("Cache-Tag").split(",")
    response_tags = response.cache_tags

    assert "topytestil" in header_tags
    assert "IL" in response_tags
    assert "topytestwi" in header_tags
    assert "WI" in response_tags


@pytest.mark.django_db
def test_model_cache_tags(mocker):
    mock_cache_tags = mocker.patch.object(
        StateViewSet, "cache_tags", new=["Lincoln", "Washington"], create=True
    )

    client = APIClient()
    response = client.get("/v1/election/state/IL/")

    header_tags = response.get("Cache-Tag").split(",")
    response_tags = response.cache_tags

    assert "topytestil" in header_tags
    assert "IL" in response_tags
    assert "topytestlincoln" in header_tags
    assert "Lincoln" in response_tags
    assert "topytestwashington" in header_tags
    assert "Washington" in response_tags
