from rest_framework import routers

from .api_views import LookupViewSet

router = routers.SimpleRouter()
router.register(r"verify", LookupViewSet)

app_name = "api_verifier"
urlpatterns = router.urls
