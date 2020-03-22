from rest_framework import routers

from .api_views import StateFieldsViewSet, StateViewSet

router = routers.SimpleRouter()
router.register(r"stateinfo", StateViewSet)
router.register(r"fields", StateFieldsViewSet)

app_name = "api_election"
urlpatterns = router.urls
