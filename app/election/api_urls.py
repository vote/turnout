from rest_framework import routers

from .api_views import StateFieldsViewSet, StateViewSet

router = routers.SimpleRouter()
router.register(r"state", StateViewSet)
router.register(r"field", StateFieldsViewSet)

app_name = "api_election"
urlpatterns = router.urls
