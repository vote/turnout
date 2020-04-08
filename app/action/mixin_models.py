from typing import Any, List, Tuple

from django.db import models


class ActionModel(models.Model):
    action = models.OneToOneField("action.Action", on_delete=models.PROTECT, null=True)

    class Meta:
        abstract = True

    def get_fields(self) -> List[Tuple[(str, Any)]]:
        return [
            (field.verbose_name, field.value_from_object(self))
            for field in self.__class__._meta.fields
        ]
