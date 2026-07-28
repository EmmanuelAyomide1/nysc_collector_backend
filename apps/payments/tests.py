import hashlib
import hmac
import json
from decimal import Decimal
from unittest import mock

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.payments.models import Payment, PaymentItem, Transaction
from apps.payments.services import (
    PaystackError,
    initialize_payment,
    verify_payment,
    verify_webhook_signature,
)

User = get_user_model()


def make_user(email="member@example.com", role=User.Role.MEMBER, **overrides):
    fields = {
        "password": "S0me-Str0ng-Pass!",
        "batch": "A1",
        "code_no": 1000,
        "first_name": "Chidi",
        "last_name": "Payer",
        "role": role,
    }
    fields.update(overrides)
    return User.objects.create_user(email=email, **fields)


def make_payment_item(name="CDS Dues", amount="500.00", is_active=True, **overrides):
    fields = {"amount": amount, "is_active": is_active}
    fields.update(overrides)
    item = PaymentItem.objects.create(name=name, **fields)
    item.refresh_from_db()
    return item


def mock_response(ok=True, json_data=None):
    response = mock.Mock()
    response.ok = ok
    response.json.return_value = json_data or {}
    return response


class PaymentItemListCreateViewTests(APITestCase):
    url = "/api/payments/items/"

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=2000, is_staff=True
        )
        self.member = make_user(email="member@example.com", code_no=2001)

    def test_list_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_returns_active_items(self):
        make_payment_item(name="Active Item", is_active=True)
        make_payment_item(name="Inactive Item", is_active=False)

        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [item["name"] for item in response.data["data"]["results"]]
        self.assertEqual(names, ["Active Item"])

    def test_admin_can_create_payment_item(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url, {"name": "New Item", "amount": "750.00"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        item = PaymentItem.objects.get(name="New Item")
        self.assertEqual(item.created_by, self.admin)

    def test_member_cannot_create_payment_item(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url, {"name": "New Item", "amount": "750.00"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_name_rejected(self):
        make_payment_item(name="Existing Item")

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url, {"name": "Existing Item", "amount": "100.00"}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaymentInitializeViewTests(APITestCase):
    url = "/api/payments/initialize/"

    def setUp(self):
        self.member = make_user(email="member@example.com", code_no=3000)
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=3001, is_staff=True
        )
        self.item = make_payment_item(name="Dues", amount="500.00")

    def test_requires_authentication(self):
        response = self.client.post(
            self.url, {"payment_item": str(self.item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_forbidden(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            self.url, {"payment_item": str(self.item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_payment_item_rejected(self):
        inactive_item = make_payment_item(name="Inactive", is_active=False)

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url, {"payment_item": str(inactive_item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @mock.patch("apps.payments.services.requests.post")
    def test_successful_initialize_creates_payment_and_transaction(self, mock_post):
        mock_post.return_value = mock_response(
            ok=True,
            json_data={
                "status": True,
                "data": {
                    "authorization_url": "https://checkout.paystack.com/abc",
                    "access_code": "abc",
                },
            },
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url, {"payment_item": str(self.item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(
            response.data["data"]["authorization_url"],
            "https://checkout.paystack.com/abc",
        )

        payment = Payment.objects.get(member=self.member, payment_item=self.item)
        self.assertEqual(payment.status, Payment.Status.PENDING)

        transaction = Transaction.objects.get(payment=payment)
        self.assertEqual(transaction.amount, Decimal("500.00"))

        sent_amount = mock_post.call_args.kwargs["json"]["amount"]
        self.assertEqual(sent_amount, 50000)

    @mock.patch("apps.payments.services.requests.post")
    def test_paystack_rejection_marks_payment_failed(self, mock_post):
        mock_post.return_value = mock_response(
            ok=True, json_data={"status": False, "message": "Invalid key"}
        )

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url, {"payment_item": str(self.item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        payment = Payment.objects.get(member=self.member, payment_item=self.item)
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertFalse(Transaction.objects.filter(payment=payment).exists())

    @mock.patch("apps.payments.services.requests.post")
    def test_network_error_marks_payment_failed(self, mock_post):
        mock_post.side_effect = requests.ConnectionError("boom")

        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            self.url, {"payment_item": str(self.item.id)}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        payment = Payment.objects.get(member=self.member, payment_item=self.item)
        self.assertEqual(payment.status, Payment.Status.FAILED)


class VerifyPaymentServiceTests(APITestCase):
    def setUp(self):
        self.member = make_user(email="member@example.com", code_no=4000)
        self.item = make_payment_item(name="Dues", amount="500.00")
        self.payment = Payment.objects.create(member=self.member, payment_item=self.item)
        self.transaction = Transaction.objects.create(
            payment=self.payment, reference="NYSC-test-ref", amount=self.item.amount
        )

    def test_unknown_reference_raises(self):
        with self.assertRaises(PaystackError):
            verify_payment("does-not-exist")

    @mock.patch("apps.payments.services.requests.get")
    def test_successful_transaction_marks_payment_successful(self, mock_get):
        mock_get.return_value = mock_response(
            ok=True,
            json_data={
                "status": True,
                "data": {
                    "status": "success",
                    "gateway_response": "Approved",
                    "channel": "card",
                    "paid_at": "2026-01-01T12:00:00.000Z",
                },
            },
        )

        result = verify_payment(self.transaction.reference)

        self.assertEqual(result.status, Transaction.Status.SUCCESSFUL)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.SUCCESSFUL)
        self.assertIsNotNone(self.payment.paid_at)

    @mock.patch("apps.payments.services.requests.get")
    def test_abandoned_transaction_marks_payment_failed(self, mock_get):
        mock_get.return_value = mock_response(
            ok=True,
            json_data={
                "status": True,
                "data": {"status": "abandoned", "gateway_response": "Abandoned", "channel": ""},
            },
        )

        result = verify_payment(self.transaction.reference)

        self.assertEqual(result.status, Transaction.Status.FAILED)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.FAILED)

    @mock.patch("apps.payments.services.requests.get")
    def test_already_successful_transaction_short_circuits(self, mock_get):
        self.transaction.status = Transaction.Status.SUCCESSFUL
        self.transaction.save(update_fields=["status"])

        result = verify_payment(self.transaction.reference)

        mock_get.assert_not_called()
        self.assertEqual(result.status, Transaction.Status.SUCCESSFUL)

    @mock.patch("apps.payments.services.requests.get")
    def test_paystack_verify_error_raises(self, mock_get):
        mock_get.return_value = mock_response(
            ok=True, json_data={"status": False, "message": "Reference not found"}
        )

        with self.assertRaises(PaystackError):
            verify_payment(self.transaction.reference)


class VerifyWebhookSignatureTests(APITestCase):
    def test_valid_signature_returns_true(self):
        payload = b'{"event": "charge.success"}'
        signature = hmac.new(
            settings.PAYSTACK_SECRET_KEY.encode(), payload, hashlib.sha512
        ).hexdigest()

        self.assertTrue(verify_webhook_signature(payload, signature))

    def test_invalid_signature_returns_false(self):
        payload = b'{"event": "charge.success"}'

        self.assertFalse(verify_webhook_signature(payload, "wrong-signature"))

    def test_missing_signature_returns_false(self):
        payload = b'{"event": "charge.success"}'

        self.assertFalse(verify_webhook_signature(payload, ""))


class PaystackWebhookViewTests(APITestCase):
    url = "/api/payments/webhook/"

    def setUp(self):
        self.member = make_user(email="member@example.com", code_no=4200)
        self.item = make_payment_item(name="Dues", amount="500.00")
        self.payment = Payment.objects.create(member=self.member, payment_item=self.item)
        self.transaction = Transaction.objects.create(
            payment=self.payment, reference="NYSC-webhook-ref", amount=self.item.amount
        )

    def _signed_post(self, payload, signature=None):
        body = json.dumps(payload).encode()
        if signature is None:
            signature = hmac.new(
                settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512
            ).hexdigest()
        return self.client.post(
            self.url,
            data=body,
            content_type="application/json",
            HTTP_X_PAYSTACK_SIGNATURE=signature,
        )

    def test_missing_signature_rejected(self):
        body = json.dumps(
            {"event": "charge.success", "data": {"reference": self.transaction.reference}}
        ).encode()

        response = self.client.post(self.url, data=body, content_type="application/json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_signature_rejected(self):
        response = self._signed_post(
            {"event": "charge.success", "data": {"reference": self.transaction.reference}},
            signature="not-a-real-signature",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_signature_accepted(self):
        response = self._signed_post(
            {"event": "charge.success", "data": {"reference": self.transaction.reference}}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_authentication_required(self):
        response = self._signed_post({"event": "some.other.event", "data": {}})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PaymentHistoryViewTests(APITestCase):
    url = "/api/payments/history/"

    def setUp(self):
        self.member_a = make_user(email="a@example.com", code_no=5000)
        self.member_b = make_user(email="b@example.com", code_no=5001)
        self.item = make_payment_item(name="Dues", amount="500.00")

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_only_own_payments(self):
        payment_a = Payment.objects.create(
            member=self.member_a, payment_item=self.item, status=Payment.Status.SUCCESSFUL
        )
        Transaction.objects.create(
            payment=payment_a,
            reference="NYSC-a-1",
            amount=self.item.amount,
            status=Transaction.Status.SUCCESSFUL,
        )
        Payment.objects.create(member=self.member_b, payment_item=self.item)

        self.client.force_authenticate(user=self.member_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], str(payment_a.id))
        self.assertEqual(len(results[0]["transactions"]), 1)


class InitializePaymentServiceTests(APITestCase):
    def setUp(self):
        self.member = make_user(email="member@example.com", code_no=4300)
        self.item = make_payment_item(name="Dues", amount="500.00")

    @mock.patch("apps.payments.services.requests.post")
    def test_uses_member_email_and_reference_metadata(self, mock_post):
        mock_post.return_value = mock_response(
            ok=True,
            json_data={
                "status": True,
                "data": {
                    "authorization_url": "https://checkout.paystack.com/xyz",
                    "access_code": "xyz",
                },
            },
        )

        result = initialize_payment(member=self.member, payment_item=self.item)

        sent_json = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_json["email"], self.member.email)
        self.assertEqual(sent_json["reference"], result["reference"])
        self.assertTrue(result["reference"].startswith("NYSC-"))