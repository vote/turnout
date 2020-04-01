from django.db import models

from common.utils.models import TimestampModel, UUIDModel


class Client(UUIDModel, TimestampModel):
    name = models.CharField(max_length=200)
    url = models.URLField()
    email = models.EmailField(
        max_length=254, null=True, default="turnout@localhost.local"
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.name

    @property
    def full_email_address(self) -> str:
        clean_name = self.name.replace('"', "'")
        return f'"{clean_name}" <{self.email}>'


class Association(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE)


class InviteAssociation(UUIDModel, TimestampModel):
    client = models.ForeignKey("multi_tenant.Client", on_delete=models.CASCADE)
    user = models.ForeignKey("accounts.Invite", on_delete=models.CASCADE)
