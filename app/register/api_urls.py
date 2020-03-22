from rest_framework import routers

from .api_views import RegistrationViewSet

router = routers.SimpleRouter()
router.register(r"register", RegistrationViewSet)

app_name = "api_register"
urlpatterns = router.urls
