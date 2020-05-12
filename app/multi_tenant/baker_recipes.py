from model_bakery.recipe import Recipe, foreign_key

from multi_tenant import models

client = Recipe(
    models.Client,
    name="My Great Organization",
    url="http://vote.local",
)

partnerslug = Recipe(models.PartnerSlug, slug="greatorg", partner=foreign_key(client))
