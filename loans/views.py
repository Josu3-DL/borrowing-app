from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .forms import LoanForm
from .models import Loan


@login_required
@require_http_methods(["GET"])
def loan_list(request):
    loans = Loan.objects.filter(owner=request.user)
    selected_status = request.GET.get("status", "")

    if selected_status in Loan.Status.values:
        loans = loans.filter(status=selected_status)
    else:
        selected_status = ""

    context = {
        "loans": loans,
        "selected_status": selected_status,
        "status_choices": Loan.Status.choices,
    }
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

    return render(
        request,
        "loans/loan_form.html",
        {"form": form, "title": "Nuevo préstamo"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def loan_update(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Préstamo actualizado correctamente.")
        return redirect("loans:list")

    return render(
        request,
        "loans/loan_form.html",
        {"form": form, "title": "Editar préstamo"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def loan_delete(request, pk):
    loan = get_object_or_404(Loan, pk=pk, owner=request.user)
    if request.method == "POST":
        loan.delete()
        messages.success(request, "Préstamo eliminado correctamente.")
        return redirect("loans:list")

    return render(request, "loans/loan_confirm_delete.html", {"loan": loan})
