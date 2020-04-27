import pytest


@pytest.fixture(autouse=True)
def cdn_settings(settings):
    settings.CLOUD_DETAIL = "Cloud-Detail"
    settings.TAG = "1.2.3"
    settings.BUILD = 10
    settings.ENV = "pytest"
