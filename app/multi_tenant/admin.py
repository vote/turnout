from django.contrib import admin

from multi_tenant import models


class PartnerSlugInline(admin.TabularInline):
    model = models.PartnerSlug
    extra = 0


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    inlines = (PartnerSlugInline,)

    def has_delete_permission(self, request, obj=None):
        return False
