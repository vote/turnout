import pytest


@pytest.fixture(autouse=True)
def mask_optimizely(mocker):
    mocker.patch("common.rollouts.PollingConfigManager")
    mocker.patch("common.rollouts.optimizely.Optimizely")
    mocker.patch("common.rollouts.optimizely_client")
