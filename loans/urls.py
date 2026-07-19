from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("", views.loan_list, name="list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("new/", views.loan_create, name="create"),
    path("<int:pk>/edit/", views.loan_update, name="update"),
    path("<int:pk>/delete/", views.loan_delete, name="delete"),
]
