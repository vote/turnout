from django.urls import path
from rest_framework import routers

from .api_views import RegistrationViewSet, StatusViewSet
from .external_views import ExternalRegistrationViewSet, RegistrationResumeView

router = routers.SimpleRouter()
router.register(r"register", RegistrationViewSet)
router.register(r"status", StatusViewSet)
router.register(r"external/request", ExternalRegistrationViewSet)

app_name = "api_register"

urlpatterns = router.urls + [
    path(
        "resume_token/",
        RegistrationResumeView.as_view(),
        name="registration_resume_token",
    )
]
