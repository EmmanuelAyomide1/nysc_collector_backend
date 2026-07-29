from datetime import datetime, timezone

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.payments.models import Payment, PaymentItem

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


class DashboardStatisticsViewTests(APITestCase):
    url = "/api/reports/dashboard/"

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=2000
        )
        self.member_a = make_user(
            email="a@example.com", code_no=2001, is_active=True
        )
        self.member_b = make_user(
            email="b@example.com", code_no=2002, is_active=False
        )
        self.active_item = make_payment_item(name="Active Item", amount="500.00")
        self.inactive_item = make_payment_item(
            name="Inactive Item", amount="300.00", is_active=False
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_access(self):
        self.client.force_authenticate(user=self.member_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_receives_statistics(self):
        Payment.objects.create(
            member=self.member_a,
            payment_item=self.active_item,
            status=Payment.Status.SUCCESSFUL,
        )
        Payment.objects.create(
            member=self.member_a,
            payment_item=self.inactive_item,
            status=Payment.Status.SUCCESSFUL,
        )
        Payment.objects.create(
            member=self.member_b,
            payment_item=self.active_item,
            status=Payment.Status.PENDING,
        )
        Payment.objects.create(
            member=self.member_b,
            payment_item=self.active_item,
            status=Payment.Status.FAILED,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data["data"]
        self.assertEqual(data["total_members"], 2)
        self.assertEqual(data["active_members"], 1)
        self.assertEqual(data["inactive_members"], 1)
        self.assertEqual(data["total_payment_items"], 2)
        self.assertEqual(data["active_payment_items"], 1)
        self.assertEqual(str(data["total_collected"]), "800.00")
        self.assertEqual(data["successful_payments_count"], 2)
        self.assertEqual(data["pending_payments_count"], 1)
        self.assertEqual(data["failed_payments_count"], 1)


class CollectionReportViewTests(APITestCase):
    url = "/api/reports/collections/"

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=3000
        )
        self.member_a = make_user(
            email="a@example.com", code_no=3001, is_active=True
        )
        self.member_b = make_user(
            email="b@example.com", code_no=3002, is_active=True
        )
        self.member_c = make_user(
            email="c@example.com", code_no=3003, is_active=False
        )
        self.paid_item = make_payment_item(name="Paid Item", amount="500.00")
        self.unpaid_item = make_payment_item(
            name="Unpaid Item", amount="300.00", is_active=False
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_access(self):
        self.client.force_authenticate(user=self.member_a)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_receives_per_item_breakdown(self):
        Payment.objects.create(
            member=self.member_a,
            payment_item=self.paid_item,
            status=Payment.Status.SUCCESSFUL,
        )
        Payment.objects.create(
            member=self.member_b,
            payment_item=self.paid_item,
            status=Payment.Status.PENDING,
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        by_name = {row["name"]: row for row in results}

        paid = by_name["Paid Item"]
        self.assertEqual(paid["total_members"], 2)
        self.assertEqual(paid["successful_payments_count"], 1)
        self.assertEqual(paid["pending_payments_count"], 1)
        self.assertEqual(paid["failed_payments_count"], 0)
        self.assertEqual(str(paid["collected_amount"]), "500.00")
        self.assertEqual(paid["outstanding_count"], 1)

        unpaid = by_name["Unpaid Item"]
        self.assertEqual(unpaid["total_members"], 2)
        self.assertEqual(unpaid["successful_payments_count"], 0)
        self.assertEqual(str(unpaid["collected_amount"]), "0.00")
        self.assertEqual(unpaid["outstanding_count"], 2)


class MonthlyStatisticsViewTests(APITestCase):
    url = "/api/reports/monthly/"

    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=4000
        )
        self.member = make_user(email="member@example.com", code_no=4001)
        self.item = make_payment_item(name="Dues", amount="500.00")

    def make_backdated_payment(self, status, created_at):
        payment = Payment.objects.create(
            member=self.member, payment_item=self.item, status=status
        )
        Payment.objects.filter(pk=payment.pk).update(created_at=created_at)
        return payment

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_access(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_receives_monthly_breakdown(self):
        self.make_backdated_payment(
            Payment.Status.SUCCESSFUL, datetime(2026, 6, 15, tzinfo=timezone.utc)
        )
        self.make_backdated_payment(
            Payment.Status.SUCCESSFUL, datetime(2026, 7, 5, tzinfo=timezone.utc)
        )
        self.make_backdated_payment(
            Payment.Status.PENDING, datetime(2026, 7, 20, tzinfo=timezone.utc)
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]
        by_month = {row["month"]: row for row in results}

        self.assertEqual(list(by_month.keys()), ["2026-06", "2026-07"])

        june = by_month["2026-06"]
        self.assertEqual(str(june["total_collected"]), "500.00")
        self.assertEqual(june["successful_payments_count"], 1)
        self.assertEqual(june["pending_payments_count"], 0)
        self.assertEqual(june["failed_payments_count"], 0)

        july = by_month["2026-07"]
        self.assertEqual(str(july["total_collected"]), "500.00")
        self.assertEqual(july["successful_payments_count"], 1)
        self.assertEqual(july["pending_payments_count"], 1)
        self.assertEqual(july["failed_payments_count"], 0)


class PaymentItemReportExportViewTests(APITestCase):
    def setUp(self):
        self.admin = make_user(
            email="admin@example.com", role=User.Role.ADMIN, code_no=5000
        )
        self.member = make_user(
            email="member@example.com",
            code_no=5001,
            batch="B1",
            first_name="Ada",
            last_name="Okafor",
        )
        self.item = make_payment_item(name="August CDS Dues", amount="500.00")
        Payment.objects.create(
            member=self.member, payment_item=self.item, status=Payment.Status.SUCCESSFUL
        )
        self.url = f"/api/reports/export/payment-items/{self.item.id}/"

    def test_requires_authentication(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_member_cannot_access(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_payment_item_404s(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(
            "/api/reports/export/payment-items/00000000-0000-0000-0000-000000000000/"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_format_rejected(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"file_format": "csv"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_exports_pdf_by_default(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn("august-cds-dues-payments.pdf", response["Content-Disposition"])
        content = response.content
        self.assertTrue(content.startswith(b"%PDF"))

    def test_admin_exports_docx(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(self.url, {"file_format": "docx"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        self.assertIn("august-cds-dues-payments.docx", response["Content-Disposition"])
        content = response.content
        self.assertTrue(content.startswith(b"PK"))