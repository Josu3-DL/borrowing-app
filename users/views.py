from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import ProfileForm, RegistrationForm


def home(request):
    destination = "loans:dashboard" if request.user.is_authenticated else "users:login"
    return redirect(destination)


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("loans:dashboard")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tu cuenta fue creada correctamente.")
        return redirect("loans:dashboard")

    return render(request, "users/register.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tu perfil fue actualizado.")
        return redirect("users:profile")

    return render(request, "users/profile.html", {"form": form})
