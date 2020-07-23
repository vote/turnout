from django.contrib import admin

from subscription import models


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("months", "cost", "public")


@admin.register(models.Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = (
        "organization_name",
        "website",
        "first_name",
        "last_name",
        "email",
        "status",
    )


@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("subscriber", "created_at", "expires", "product")
