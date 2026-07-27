from rest_framework import serializers

from apps.payments.models import Payment, PaymentItem, Transaction


class PaymentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentItem
        fields = [
            "id",
            "name",
            "description",
            "amount",
            "is_active",
            "due_date",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class PaymentInitializeSerializer(serializers.Serializer):
    payment_item = serializers.PrimaryKeyRelatedField(
        queryset=PaymentItem.objects.filter(is_active=True)
    )


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "amount",
            "status",
            "channel",
            "paid_at",
            "created_at",
        ]
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    payment_item = PaymentItemSerializer(read_only=True)
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "payment_item",
            "status",
            "paid_at",
            "created_at",
            "transactions",
        ]
        read_only_fields = fields


class VerifyPaymentSerializer(serializers.Serializer):
    reference = serializers.CharField(max_length=255)
