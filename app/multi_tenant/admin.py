from django.contrib import admin

from multi_tenant import models


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "url")

    def has_delete_permission(self, request, obj=None):
        return False
