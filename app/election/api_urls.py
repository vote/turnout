from django.urls import path
from rest_framework import routers

from .api_views import StateExternalToolRedirectView, StateFieldsViewSet, StateViewSet

router = routers.SimpleRouter()
router.register(r"state", StateViewSet)
router.register(r"field", StateFieldsViewSet)

app_name = "api_election"
urlpatterns = router.urls + [
    path(
        "state-redirect/<str:state>/<str:slug>/",
        StateExternalToolRedirectView.as_view(),
    ),
]
