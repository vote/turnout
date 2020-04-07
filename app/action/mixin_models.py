from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    pass


class ActionModel(models.Model):
    action = models.OneToOneField("action.Action", on_delete=models.PROTECT, null=True)

    class Meta:
        abstract = True
