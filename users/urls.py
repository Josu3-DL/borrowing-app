from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import LoginForm
from . import views

app_name = "users"

urlpatterns = [
    path("", views.home, name="home"),
    path("registro/", views.register, name="register"),
    path(
        "iniciar-sesion/",
        LoginView.as_view(
            template_name="users/login.html",
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("cerrar-sesion/", LogoutView.as_view(), name="logout"),
    path("perfil/", views.profile, name="profile"),
]
