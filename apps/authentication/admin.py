from django.contrib import admin

from apps.authentication.models import Otp


@admin.register(Otp)
class OtpAdmin(admin.ModelAdmin):
    list_display = ["user", "otp", "is_used", "expires_at", "created_at"]
    list_filter = ["is_used"]
    search_fields = ["user__email", "otp"]
    readonly_fields = ["otp", "user", "expires_at", "is_used", "created_at", "updated_at"]
