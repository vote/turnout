import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .rollouts import (
    get_feature,
    get_feature_bool,
    get_feature_int,
    get_feature_str,
    get_optimizely_version,
)
from .tasks import test_optimizely as test_optimizely_task

logger = logging.getLogger("common")


@api_view(["GET"])
@permission_classes([AllowAny])
def test_optimizely(request):
    feature = request.GET.get("feature", "test_optimizely")
    var = request.GET.get("var", "var")

    logger.info(
        f"test_optimizely endpoint: version {get_optimizely_version()}, feature {feature}={get_feature(feature)}, var {var}={get_feature_bool(feature, var)}"
    )

    test_optimizely_task.delay(feature, var)
    return Response(
        {
            "feature": feature,
            "var": var,
            "overall": get_feature(feature),
            "as_bool": get_feature_bool(feature, var),
            "as_int": get_feature_int(feature, var),
            "as_str": get_feature_str(feature, var),
            "version": get_optimizely_version(),
        }
    )
