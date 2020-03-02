from django.contrib import admin

from election import models


@admin.register(models.State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("code", "name")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.StateInformationFieldType)
class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ("slug", "long_name", "field_format")


@admin.register(models.UpdateNotificationWebhook)
class UpdateNotificationWebhookAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "last_triggered")
