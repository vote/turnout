from django.db import models

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
    default_slug = models.ForeignKey(
        "multi_tenant.PartnerSlug", null=True, on_delete=models.PROTECT
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    @property
    def full_email_address(self) -> str:
        clean_name = self.name.replace('"', "'")
        return f'"{clean_name}" <{self.email}>'


class PartnerSlug(UUIDModel, TimestampModel):
    partner = models.ForeignKey(Client, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.slug


class Association(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)


class InviteAssociation(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.Invite", on_delete=models.CASCADE)
