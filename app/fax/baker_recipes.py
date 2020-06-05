from model_bakery.recipe import Recipe

from common import enums

from .models import Fax

fax = Recipe(Fax, status=enums.FaxStatus.PENDING)
