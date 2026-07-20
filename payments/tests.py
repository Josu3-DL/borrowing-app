from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from loans.models import Loan

from .models import Payment


User = get_user_model()


class PaymentViewTests(TestCase):
    password = "SecurePassword2026!"

    def setUp(self):
        self.user = User.objects.create_user(
            username="payment-owner",
            email="payment-owner@example.com",
            password=self.password,
        )
        self.other_user = User.objects.create_user(
            username="other-payment-owner",
            email="other-payment-owner@example.com",
            password=self.password,
        )
        today = timezone.localdate()
        self.loan = Loan.objects.create(
            owner=self.user,
            borrower_name="Ana García",
            borrower_phone="+505 88888888",
            amount=Decimal("500.00"),
            currency=Loan.Currency.USD,
            loan_date=today - timedelta(days=30),
            due_date=today + timedelta(days=30),
        )
        self.other_loan = Loan.objects.create(
            owner=self.other_user,
            borrower_name="Hidden Person",
            amount=Decimal("900.00"),
            currency=Loan.Currency.USD,
            loan_date=today - timedelta(days=30),
            due_date=today + timedelta(days=30),
        )

    def test_payment_routes_require_authentication(self):
        for url in (reverse("payments:list"), reverse("payments:create")):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('users:login')}?next={url}",
                )

    def test_payment_list_renders_desktop_and_mobile_with_user_metrics(self):
        today = timezone.localdate()
        Payment.objects.create(
            loan=self.loan,
            amount=Decimal("125.00"),
            currency=Payment.Currency.USD,
            payment_date=today,
        )
        Payment.objects.create(
            loan=self.other_loan,
            amount=Decimal("700.00"),
            currency=Payment.Currency.USD,
            payment_date=today,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("payments:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_collected_month"], "$125.00")
        self.assertContains(response, 'class="payments-desktop"')
        self.assertContains(response, 'class="payments-mobile"')
        self.assertContains(
            response,
            ".payments-primary-button { align-items: center; background: var(--action-primary);",
        )
        self.assertContains(response, "Ana García")
        self.assertNotContains(response, "Hidden Person")

    def test_payment_list_filters_by_borrower(self):
        today = timezone.localdate()
        second_loan = Loan.objects.create(
            owner=self.user,
            borrower_name="Carlos Ruiz",
            amount=Decimal("300.00"),
            currency=Loan.Currency.USD,
            loan_date=today - timedelta(days=20),
            due_date=today + timedelta(days=20),
        )
        Payment.objects.create(
            loan=self.loan,
            amount=Decimal("50.00"),
            currency=Payment.Currency.USD,
            payment_date=today,
        )
        Payment.objects.create(
            loan=second_loan,
            amount=Decimal("60.00"),
            currency=Payment.Currency.USD,
            payment_date=today,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("payments:list"),
            {"borrower_name": "ana"},
        )

        self.assertEqual(
            [
                row["payment"].loan.borrower_name
                for row in response.context["payment_rows"]
            ],
            ["Ana García"],
        )

    def test_payment_list_renders_mobile_filters_with_selected_values(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("payments:list"),
            {
                "borrower_name": self.loan.borrower_name,
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="mobile-payment-filters"')
        self.assertContains(response, 'id="mobile-payment-person-filter"')
        self.assertContains(
            response,
            f'<option value="{self.loan.borrower_name}" selected>',
        )
        self.assertContains(
            response,
            'id="mobile-payment-date-from" name="date_from" type="date" '
            'value="2026-07-01"',
        )
        self.assertContains(
            response,
            'id="mobile-payment-date-to" name="date_to" type="date" '
            'value="2026-07-31"',
        )
        self.assertContains(response, "Aplicar filtros")
        self.assertContains(response, "Limpiar")

    def test_payment_create_renders_responsive_modal(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("payments:create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="payment-modal-backdrop"')
        self.assertContains(response, "Registrar pago")
        self.assertContains(response, "Referencia / Nota")

    def test_user_can_register_payment_for_own_loan(self):
        self.client.force_login(self.user)
        today = timezone.localdate()

        response = self.client.post(
            reverse("payments:create"),
            {
                "loan": self.loan.pk,
                "amount": "100.00",
                "currency": Payment.Currency.USD,
                "payment_date": today.isoformat(),
                "notes": "Transferencia bancaria",
            },
        )

        self.assertRedirects(response, reverse("payments:list"))
        payment = Payment.objects.get()
        self.assertEqual(payment.loan, self.loan)
        self.assertEqual(payment.amount, Decimal("100.00"))

    def test_user_cannot_register_payment_for_another_users_loan(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("payments:create"),
            {
                "loan": self.other_loan.pk,
                "amount": "100.00",
                "currency": Payment.Currency.USD,
                "payment_date": timezone.localdate().isoformat(),
                "notes": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Payment.objects.exists())
        self.assertIn("loan", response.context["form"].errors)
