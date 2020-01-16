from rest_framework import routers

from election.api_views import StateFieldsViewSet, StateViewSet

router = routers.SimpleRouter()
router.register(r"states", StateViewSet)
router.register(r"fields", StateFieldsViewSet)
