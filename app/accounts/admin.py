from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts import models
from multi_tenant.models import Association, InviteAssociation

from .forms import ArticleAdminForm


class AssociationInline(admin.TabularInline):
    model = Association
    extra = 0


@admin.register(models.User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "last_name", "active_client")
    fieldsets = (
        (None, {"fields": ("password", "email", "active_client")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "created_at", "modified_at")}),
    )
    inlines = (AssociationInline,)
    readonly_fields = [
        "email",
        "created_at",
        "modified_at",
    ]
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class InviteAssociationInline(admin.TabularInline):
    model = InviteAssociation
    extra = 0


@admin.register(models.Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "token",
        "consumed_at",
        "expires",
        "expired",
        "primary_client",
    )
    inlines = (InviteAssociationInline,)
    fieldsets = (
        (
            None,
            {"fields": ("token", "email", "expires", "primary_client", "consumed_at",)},
        ),
    )
    form = ArticleAdminForm
    readonly_fields = ["token", "consumed_at"]
