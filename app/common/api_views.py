import logging

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .rollouts import get_feature, get_feature_bool, get_optimizely_version

logger = logging.getLogger("common")


@api_view(["GET"])
@permission_classes([AllowAny])
def test_optimizely(request):
    logger.info(
        f"test_optimizely endpoint: version {get_optimizely_version()}, feature {get_feature('test_optimizely')}, var {get_feature_bool('test_optimizely', 'var')}"
    )
    return Response(
        {
            "feature": get_feature("test_optimizely"),
            "var": get_feature_bool("test_optimizely", "var"),
            "version": get_optimizely_version(),
        }
    )
