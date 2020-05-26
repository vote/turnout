from rest_framework import routers

from .api_views import SubscriberSlugViewSet

router = routers.SimpleRouter()
router.register(r"id", SubscriberSlugViewSet)

app_name = "api_subscriber"
urlpatterns = router.urls
