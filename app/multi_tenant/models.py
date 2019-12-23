from django.db import models

from common.utils.models import TimestampModel, UUIDModel


class Client(UUIDModel, TimestampModel):
    name = models.CharField(max_length=200)
    url = models.URLField()


class Association(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)
