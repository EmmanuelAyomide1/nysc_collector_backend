from django.contrib import admin

from apps.payments.models import Payment, PaymentItem, Transaction


@admin.register(PaymentItem)
class PaymentItemAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "amount",
        "is_active",
        "due_date",
        "created_by",
        "created_at",
    ]
    list_filter = ["is_active"]
    search_fields = ["name"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "member",
        "payment_item",
        "payment_item__amount",
        "status",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status"]
    search_fields = ["member__email", "payment_item__name"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "payment",
        "amount",
        "status",
        "channel",
        "paid_at",
        "created_at",
    ]
    list_filter = ["status", "channel"]
    search_fields = ["reference", "payment__member__email"]
