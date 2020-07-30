from model_bakery.recipe import Recipe, foreign_key

from accounts.baker_recipes import user
from apikey import models
from multi_tenant.baker_recipes import client

apikey = Recipe(
    models.ApiKey, subscriber=foreign_key(client), created_by=foreign_key(user)
)
