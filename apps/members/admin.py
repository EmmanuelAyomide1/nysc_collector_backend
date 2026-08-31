from django.contrib import admin

from .models import Batch


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ("year", "name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("year", "name")
