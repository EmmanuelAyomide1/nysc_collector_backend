from django.urls import path

from apps.payments.views import (
    PaymentHistoryView,
    PaymentInitializeView,
    PaymentItemListCreateView,
    PaymentVerificationView,
    PaystackWebhookView,
)

app_name = "payments"

urlpatterns = [
    path(
        "items/", PaymentItemListCreateView.as_view(), name="payment-item-list-create"
    ),
    path("initialize/", PaymentInitializeView.as_view(), name="payment-initialize"),
    path("verify/", PaymentVerificationView.as_view(), name="payment-verify"),
    path("history/", PaymentHistoryView.as_view(), name="payment-history"),
    path("webhook/", PaystackWebhookView.as_view(), name="paystack-webhook"),
]
