from django.contrib import admin

from multi_tenant import models
from subscription import models as subscription_models


class SubscriberSlugInline(admin.TabularInline):
    model = models.SubscriberSlug
    extra = 0


class SubscriptionInline(admin.TabularInline):
    model = subscription_models.Subscription
    extra = 0


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "default_slug", "status", "has_api_access")
    inlines = (SubscriberSlugInline,)

    def has_delete_permission(self, request, obj=None):
        return False
