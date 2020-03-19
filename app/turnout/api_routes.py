from rest_framework import routers

from election.api_views import StateFieldsViewSet, StateViewSet
from register.api_views import RegistrationViewSet
from verifier.api_views import LookupViewSet

router = routers.SimpleRouter()
router.register(r"states", StateViewSet)
router.register(r"fields", StateFieldsViewSet)
router.register(r"lookup", LookupViewSet)
router.register(r"register", RegistrationViewSet)
