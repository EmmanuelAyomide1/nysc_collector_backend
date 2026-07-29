from rest_framework import serializers


class DashboardStatisticsSerializer(serializers.Serializer):
    total_members = serializers.IntegerField()
    active_members = serializers.IntegerField()
    inactive_members = serializers.IntegerField()
    total_payment_items = serializers.IntegerField()
    active_payment_items = serializers.IntegerField()
    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    successful_payments_count = serializers.IntegerField()
    pending_payments_count = serializers.IntegerField()
    failed_payments_count = serializers.IntegerField()


class CollectionReportItemSerializer(serializers.Serializer):
    payment_item_id = serializers.UUIDField(source="id")
    name = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField()
    due_date = serializers.DateField(allow_null=True)
    total_members = serializers.IntegerField()
    successful_payments_count = serializers.IntegerField()
    pending_payments_count = serializers.IntegerField()
    failed_payments_count = serializers.IntegerField()
    collected_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    outstanding_count = serializers.IntegerField()


class MonthlyStatisticsItemSerializer(serializers.Serializer):
    month = serializers.CharField()
    total_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    successful_payments_count = serializers.IntegerField()
    pending_payments_count = serializers.IntegerField()
    failed_payments_count = serializers.IntegerField()