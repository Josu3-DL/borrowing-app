from django.urls import path

from . import views

app_name = 'prestamos'

urlpatterns = [
    path('', views.lista_prestamos, name='lista'),
    path('nuevo/', views.crear_prestamo, name='crear'),
    path('<int:pk>/editar/', views.editar_prestamo, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar_prestamo, name='eliminar'),
]
