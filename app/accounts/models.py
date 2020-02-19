from datetime import timedelta

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django_smalluuid.models import SmallUUIDField, uuid_default

from common.utils.models import TimestampModel, UUIDModel
from multi_tenant.models import Association


class TurnoutUserManager(auth_models.UserManager):
    def create_user(self, password, email, client=None):
        from multi_tenant.models import Client, Association

        if not client:
            client = Client.objects.first()
        new_user = self.model(email=email, active_client=client)
        new_user.set_password(password)
        new_user.save()
        Association(client=client, user=new_user).save()
        return new_user

    def create_superuser(self, password, email, client=None):
        from multi_tenant.models import Client, Association

        if not client:
            client = Client.objects.first()
        new_user = self.model(
            email=email, is_staff=True, is_superuser=True, active_client=client
        )
        new_user.set_password(password)
        new_user.save()
        Association(client=client, user=new_user).save()
        return new_user


class User(
    UUIDModel,
    TimestampModel,
    auth_models.AbstractBaseUser,
    auth_models.PermissionsMixin,
):
    is_staff = models.BooleanField(_("Staff Status"), default=False)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    email = models.EmailField(_("Email Address"), editable=False, unique=True)
    first_name = models.CharField(_("First Name"), max_length=100, blank=True)
    last_name = models.CharField(_("Last Name"), max_length=200, blank=True)
    clients = models.ManyToManyField(
        "multi_tenant.Client", through="multi_tenant.Association"
    )
    active_client = models.ForeignKey(
        "multi_tenant.Client", related_name="active_client", on_delete=models.PROTECT,
    )

    objects = TurnoutUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta(object):
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["created_at"]

    def __unicode__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        return self.email


def expire_date_time():
    return now() + timedelta(days=settings.INVITE_EXPIRATION_DAYS)


class Invite(UUIDModel, TimestampModel):
    email = models.EmailField()
    token = SmallUUIDField(default=uuid_default(), editable=False)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, editable=False)
    expires = models.DateTimeField(default=expire_date_time)
    consumed_at = models.DateTimeField(null=True, editable=False)
    clients = models.ManyToManyField(
        "multi_tenant.Client", through="multi_tenant.InviteAssociation"
    )
    primary_client = models.ForeignKey(
        "multi_tenant.Client", related_name="invited_client", on_delete=models.PROTECT,
    )

    class Meta(object):
        verbose_name = _("Invite")
        verbose_name_plural = _("Invites")
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.email} {self.token}"

    @property
    def expired(self):
        return self.expires <= now()

    def consume_invite(self, user):
        new_associations = []
        new_associations.append(Association(client=self.primary_client, user=user))
        for client in self.clients.exclude(pk=self.primary_client.pk):
            new_associations.append(Association(client=client.pk, user=user))
        Association.objects.bulk_create(new_associations)

        Invite.objects.filter(email__iexact=user.email).update(
            user=user, consumed_at=now()
        )

    def get_absolute_url(self):
        return reverse("accounts:consume_invite", kwargs={"slug": self.token})
