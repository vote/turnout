from django.contrib import admin

from multi_tenant import models

from . import leads


class SubscriberSlugInline(admin.TabularInline):
    model = models.SubscriberSlug
    extra = 0


class SubscriptionIntervalInline(admin.TabularInline):
    model = models.SubscriptionInterval
    extra = 0


@admin.register(models.Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    inlines = (SubscriberSlugInline,)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.SubscriberLead)
class SubscriberLeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "slug", "url", "is_c3", "status")

    actions = ["approve_lead", "deny_lead"]

    def approve_lead(self, request, queryset):
        for lead in queryset:
            leads.approve_lead(lead)

    def deny_lead(self, request, queryset):
        for lead in queryset:
            leads.deny_lead(lead)
