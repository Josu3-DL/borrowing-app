from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import LoanForm
from .models import Loan


User = get_user_model()


class LoanTestMixin:
    password = "UnaClaveSegura2026!"

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password=self.password,
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password=self.password,
        )

    def loan_data(self, **overrides):
        data = {
            "borrower_name": "María López",
            "borrower_phone": "8888-8888",
            "borrower_email": "maria@example.com",
            "amount": "250.00",
            "loan_date": "2026-07-01",
            "due_date": "2026-08-01",
            "status": Loan.Status.PENDING,
        }
        data.update(overrides)
        return data

    def create_loan(self, owner=None, **overrides):
        data = self.loan_data(**overrides)
        return Loan.objects.create(
            owner=owner or self.user,
            borrower_name=data["borrower_name"],
            borrower_phone=data["borrower_phone"],
            borrower_email=data["borrower_email"],
            amount=Decimal(data["amount"]),
            loan_date=date.fromisoformat(data["loan_date"]),
            due_date=date.fromisoformat(data["due_date"]),
            status=data["status"],
        )


class LoanModelAndFormTests(LoanTestMixin, TestCase):
    def test_new_loan_defaults_to_pending(self):
        loan = Loan(
            owner=self.user,
            borrower_name="Carlos Pérez",
            amount=Decimal("100.00"),
            loan_date=date(2026, 7, 1),
            due_date=date(2026, 8, 1),
        )

        self.assertEqual(loan.status, Loan.Status.PENDING)

    def test_form_rejects_non_positive_amount(self):
        form = LoanForm(data=self.loan_data(amount="0"))

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_form_rejects_due_date_before_loan_date(self):
        form = LoanForm(
            data=self.loan_data(
                loan_date="2026-08-01",
                due_date="2026-07-01",
            )
        )

        self.assertFalse(form.is_valid())
        self.assertIn("due_date", form.errors)


class LoanViewTests(LoanTestMixin, TestCase):
    def test_all_loan_routes_require_authentication(self):
        loan = self.create_loan()
        protected_urls = [
            reverse("loans:list"),
            reverse("loans:create"),
            reverse("loans:update", args=[loan.pk]),
            reverse("loans:delete", args=[loan.pk]),
        ]

        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('users:login')}?next={url}",
                )

    def test_user_can_create_loan_for_external_borrower(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:create"), self.loan_data())

        self.assertRedirects(response, reverse("loans:list"))
        loan = Loan.objects.get()
        self.assertEqual(loan.owner, self.user)
        self.assertEqual(loan.borrower_name, "María López")
        self.assertNotEqual(loan.borrower_email, self.user.email)

    def test_list_only_shows_current_users_loans(self):
        own_loan = self.create_loan(borrower_name="Visible")
        other_loan = self.create_loan(
            owner=self.other_user,
            borrower_name="Hidden",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:list"))

        self.assertContains(response, own_loan.borrower_name)
        self.assertNotContains(response, other_loan.borrower_name)

    def test_list_filters_loans_by_status(self):
        pending = self.create_loan(
            borrower_name="Prestatario pendiente",
            status=Loan.Status.PENDING,
        )
        paid = self.create_loan(
            borrower_name="Prestatario pagado",
            status=Loan.Status.PAID,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:list"),
            {"status": Loan.Status.PAID},
        )

        self.assertContains(response, paid.borrower_name)
        self.assertNotContains(response, pending.borrower_name)

    def test_user_can_update_own_loan(self):
        loan = self.create_loan()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("loans:update", args=[loan.pk]),
            self.loan_data(
                borrower_name="Nombre actualizado",
                status=Loan.Status.PAID,
            ),
        )

        self.assertRedirects(response, reverse("loans:list"))
        loan.refresh_from_db()
        self.assertEqual(loan.borrower_name, "Nombre actualizado")
        self.assertEqual(loan.status, Loan.Status.PAID)

    def test_user_cannot_update_another_users_loan(self):
        loan = self.create_loan(owner=self.other_user)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("loans:update", args=[loan.pk]),
            self.loan_data(borrower_name="Intento de cambio"),
        )

        self.assertEqual(response.status_code, 404)
        loan.refresh_from_db()
        self.assertEqual(loan.borrower_name, "María López")

    def test_user_can_delete_own_loan(self):
        loan = self.create_loan()
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:delete", args=[loan.pk]))

        self.assertRedirects(response, reverse("loans:list"))
        self.assertFalse(Loan.objects.filter(pk=loan.pk).exists())

    def test_user_cannot_delete_another_users_loan(self):
        loan = self.create_loan(owner=self.other_user)
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:delete", args=[loan.pk]))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Loan.objects.filter(pk=loan.pk).exists())

    def test_loan_list_only_accepts_get(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:list"))

        self.assertEqual(response.status_code, 405)
