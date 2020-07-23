from model_bakery.recipe import Recipe

from accounts import models

user = Recipe(models.User, first_name="Joe", last_name="Smith",)
