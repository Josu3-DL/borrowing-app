from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoanFilterForm, LoanForm
from .models import Loan


@login_required
@require_http_methods(["GET"])
def dashboard(request):
    loans = Loan.objects.filter(owner=request.user).prefetch_related("payments")

    usd = [l for l in loans if l.currency == Loan.Currency.USD]
    nio = [l for l in loans if l.currency == Loan.Currency.NIO]

    def stats(loan_list):
        total_lent = sum(l.amount for l in loan_list) or Decimal("0")
        total_recovered = sum(l.total_paid for l in loan_list) or Decimal("0")
        total_pending = sum(l.remaining_balance for l in loan_list) or Decimal("0")
        active = sum(1 for l in loan_list if l.status == Loan.Status.PENDING)
        return {
            "total_lent": total_lent,
            "total_recovered": total_recovered,
            "total_pending": total_pending,
            "active": active,
        }

    context = {
        "usd": stats(usd),
        "nio": stats(nio),
        "total_active": sum(1 for l in loans if l.status == Loan.Status.PENDING),
    }
    return render(request, "loans/dashboard.html", context)


@login_required
@require_http_methods(["GET"])
def loan_list(request):
    loans = Loan.objects.filter(owner=request.user)
    filter_form = LoanFilterForm(request.GET)

    if filter_form.is_valid():
        status = filter_form.cleaned_data["status"]
        currency = filter_form.cleaned_data["currency"]
        borrower_name = filter_form.cleaned_data["borrower_name"]
        date_from = filter_form.cleaned_data["date_from"]
        date_to = filter_form.cleaned_data["date_to"]

        if status:
            loans = loans.filter(status=status)
        if currency:
            loans = loans.filter(currency=currency)
        if borrower_name:
            loans = loans.filter(borrower_name__icontains=borrower_name)
        if date_from:
            loans = loans.filter(loan_date__gte=date_from)
        if date_to:
            loans = loans.filter(loan_date__lte=date_to)

    context = {"loans": loans, "filter_form": filter_form}
    return render(request, "loans/loan_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_create(request):
    form = LoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.owner = request.user
        loan.save()
        messages.success(request, "Prestamo creado correctamente.")
        return redirect("loans:list")
    return render(request, "loans/loan_form.html", {"form": form, "title": "Nuevo prestamo"})


@login_required
@require_http_methods(["GET", "POST"])
def loan_update(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Prestamo actualizado correctamente.")
        return redirect("loans:list")
    return render(request, "loans/loan_form.html", {"form": form, "title": "Editar prestamo"})


@login_required
@require_http_methods(["GET", "POST"])
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    if request.method == "POST":
        loan.delete()
        messages.success(request, "Prestamo eliminado correctamente.")
        return redirect("loans:list")
    return render(request, "loans/loan_confirm_delete.html", {"loan": loan})
