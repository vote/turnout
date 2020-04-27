import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_middleware():
    client = APIClient()
    response = client.get("/v1/election/state/IL/")

    header_tags = response.get("Cache-Tag").split(",")
    response_tags = response.cache_tags

    assert "topytestil" in header_tags
    assert "IL" in response_tags

    assert "topytestdetail_cloud-detail" in header_tags
    assert "detail_Cloud-Detail" in response_tags
    assert "topytesttag_123" in header_tags
    assert "tag_1.2.3" in response_tags
    assert "topytestbuild_10" in header_tags
    assert "build_10" in response_tags
    assert "topytestenv_pytest" in header_tags
    assert "env_pytest" in response_tags
