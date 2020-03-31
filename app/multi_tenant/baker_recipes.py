from model_bakery.recipe import Recipe

from multi_tenant import models

client = Recipe(models.Client, name="My Great Organization", url="http://vote.local")
