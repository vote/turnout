from django.contrib import admin

from multi_tenant import models


class SubscriberSlugInline(admin.TabularInline):
    model = models.SubscriberSlug
    extra = 0


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    inlines = (SubscriberSlugInline,)

    def has_delete_permission(self, request, obj=None):
        return False
