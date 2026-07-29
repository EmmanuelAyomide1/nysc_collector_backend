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


class AdminTransactionSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(source="payment.id", read_only=True)
    payment_status = serializers.CharField(source="payment.status", read_only=True)
    member_email = serializers.EmailField(source="payment.member.email", read_only=True)
    member_name = serializers.SerializerMethodField()
    payment_item_id = serializers.UUIDField(
        source="payment.payment_item.id", read_only=True
    )
    payment_item_name = serializers.CharField(
        source="payment.payment_item.name", read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference",
            "amount",
            "status",
            "channel",
            "gateway_response",
            "paid_at",
            "created_at",
            "payment_id",
            "payment_status",
            "member_email",
            "member_name",
            "payment_item_id",
            "payment_item_name",
        ]
        read_only_fields = fields

    def get_member_name(self, obj):
        member = obj.payment.member
        return f"{member.first_name} {member.last_name}".strip()
