import hashlib
import hmac
import logging
import uuid
import requests

from django.conf import settings
from django.utils import timezone

from rest_framework.exceptions import APIException

from apps.common.constants import PAYSTACK_BASE_URL
from apps.payments.models import Payment, PaymentItem, Transaction

logger = logging.getLogger(__name__)

from threading import Thread
from django.db import transaction, close_old_connections


def _process_reference(reference):
    close_old_connections()
    try:
        verify_payment(reference)
    except Exception:
        logger.exception(
            "Failed to process Paystack webhook for reference %s", reference
        )
    finally:
        close_old_connections()


class PaystackError(APIException):
    status_code = 502
    default_detail = "Unable to reach the payment provider. Please try again."
    default_code = "paystack_error"


def _headers():
    return {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }


def initialize_payment(member, payment_item: "PaymentItem"):
    payment = Payment.objects.create(member=member, payment_item=payment_item)
    reference = f"NYSC-{uuid.uuid4().hex}"

    try:
        response = requests.post(
            f"{PAYSTACK_BASE_URL}/transaction/initialize",
            headers=_headers(),
            json={
                "email": member.email,
                "amount": int(payment_item.amount * 100),
                "reference": reference,
                "metadata": {"payment_id": str(payment.id)},
            },
            timeout=15,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error("Paystack initialize request failed: %s", exc)
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        raise PaystackError("Unable to reach the payment provider. Please try again.")

    if not response.ok or not data.get("status"):
        logger.error("Paystack initialize failed for payment %s: %s", payment.id, data)
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])
        raise PaystackError(data.get("message", "Unable to initialize payment."))

    transaction = Transaction.objects.create(
        payment=payment,
        reference=reference,
        amount=payment_item.amount,
        raw_response=data,
    )

    logger.info(
        "Initialized Paystack transaction %s for payment %s", reference, payment.id
    )

    return {
        "payment_id": str(payment.id),
        "reference": transaction.reference,
        "authorization_url": data["data"]["authorization_url"],
        "access_code": data["data"]["access_code"],
    }


def verify_payment(reference):
    try:
        transaction = Transaction.objects.select_related("payment").get(
            reference=reference
        )
    except Transaction.DoesNotExist:
        logger.error("Paystack verify requested for unknown reference %s", reference)
        raise PaystackError("Transaction not found.")

    if transaction.status == Transaction.Status.SUCCESSFUL:
        return transaction

    try:
        response = requests.get(
            f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
            headers=_headers(),
            timeout=15,
        )
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error("Paystack verify request failed for %s: %s", reference, exc)
        raise PaystackError("Unable to reach the payment provider. Please try again.")

    if not response.ok or not data.get("status"):
        logger.error("Paystack verify failed for %s: %s", reference, data)
        raise PaystackError(data.get("message", "Unable to verify transaction."))

    _apply_transaction_result(transaction, data["data"])
    return transaction


def _apply_transaction_result(transaction, tx_data):
    paystack_status = tx_data.get("status")
    transaction.gateway_response = tx_data.get("gateway_response", "")
    transaction.channel = tx_data.get("channel", "")
    transaction.raw_response = tx_data

    if paystack_status == "success":
        transaction.status = Transaction.Status.SUCCESSFUL
        transaction.paid_at = tx_data.get("paid_at") or timezone.now()
    elif paystack_status in ("failed", "abandoned", "reversed"):
        transaction.status = Transaction.Status.FAILED
    else:
        transaction.status = Transaction.Status.PENDING

    transaction.save(
        update_fields=[
            "status",
            "channel",
            "gateway_response",
            "raw_response",
            "paid_at",
        ]
    )

    payment = transaction.payment
    if transaction.status == Transaction.Status.SUCCESSFUL:
        payment.status = Payment.Status.SUCCESSFUL
        payment.paid_at = transaction.paid_at
        payment.save(update_fields=["status", "paid_at"])
    elif (
        transaction.status == Transaction.Status.FAILED
        and payment.status != Payment.Status.SUCCESSFUL
    ):
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status"])

    logger.info(
        "Transaction %s resolved to status %s",
        transaction.reference,
        transaction.status,
    )


def verify_webhook_signature(payload, signature):
    if not signature:
        return False

    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha512,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
