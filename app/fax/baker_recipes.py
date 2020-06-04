from model_bakery.recipe import Recipe, foreign_key

from common import enums
from storage.baker_recipes import ballot_request_form

from .models import Fax

fax = Recipe(Fax, status=enums.FaxStatus.PENDING)
