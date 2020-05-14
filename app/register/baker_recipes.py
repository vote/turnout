from model_bakery.recipe import Recipe, foreign_key

from action.baker_recipes import action

from .models import Registration

registration = Recipe(Registration, action=foreign_key(action))
