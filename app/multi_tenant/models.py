from django.core.cache import cache
from django.db import models
from django.utils.functional import cached_property

from common.utils.models import TimestampModel, UUIDModel


class Client(UUIDModel, TimestampModel):
    name = models.CharField(max_length=200)
    url = models.URLField()
    email = models.EmailField(
        max_length=254, null=True, default="turnout@localhost.local"
    )
    privacy_policy = models.URLField(null=True)
    terms_of_service = models.URLField(null=True)
    sms_enabled = models.BooleanField(default=False, null=True)
    sms_checkbox = models.BooleanField(default=True, null=True)
    sms_checkbox_default = models.BooleanField(default=False, null=True)
    sms_disclaimer = models.TextField(blank=True, null=True)
    # In order to create this in the admin, we need blank=True
    default_slug = models.ForeignKey(
        "multi_tenant.SubscriberSlug", null=True, on_delete=models.PROTECT, blank=True
    )

    # Passed to Civis to determine if subscriber's data should be synced to TMC
    sync_tmc = models.BooleanField(default=False, null=True)

    # Determines if we show our own donate asks when a user is interacting with
    # this client.
    is_first_party = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Subscriber"
        verbose_name_plural = "Subscribers"

    def __str__(self):
        return self.name

    @cached_property
    def slug(self):
        return self.default_slug.slug

    @property
    def full_email_address(self) -> str:
        clean_name = self.name.replace('"', "'")
        return f'"{clean_name}" <{self.email}>'

    @property
    def stats(self):
        # NOTE: callers should be able to cope with getting an empty dict here
        return cache.get(f"client.stats/{self.uuid}") or {}


class SubscriberSlug(UUIDModel, TimestampModel):
    subscriber = models.ForeignKey(
        Client, on_delete=models.CASCADE, db_column="partner_id"
    )
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = "multi_tenant_partnerslug"

    def __str__(self):
        return self.slug


class Association(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)


class InviteAssociation(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.Invite", on_delete=models.CASCADE)
