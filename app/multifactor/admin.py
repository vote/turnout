from django.contrib import admin

from multifactor import models


@admin.register(models.UUIDTOTPDevice)
class TOTPDeviceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "confirmed",
    )
    fieldsets = (
        (None, {"fields": ("user", "throttling_failure_count", "confirmed",)},),
    )
    readonly_fields = ["user"]

    def has_add_permission(self, request):
        return False
