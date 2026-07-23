from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from borrowing_app.reporting import dashboard_context

from . import selectors, services
from .forms import LoanFilterForm, LoanForm
from .models import Loan


def _loan_page_context(request, apply_filters=False):
    filter_form = LoanFilterForm(
        request.GET if apply_filters else None,
        auto_id="filter_%s",
    )

    filters = None
    if apply_filters and filter_form.is_valid():
        filters = filter_form.cleaned_data

    loans = selectors.filtered_loans(request.user, filters=filters)
    paginator, page_obj = selectors.paginate_loans(
        loans, page_number=request.GET.get("page")
    )

    query_params = request.GET.copy()
    query_params.pop("page", None)
    return {
        "loans": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "query_string": query_params.urlencode(),
        "filter_form": filter_form,
    }


@login_required
@require_http_methods(["GET"])
def dashboard(request):
    context = dashboard_context(
        request.user, chart_months_param=request.GET.get("chart_months")
    )
    return render(request, "loans/dashboard.html", context)


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
        services.create_loan(owner=request.user, cleaned_data=form.cleaned_data)
        messages.success(request, "Prestamo creado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Nuevo préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_update(request, pk):
    loan = get_object_or_404(Loan.objects.owned_by(request.user), pk=pk)
    form = LoanForm(request.POST or None, instance=loan)
    if request.method == "POST" and form.is_valid():
        services.update_loan(loan=loan, cleaned_data=form.cleaned_data)
        messages.success(request, "Prestamo actualizado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context.update({"form": form, "title": "Editar préstamo"})
    return render(request, "loans/loan_form.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def loan_delete(request, pk):
    loan = get_object_or_404(Loan.objects.owned_by(request.user), pk=pk)
    if request.method == "POST":
        loan.delete()
        messages.success(request, "Prestamo eliminado correctamente.")
        return redirect("loans:list")

    context = _loan_page_context(request)
    context["loan"] = loan
    return render(request, "loans/loan_confirm_delete.html", context)
