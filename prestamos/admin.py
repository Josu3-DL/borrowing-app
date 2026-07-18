from django.contrib import admin

from .models import Cliente, Prestamo


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'email')
    search_fields = ('nombre',)


@admin.register(Prestamo)
class PrestamoAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'monto', 'fecha_prestamo', 'fecha_vencimiento', 'estado')
    list_filter = ('estado',)
    search_fields = ('cliente__nombre',)
