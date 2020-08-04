from django.contrib import admin

from apikey import models


@admin.register(models.ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "created_by",
        "deactivated_by",
        "description",
        "subscriber",
    )
