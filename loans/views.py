from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoanFilterForm, LoanForm
from .models import Loan


def _loan_page_context(request, apply_filters=False):
    loans = Loan.objects.filter(owner=request.user)
    filter_form = LoanFilterForm(
        request.GET if apply_filters else None,
        auto_id="filter_%s",
    )

    if apply_filters and filter_form.is_valid():
        status = filter_form.cleaned_data["status"]
        borrower_name = filter_form.cleaned_data["borrower_name"]
        date_from = filter_form.cleaned_data["date_from"]
        date_to = filter_form.cleaned_data["date_to"]

        if status:
            loans = loans.filter(status=status)
        if borrower_name:
            loans = loans.filter(borrower_name__icontains=borrower_name)
        if date_from:
            loans = loans.filter(loan_date__gte=date_from)
        if date_to:
            loans = loans.filter(loan_date__lte=date_to)

    return {"loans": loans, "filter_form": filter_form}


@login_required
@require_http_methods(["GET"])
def loan_list(request):
    context = _loan_page_context(request, apply_filters=True)
    return render(request, "loans/loan_list.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_create(request):
    form = LoanForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.owner = request.user
        loan.save()
        messages.success(request, "Préstamo creado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Nuevo préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_update(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Préstamo actualizado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Editar préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    if request.method == "POST":
        loan.delete()
        messages.success(request, "Préstamo eliminado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context["loan"] = loan
    return render(request, "loans/loan_confirm_delete.html", context)
