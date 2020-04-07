from rest_framework import routers

from .api_views import TrackViewSet

router = routers.SimpleRouter()
router.register(r"track", TrackViewSet)

app_name = "api_event_tracking"
urlpatterns = router.urls
