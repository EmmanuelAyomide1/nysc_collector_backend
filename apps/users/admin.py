from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ["email"]
    list_display = [
        "email",
        "batch",
        "code_no",
        "first_name",
        "last_name",
        "role",
        "is_active",
        "is_staff",
        "created_at",
    ]
    search_fields = [
        "email",
        "batch__name",
        "batch__year",
        "code_no",
        "first_name",
        "last_name",
    ]
    actions = ["make_active", "make_inactive"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone_number", "batch", "code_no")},
        ),
        (
            "Role & permissions",
            {
                "fields": (
                    "role",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "batch",
                    "code_no",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    @admin.action(description="Deactivate selected custom users")
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Activate selected custom users")
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
