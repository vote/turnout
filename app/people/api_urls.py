from django.urls import path
from rest_framework import routers

from .api_views import NameOverrideViewSet, OptOutView

router = routers.SimpleRouter()
router.register(r"name-override", NameOverrideViewSet)

app_name = "api_people"
urlpatterns = router.urls + [
    path("opt-out/", OptOutView.as_view()),
]
