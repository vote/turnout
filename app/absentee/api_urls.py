from rest_framework import routers

from .api_views import BallotRequestViewSet

router = routers.SimpleRouter()
router.register(r"request", BallotRequestViewSet)

app_name = "api_absentee"
urlpatterns = router.urls
