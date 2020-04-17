from typing import TYPE_CHECKING, Type

from django.db import models
from enumfields.fields import EnumFieldMixin

if TYPE_CHECKING:
    from enumfields import Enum


class TurnoutEnumField(EnumFieldMixin, models.TextField):
    def __init__(self, enum: Type["Enum"], **options) -> None:
        super().__init__(enum, **options)  # type: ignore
