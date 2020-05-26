from django.db import models


class SubscriberModel(models.Model):
    subscriber = models.ForeignKey(
        "multi_tenant.Client",
        null=True,
        on_delete=models.PROTECT,
        db_column="partner_id",
    )

    class Meta:
        abstract = True
