from typing import TYPE_CHECKING

from django.db import models
from django.template.defaultfilters import pluralize
from phonenumber_field.modelfields import PhoneNumberField

from common import enums
from common.fields import TurnoutEnumField
from common.utils.models import SearchableModel, TimestampModel, UUIDModel
from multi_tenant.invite import invite_user

from .tasks import send_organization_welcome_notification

if TYPE_CHECKING:
    # One models.py importing from another can cause circular import hell
    from multi_tenant.models import Client


class Product(UUIDModel, TimestampModel):
    months = models.PositiveIntegerField(null=True, blank=True)
    cost = models.PositiveIntegerField(null=True)
    public = models.BooleanField(null=True, default=True)

    class Meta:
        ordering = ["public", "months"]

    def __str__(self):
        return f"{self.months} month{pluralize(self.months)} at ${self.cost} per month (billed in advance)"


class Interest(
    SearchableModel("organization_name", "first_name", "last_name", "email"),  # type: ignore
    UUIDModel,
    TimestampModel,
):
    organization_name = models.TextField(null=True)
    website = models.URLField(null=True)
    first_name = models.TextField(null=True)
    last_name = models.TextField(null=True)
    email = models.EmailField(null=True)
    phone = PhoneNumberField(blank=True, null=True)
    product = models.ForeignKey(Product, null=True, on_delete=models.SET_NULL)
    nonprofit = models.BooleanField(null=True)
    ein = models.TextField(null=True, blank=True)
    status = TurnoutEnumField(
        enums.SubscriptionInterestStatus,
        default=enums.SubscriptionInterestStatus.PENDING,
        null=True,
    )
    reject_reason = models.TextField(null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.organization_name} Interest Submission"

    @property
    def consumed(self):
        return self.status == enums.SubscriptionInterestStatus.SUBSCRIBED

    def consume(self, subscriber: "Client", initial_user_email: str, slug: str) -> None:
        from multi_tenant.models import SubscriberSlug

        self.status = enums.SubscriptionInterestStatus.SUBSCRIBED
        self.save()
        subscriber_slug = SubscriberSlug.objects.create(
            slug=slug, subscriber=subscriber
        )
        subscriber.default_slug = subscriber_slug
        subscriber.save()
        sub = Subscription.objects.create(
            subscriber=subscriber, product=self.product, interest=self,
        )

        invite_user(initial_user_email, subscriber)
        send_organization_welcome_notification.delay(subscriber.pk, initial_user_email)


class Subscription(UUIDModel, TimestampModel):
    subscriber = models.ForeignKey("multi_tenant.Client", on_delete=models.PROTECT)
    product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.SET_NULL
    )
    interest = models.ForeignKey(
        Interest, null=True, blank=True, on_delete=models.SET_NULL
    )
    expires = models.DateField(null=True, blank=True, db_index=True)

    def __str__(self):
        return f"{self.subscriber} {self.expires}"
