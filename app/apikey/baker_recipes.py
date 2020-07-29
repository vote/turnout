from model_bakery.recipe import Recipe, foreign_key

from apikey import models
from multi_tenant.baker_recipes import client
from accounts.baker_recipes import user

apikey = Recipe(
    models.ApiKey, subscriber=foreign_key(client), created_by=foreign_key(user)
)
