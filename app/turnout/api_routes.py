from rest_framework import routers

from election.api_views import StateViewSet

router = routers.SimpleRouter()
router.register(r"states", StateViewSet)
