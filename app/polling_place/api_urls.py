from rest_framework import routers

from .api_views import PollingPlaceLookupViewSet

router = routers.SimpleRouter()
router.register(r"lookup", PollingPlaceLookupViewSet)

app_name = "api_polling_place"
urlpatterns = router.urls
