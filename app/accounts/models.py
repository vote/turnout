from django.contrib.auth import models as auth_models
from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.utils.models import TimestampModel, UUIDModel


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
