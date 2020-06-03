from django.urls import path
from rest_framework import routers

from .api_views import RegionDetailViewSet, StateRegionsViewSet, address_regions

router = routers.SimpleRouter()
router.register(r"region", RegionDetailViewSet, basename="region")

app_name = "api_official"
urlpatterns = router.urls + [
    path(
        "state/<slug:state>/",
        StateRegionsViewSet.as_view({"get": "list"}),
        name="state_regions",
    ),
    path("address/", address_regions, name="address_regions",),
]
