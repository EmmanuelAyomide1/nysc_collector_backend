import logging

from django.utils.decorators import method_decorator

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.payments.models import Payment, PaymentItem, Transaction
from apps.common.permissions import IsAdministrator, IsMember
from apps.users.models import CustomUser
from apps.payments.serializers import (
    AdminTransactionSerializer,
    PaymentInitializeSerializer,
    PaymentItemSerializer,
    PaymentSerializer,
    TransactionSerializer,
    VerifyPaymentSerializer,
)
from apps.payments.services import (
    initialize_payment,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)


class PaymentItemListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentItemSerializer

    def get_queryset(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.Role.ADMIN
        ):
            return PaymentItem.objects.all()
        return PaymentItem.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdministrator()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

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


class PaymentItemDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = PaymentItemSerializer

    def get_queryset(self):
        if (
            self.request.user.is_authenticated
            and self.request.user.role == CustomUser.Role.ADMIN
        ):
            return PaymentItem.objects.all()
        return PaymentItem.objects.filter(is_active=True)

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH"):
            return [IsAdministrator()]
        return [IsAuthenticated()]

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


class PaymentHistoryView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Payment.objects.filter(member=self.request.user)
            .select_related("payment_item")
            .prefetch_related("transactions")
        )

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
    decorator=swagger_auto_schema(
        tags=["Payments"],
        manual_parameters=[
            openapi.Parameter(
                "search",
                openapi.IN_QUERY,
                description="Search by reference, member name/email, or payment item name.",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "status",
                openapi.IN_QUERY,
                description="Filter by transaction status (pending, successful, failed).",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "payment_item",
                openapi.IN_QUERY,
                description="Filter by payment item ID.",
                type=openapi.TYPE_STRING,
            ),
        ],
    ),
)
class AdminTransactionListView(generics.ListAPIView):
    serializer_class = AdminTransactionSerializer
    permission_classes = [IsAdministrator]
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "reference",
        "payment__member__email",
        "payment__member__first_name",
        "payment__member__last_name",
        "payment__payment_item__name",
    ]

    def get_queryset(self):
        queryset = Transaction.objects.select_related(
            "payment__member", "payment__payment_item"
        )

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        payment_item = self.request.query_params.get("payment_item")
        if payment_item:
            queryset = queryset.filter(payment__payment_item_id=payment_item)

        return queryset

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
    name="post",
    decorator=swagger_auto_schema(
        tags=["Payments"], request_body=VerifyPaymentSerializer
    ),
)
class PaymentVerificationView(APIView):
    permission_classes = [IsMember]
    serializer_class = VerifyPaymentSerializer

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response(
                {"success": False, "message": "Reference parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.payments.services import verify_payment

        try:
            data = verify_payment(reference)
        except Exception as e:
            logger.exception("Payment verification failed for reference %s", reference)
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"success": True, "data": TransactionSerializer(data).data},
            status=status.HTTP_200_OK,
        )


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(
        request_body=PaymentInitializeSerializer, tags=["Payments"]
    ),
)
class PaymentInitializeView(APIView):
    permission_classes = [IsMember]
    serializer_class = PaymentInitializeSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment_item = serializer.validated_data["payment_item"]

        data = initialize_payment(member=request.user, payment_item=payment_item)

        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


@method_decorator(
    name="post",
    decorator=swagger_auto_schema(tags=["Payments"]),
)
class PaystackWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        signature = request.headers.get("x-paystack-signature", "")
        if not verify_webhook_signature(request.body, signature):
            logger.warning("Rejected Paystack webhook with invalid signature.")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event = request.data
        reference = event.get("data", {}).get("reference")

        if event.get("event") == "charge.success" and reference:
            try:
                from apps.payments.services import _process_reference
                from threading import Thread
                from django.db import transaction

                try:
                    transaction.on_commit(
                        lambda: Thread(
                            target=_process_reference,
                            args=(reference,),
                            daemon=True,
                        ).start()
                    )
                except Exception:
                    logger.exception(
                        "Failed to schedule Paystack webhook job for reference %s",
                        reference,
                    )

            except Exception:
                logger.exception(
                    "Failed to process Paystack webhook for reference %s", reference
                )

        return Response(status=status.HTTP_200_OK)
