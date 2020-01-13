from rest_framework import routers

from election.api_views import StateViewSet, StateFieldsViewSet

router = routers.SimpleRouter()
router.register(r"states", StateViewSet)
router.register(r"fields", StateFieldsViewSet)
