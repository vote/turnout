from rest_framework import routers

from election.api_views import StateFieldsViewSet, StateViewSet
from verifier.api_views import LookupViewSet

router = routers.SimpleRouter()
router.register(r"states", StateViewSet)
router.register(r"fields", StateFieldsViewSet)
router.register(r"lookup", LookupViewSet)
