from rest_framework import routers

from .api_views import PartnerSlugViewSet

router = routers.SimpleRouter()
router.register(r"id", PartnerSlugViewSet)

app_name = "api_partner"
urlpatterns = router.urls
