from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.text import slugify

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsAdministrator
from apps.payments.models import PaymentItem
from apps.reports.exports import (
    export_payment_item_report_docx,
    export_payment_item_report_pdf,
)
from apps.reports.serializers import (
    CollectionReportItemSerializer,
    DashboardStatisticsSerializer,
    MonthlyStatisticsItemSerializer,
)
from apps.reports.services import (
    get_collection_report,
    get_dashboard_statistics,
    get_monthly_statistics,
)

EXPORT_CONTENT_TYPES = {
    "pdf": "application/pdf",
    "docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
}


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(tags=["Reports"]),
)
class DashboardStatisticsView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        data = get_dashboard_statistics()
        serializer = DashboardStatisticsSerializer(data)
        return Response({"success": True, "data": serializer.data})


class CollectionReportView(generics.ListAPIView):
    serializer_class = CollectionReportItemSerializer
    permission_classes = [IsAdministrator]

    def get_queryset(self):
        return get_collection_report()

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)

        if (
            isinstance(response, Response)
            and 200 <= response.status_code < 300
            and isinstance(response.data, dict)
            and "success" not in response.data
        ):
            response.data = {
                "success": True,
                "data": response.data,
            }

        return response


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(tags=["Reports"]),
)
class MonthlyStatisticsView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        data = get_monthly_statistics()
        serializer = MonthlyStatisticsItemSerializer(data, many=True)
        return Response({"success": True, "data": serializer.data})


@method_decorator(
    name="get",
    decorator=swagger_auto_schema(
        tags=["Reports"],
        manual_parameters=[
            openapi.Parameter(
                "file_format",
                openapi.IN_QUERY,
                description="Export format: 'pdf' (default) or 'docx'.",
                type=openapi.TYPE_STRING,
            ),
        ],
    ),
)
class PaymentItemReportExportView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request, payment_item_id):
        payment_item = get_object_or_404(PaymentItem, pk=payment_item_id)
        # Named "file_format", not "format" — DRF reserves the "format" query
        # param for its own content-negotiation override (URL_FORMAT_OVERRIDE)
        # and raises Http404 if it doesn't match a configured renderer, before
        # this view even runs.
        export_format = request.query_params.get("file_format", "pdf").lower()

        if export_format not in EXPORT_CONTENT_TYPES:
            return Response(
                {"success": False, "message": "file_format must be 'pdf' or 'docx'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generated entirely in memory (see apps/reports/exports.py) and
        # streamed straight to the client — nothing is written to disk.
        if export_format == "docx":
            buffer = export_payment_item_report_docx(payment_item)
        else:
            buffer = export_payment_item_report_pdf(payment_item)

        filename = f"{slugify(payment_item.name)}-payments.{export_format}"
        response = HttpResponse(
            buffer.getvalue(), content_type=EXPORT_CONTENT_TYPES[export_format]
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response