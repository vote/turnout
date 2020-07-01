from django.conf import settings
from optimizely import optimizely
from optimizely.config_manager import PollingConfigManager

conf_manager = PollingConfigManager(
    sdk_key=settings.OPTIMIZELY_SDK_KEY,
    update_interval=settings.OPTIMIZELY_UPDATE_INTERVAL_SECONDS,
)

optimizely_client = optimizely.Optimizely(config_manager=conf_manager)


def flag_enabled_for_state(
    flag: str, state_code: str, user_id: str = "__anonymous__"
) -> bool:
    return optimizely_client.is_feature_enabled(
        flag, user_id=user_id
    ) and optimizely_client.get_feature_variable_boolean(
        flag, state_code, user_id=user_id
    )
