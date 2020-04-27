import pytest
from model_bakery import baker


@pytest.mark.django_db
def test_purge_cdn_tags(settings, mocker):
    settings.CLOUDFLARE_ENABLED = True
    settings.CLOUDFLARE_ZONE = "zone123"
    settings.CLOUDFLARE_TOKEN = "token456"

    mock_cloudflare_api_client = mocker.Mock()
    cloudflare_patch = mocker.patch("cdn.utils.CloudFlare")
    cloudflare_patch.CloudFlare.return_value = mock_cloudflare_api_client

    information = baker.make_recipe("election.markdown_information")

    cloudflare_patch.CloudFlare.assert_called_once_with(token="token456")
    mock_cloudflare_api_client.zones.purge_cache.delete.assert_called_once_with(
        identifier1="zone123",
        data={
            "tags": [
                "topyteststate",
                "topyteststateinformationfield",
                "topyteststateinformationfieldtype",
            ]
        },
    )

    information.text = "New Text"
    information.save()

    assert mock_cloudflare_api_client.zones.purge_cache.delete.call_count == 2
    assert information.state_id == "XX"
    mock_cloudflare_api_client.zones.purge_cache.delete.assert_called_with(
        identifier1="zone123", data={"tags": ["topytestxx"]}
    )


@pytest.mark.django_db
def test_cloudflare_disabled(settings, mocker):
    settings.CLOUDFLARE_ENABLED = False
    cloudflare_patch = mocker.patch("cdn.utils.CloudFlare")
    information = baker.make_recipe("election.markdown_information")
    information.text = "New Text"
    information.save()

    assert not cloudflare_patch.CloudFlare.called
