import secrets

from django.db import models

from common.utils.models import TimestampModel, UUIDModel
from multi_tenant.mixins_models import SubscriberModel

from .crypto import hash_key_secret

# From python docs: https://docs.python.org/3/library/secrets.html#how-many-bytes-should-tokens-use
SECRET_TOKEN_BYTES = 32


def secret_token() -> str:
    return secrets.token_urlsafe(SECRET_TOKEN_BYTES)


class ApiKey(SubscriberModel, UUIDModel, TimestampModel):
    created_by = models.ForeignKey(
        "accounts.User", null=True, on_delete=models.SET_NULL, related_name="+"
    )

    deactivated_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    secret = models.TextField(null=True, default=secret_token)

    class Meta(object):
        ordering = ["-created_at"]

    def __str__(self):
        return f"API Key for {self.subscriber} - {self.pk}"

    def hashed_secret(self) -> str:
        return hash_key_secret(self.secret)
