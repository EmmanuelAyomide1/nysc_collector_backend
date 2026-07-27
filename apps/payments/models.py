from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.users.models import CustomUser


class PaymentItem(BaseModel):
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    is_active = models.BooleanField(default=True)
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_items",
    )

    def __str__(self):
        return self.name


class Payment(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"

    member = models.ForeignKey(
        CustomUser, on_delete=models.PROTECT, related_name="payments"
    )
    payment_item = models.ForeignKey(
        PaymentItem, on_delete=models.PROTECT, related_name="payments"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.member.email} - {self.payment_item.name} ({self.status})"


class Transaction(BaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="transactions"
    )
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    channel = models.CharField(max_length=50, blank=True)
    gateway_response = models.CharField(max_length=255, blank=True)
    raw_response = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.reference} ({self.status})"
