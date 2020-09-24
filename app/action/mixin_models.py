import urllib.parse
from typing import Any, List, Tuple

from django.db import models


class ActionModel(models.Model):
    action = models.OneToOneField(
        "action.Action", on_delete=models.PROTECT, null=True, db_index=True
    )
    sms_opt_in_subscriber = models.BooleanField(
        null=True, default=False, db_column="sms_opt_in_partner"
    )

    class Meta:
        abstract = True

    def get_fields(self) -> List[Tuple[(str, Any)]]:
        return [
            (field.verbose_name, field.value_from_object(self))
            for field in self.__class__._meta.fields
        ]

    def get_query_params(self) -> str:
        query_param_dict = {
            "first_name": self.first_name,  # type: ignore
            "last_name": self.last_name,  # type: ignore
            "address1": self.address1,  # type: ignore
            "address2": self.address2,  # type: ignore
            "city": self.city,  # type: ignore
            "state": self.state_id,  # type: ignore
            "zipcode": self.zipcode,  # type: ignore
            "month_of_birth": f"{self.date_of_birth.month:02}",  # type: ignore
            "day_of_birth": f"{self.date_of_birth.day:02}",  # type: ignore
            "year_of_birth": f"{self.date_of_birth.year}",  # type: ignore
            "email": self.email,  # type: ignore
            "phone": self.phone,  # type: ignore
            "subscriber": self.subscriber.default_slug,  # type: ignore
        }
        return urllib.parse.urlencode({k: v for k, v in query_param_dict.items() if v})
