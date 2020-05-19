from django.contrib import admin

from storage import models


@admin.register(models.StorageItem)
class StorageItemAdmin(admin.ModelAdmin):
    list_display = ("uuid", "email", "token", "created_at")
    search_fields = ("email",)
