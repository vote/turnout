from rest_framework import routers

from .api_views import RegistrationViewSet, StatusViewSet

router = routers.SimpleRouter()
router.register(r"register", RegistrationViewSet)
router.register(r"status", StatusViewSet)

app_name = "api_register"
urlpatterns = router.urls
