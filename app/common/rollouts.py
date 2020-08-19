from django.conf import settings
from optimizely import optimizely
from optimizely.config_manager import PollingConfigManager

conf_manager = PollingConfigManager(
    sdk_key=settings.OPTIMIZELY_SDK_KEY,
    update_interval=settings.OPTIMIZELY_UPDATE_INTERVAL_SECONDS,
    url_template="https://optimizely.s3.amazonaws.com/datafiles/{sdk_key}.json",
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


def get_feature(flag: str, user_id: str = "__anonymous__") -> bool:
    return optimizely_client.is_feature_enabled(flag, user_id=user_id)


def get_feature_int(flag: str, var: str, user_id: str = "__anonymous__") -> bool:
    if optimizely_client.is_feature_enabled(flag, user_id=user_id):
        return optimizely_client.get_feature_variable_integer(
            flag, var, user_id=user_id
        )
    else:
        return None


def get_feature_bool(flag: str, var: str, user_id: str = "__anonymous__") -> bool:
    if optimizely_client.is_feature_enabled(flag, user_id=user_id):
        return optimizely_client.get_feature_variable_boolean(
            flag, var, user_id=user_id
        )
    else:
        return None
