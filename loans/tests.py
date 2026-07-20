from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from payments.models import Payment

from .forms import LoanFilterForm, LoanForm
from .models import Loan


User = get_user_model()


class LoanTestMixin:
    password = "SecurePassword2026!"

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
            "borrower_name": "Mary Smith",
            "borrower_phone_0": "+505",
            "borrower_phone_1": "88888888",
            "borrower_email": "maria@example.com",
            "amount": "250.00",
            "currency": Loan.Currency.NIO,
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
            borrower_phone=f"{data['borrower_phone_0']} {data['borrower_phone_1']}",
            borrower_email=data["borrower_email"],
            amount=Decimal(data["amount"]),
            currency=data.get("currency", Loan.Currency.NIO),
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

    def test_form_rejects_non_numeric_phone(self):
        form = LoanForm(data=self.loan_data(borrower_phone_1="8888ABCD"))

        self.assertFalse(form.is_valid())
        self.assertIn("borrower_phone", form.errors)

    def test_filter_form_rejects_reversed_date_range(self):
        form = LoanFilterForm(
            data={"date_from": "2026-08-01", "date_to": "2026-07-01"}
        )

        self.assertFalse(form.is_valid())
        self.assertIn("La fecha inicial", form.non_field_errors()[0])


class LoanViewTests(LoanTestMixin, TestCase):
    def test_all_loan_routes_require_authentication(self):
        loan = self.create_loan()
        protected_urls = [
            reverse("loans:list"),
            reverse("loans:dashboard"),
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

    def test_dashboard_uses_only_current_users_financial_data(self):
        own_loan = self.create_loan(
            borrower_name="Visible dashboard borrower",
            amount="100.00",
            currency=Loan.Currency.USD,
            loan_date="2026-07-01",
            due_date="2026-08-01",
        )
        Payment.objects.create(
            loan=own_loan,
            amount=Decimal("25.00"),
            currency=Loan.Currency.USD,
            payment_date=date(2026, 7, 15),
        )
        other_loan = self.create_loan(
            owner=self.other_user,
            borrower_name="Hidden dashboard borrower",
            amount="900.00",
            currency=Loan.Currency.USD,
        )
        Payment.objects.create(
            loan=other_loan,
            amount=Decimal("500.00"),
            currency=Loan.Currency.USD,
            payment_date=date(2026, 7, 15),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_lent"], "C$3,700.00")
        self.assertEqual(response.context["total_recovered"], "C$925.00")
        self.assertEqual(response.context["total_pending"], "C$2,775.00")
        self.assertEqual(response.context["active_count"], 1)
        self.assertContains(response, "Visible dashboard borrower")
        self.assertNotContains(response, "Hidden dashboard borrower")

    def test_dashboard_renders_responsive_sections_and_real_empty_states(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:dashboard"))

        self.assertContains(response, "Panel de Control")
        self.assertContains(response, 'class="dashboard-desktop"')
        self.assertContains(response, 'class="dashboard-mobile"')
        self.assertContains(response, "Aún no hay préstamos registrados")
        self.assertContains(response, "No hay pagos pendientes")

    def test_dashboard_metrics_use_three_columns_on_small_desktop_screens(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:dashboard"))

        self.assertContains(
            response,
            "@media (min-width: 901px) and (max-width: 1050px)",
        )
        self.assertContains(
            response,
            ".dashboard-metrics { grid-template-columns: repeat(3, minmax(0, 1fr)); }",
        )

    def test_dashboard_filters_charts_by_supported_month_period(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:dashboard"),
            {"chart_months": "3"},
        )

        self.assertEqual(response.context["chart_month_count"], 3)
        self.assertEqual(len(response.context["month_series"]), 3)
        self.assertContains(response, '<option value="3" selected>')
        self.assertContains(
            response,
            'aria-label="Préstamos emitidos durante los últimos 3 meses"',
        )
        self.assertContains(
            response,
            'html[data-theme="dark"] .chart-period-filter select {',
        )
        self.assertContains(
            response,
            'html[data-theme="dark"] .chart-period-filter button {',
        )
        self.assertContains(
            response,
            'html[data-theme="dark"] .chart-period-filter button:hover {',
        )

    def test_dashboard_defaults_to_six_months_for_invalid_chart_period(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:dashboard"),
            {"chart_months": "24"},
        )

        self.assertEqual(response.context["chart_month_count"], 6)
        self.assertEqual(len(response.context["month_series"]), 6)

    def test_dashboard_only_accepts_get(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:dashboard"))

        self.assertEqual(response.status_code, 405)

    def test_user_can_create_loan_for_external_borrower(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("loans:create"), self.loan_data())

        self.assertRedirects(response, reverse("loans:list"))
        loan = Loan.objects.get()
        self.assertEqual(loan.owner, self.user)
        self.assertEqual(loan.borrower_name, "Mary Smith")
        self.assertNotEqual(loan.borrower_email, self.user.email)

    def test_success_message_is_rendered_as_accessible_toast(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("loans:create"),
            self.loan_data(),
            follow=True,
        )

        self.assertContains(response, 'class="toast-region"')
        self.assertContains(response, 'class="toast success"')
        self.assertContains(response, "Prestamo creado correctamente.")
        self.assertContains(response, 'data-toast-close')
        self.assertContains(response, 'aria-label="Cerrar notificación"')
        self.assertContains(response, 'role="status"')
        self.assertNotContains(response, 'class="flash-messages"')
        self.assertContains(response, 'html[data-theme="dark"] .toast {')
        self.assertContains(response, 'html[data-theme="dark"] .toast.success {')
        self.assertContains(response, 'html[data-theme="dark"] .toast.warning {')
        self.assertContains(response, 'html[data-theme="dark"] .toast.error {')
        self.assertContains(response, 'html[data-theme="dark"] .toast-close:hover {')

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

    def test_list_keeps_table_and_pagination_in_same_scroll_container(self):
        self.create_loan()
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:list"))

        self.assertContains(response, 'class="loan-table-scroll-content"')
        self.assertContains(
            response,
            "body.loans-page .loan-table-scroll-content {",
        )
        self.assertContains(
            response,
            'class="loan-actions-column" style="width: 11%"',
        )

    def test_list_includes_mid_size_overflow_rules(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:list"))

        self.assertContains(
            response,
            "@media (min-width: 901px) and (max-width: 970px)",
        )
        self.assertContains(
            response,
            "body.loans-page .loan-table {\n            min-width: 0;",
        )
        self.assertContains(
            response,
            "body.loans-page .loan-table th:nth-child(4)",
        )

    def test_list_filters_loans_by_status(self):
        pending = self.create_loan(
            borrower_name="Pending borrower",
            status=Loan.Status.PENDING,
        )
        paid = self.create_loan(
            borrower_name="Paid borrower",
            status=Loan.Status.PAID,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:list"),
            {"status": Loan.Status.PAID},
        )

        self.assertContains(response, paid.borrower_name)
        self.assertNotContains(response, pending.borrower_name)

    def test_list_filters_loans_by_borrower_name_case_insensitively(self):
        matching = self.create_loan(borrower_name="Alice Smith")
        non_matching = self.create_loan(borrower_name="Bob Jones")
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:list"),
            {"borrower_name": "alice"},
        )

        self.assertContains(response, matching.borrower_name)
        self.assertNotContains(response, non_matching.borrower_name)

    def test_list_filters_loans_by_inclusive_loan_date_range(self):
        before_range = self.create_loan(
            borrower_name="Before range",
            loan_date="2026-06-30",
        )
        range_start = self.create_loan(
            borrower_name="Range start",
            loan_date="2026-07-01",
        )
        range_end = self.create_loan(
            borrower_name="Range end",
            loan_date="2026-07-31",
        )
        after_range = self.create_loan(
            borrower_name="After range",
            loan_date="2026-08-01",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:list"),
            {"date_from": "2026-07-01", "date_to": "2026-07-31"},
        )

        self.assertContains(response, range_start.borrower_name)
        self.assertContains(response, range_end.borrower_name)
        self.assertNotContains(response, before_range.borrower_name)
        self.assertNotContains(response, after_range.borrower_name)

    def test_list_combines_all_filters(self):
        matching = self.create_loan(
            borrower_name="Alice Matching",
            loan_date="2026-07-15",
            status=Loan.Status.PAID,
        )
        self.create_loan(
            borrower_name="Alice Pending",
            loan_date="2026-07-15",
            status=Loan.Status.PENDING,
        )
        self.create_loan(
            borrower_name="Alice Outside Range",
            loan_date="2026-06-15",
            status=Loan.Status.PAID,
        )
        self.create_loan(
            borrower_name="Bob Matching",
            loan_date="2026-07-15",
            status=Loan.Status.PAID,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("loans:list"),
            {
                "status": Loan.Status.PAID,
                "borrower_name": "alice",
                "date_from": "2026-07-01",
                "date_to": "2026-07-31",
            },
        )

        self.assertContains(response, matching.borrower_name)
        self.assertNotContains(response, "Alice Pending")
        self.assertNotContains(response, "Alice Outside Range")
        self.assertNotContains(response, "Bob Matching")

    def test_user_can_update_own_loan(self):
        loan = self.create_loan()
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("loans:update", args=[loan.pk]),
            self.loan_data(
                borrower_name="Updated name",
                status=Loan.Status.PAID,
            ),
        )

        self.assertRedirects(response, reverse("loans:list"))
        loan.refresh_from_db()
        self.assertEqual(loan.borrower_name, "Updated name")
        self.assertEqual(loan.status, Loan.Status.PAID)

    def test_user_cannot_update_another_users_loan(self):
        loan = self.create_loan(owner=self.other_user)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("loans:update", args=[loan.pk]),
            self.loan_data(borrower_name="Attempted change"),
        )

        self.assertEqual(response.status_code, 404)
        loan.refresh_from_db()
        self.assertEqual(loan.borrower_name, "Mary Smith")

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

    def test_navigation_is_in_spanish_and_excludes_reports(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("loans:list"))

        self.assertContains(response, "Gestión de préstamos")
        self.assertContains(response, "Panel")
        self.assertNotContains(response, "Dashboard")
        self.assertNotContains(response, "Reportes")
