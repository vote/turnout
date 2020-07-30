from django.urls import path
from rest_framework import routers

from .api_views import BallotRequestViewSet, StateMetadataView

router = routers.SimpleRouter()
router.register(r"request", BallotRequestViewSet)


app_name = "api_absentee"
urlpatterns = [
    path("state/<slug:state_code>/", StateMetadataView.as_view(), name="state_metadata")
]

urlpatterns += router.urls
