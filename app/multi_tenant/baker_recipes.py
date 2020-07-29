from model_bakery.recipe import Recipe, foreign_key

from multi_tenant import models

client = Recipe(models.Client, name="My Great Organization", url="http://vote.local")

subscriberslug = Recipe(
    models.SubscriberSlug, slug="greatorg", subscriber=foreign_key(client)
)
