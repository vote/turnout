from django.db import models


class PartnerModel(models.Model):
    partner = models.ForeignKey(
        "multi_tenant.Client", null=True, on_delete=models.PROTECT
    )

    class Meta:
        abstract = True
