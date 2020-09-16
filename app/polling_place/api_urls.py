from rest_framework import routers

from .api_views import PollingPlaceLookupReportViewSet

router = routers.SimpleRouter()
router.register(r"report", PollingPlaceLookupReportViewSet)

app_name = "api_polling_place"
urlpatterns = router.urls
