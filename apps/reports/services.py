from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncMonth

from apps.payments.models import Payment, PaymentItem
from apps.users.models import CustomUser


def get_dashboard_statistics():
    members = CustomUser.objects.filter(role=CustomUser.Role.MEMBER)
    total_members = members.count()
    active_members = members.filter(is_active=True).count()

    total_payment_items = PaymentItem.objects.count()
    active_payment_items = PaymentItem.objects.filter(is_active=True).count()

    successful_payments = Payment.objects.filter(status=Payment.Status.SUCCESSFUL)
    total_collected = (
        successful_payments.aggregate(total=Sum("payment_item__amount"))["total"] or 0
    )

    return {
        "total_members": total_members,
        "active_members": active_members,
        "inactive_members": total_members - active_members,
        "total_payment_items": total_payment_items,
        "active_payment_items": active_payment_items,
        "total_collected": total_collected,
        "successful_payments_count": successful_payments.count(),
        "pending_payments_count": Payment.objects.filter(
            status=Payment.Status.PENDING
        ).count(),
        "failed_payments_count": Payment.objects.filter(
            status=Payment.Status.FAILED
        ).count(),
    }


def get_collection_report():
    active_members_count = CustomUser.objects.filter(
        role=CustomUser.Role.MEMBER, is_active=True
    ).count()

    items = list(
        PaymentItem.objects.annotate(
            successful_payments_count=Count(
                "payments",
                filter=Q(payments__status=Payment.Status.SUCCESSFUL),
                distinct=True,
            ),
            pending_payments_count=Count(
                "payments",
                filter=Q(payments__status=Payment.Status.PENDING),
                distinct=True,
            ),
            failed_payments_count=Count(
                "payments",
                filter=Q(payments__status=Payment.Status.FAILED),
                distinct=True,
            ),
            paid_members_count=Count(
                "payments__member",
                filter=Q(payments__status=Payment.Status.SUCCESSFUL),
                distinct=True,
            ),
        )
    )

    for item in items:
        item.total_members = active_members_count
        item.collected_amount = item.successful_payments_count * item.amount
        item.outstanding_count = max(
            active_members_count - item.paid_members_count, 0
        )

    return items


def get_monthly_statistics():
    monthly = (
        Payment.objects.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(
            total_collected=Sum(
                "payment_item__amount", filter=Q(status=Payment.Status.SUCCESSFUL)
            ),
            successful_payments_count=Count(
                "id", filter=Q(status=Payment.Status.SUCCESSFUL)
            ),
            pending_payments_count=Count(
                "id", filter=Q(status=Payment.Status.PENDING)
            ),
            failed_payments_count=Count(
                "id", filter=Q(status=Payment.Status.FAILED)
            ),
        )
        .order_by("month")
    )

    return [
        {
            "month": entry["month"].strftime("%Y-%m"),
            "total_collected": entry["total_collected"] or 0,
            "successful_payments_count": entry["successful_payments_count"],
            "pending_payments_count": entry["pending_payments_count"],
            "failed_payments_count": entry["failed_payments_count"],
        }
        for entry in monthly
    ]