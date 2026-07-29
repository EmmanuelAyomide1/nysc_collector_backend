from django.urls import path

from apps.reports.views import (
    CollectionReportView,
    DashboardStatisticsView,
    MonthlyStatisticsView,
    PaymentItemReportExportView,
)

app_name = "reports"

urlpatterns = [
    path(
        "dashboard/", DashboardStatisticsView.as_view(), name="dashboard-statistics"
    ),
    path(
        "collections/", CollectionReportView.as_view(), name="collection-report"
    ),
    path(
        "monthly/", MonthlyStatisticsView.as_view(), name="monthly-statistics"
    ),
    path(
        "export/payment-items/<uuid:payment_item_id>/",
        PaymentItemReportExportView.as_view(),
        name="payment-item-export",
    ),
]