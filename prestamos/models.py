from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Prestamo(models.Model):
    ESTADO_PENDIENTE = 'PENDIENTE'
    ESTADO_PAGADO = 'PAGADO'
    ESTADO_CHOICES = [
        (ESTADO_PENDIENTE, 'Pendiente'),
        (ESTADO_PAGADO, 'Pagado'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='prestamos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_prestamo = models.DateField()
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default=ESTADO_PENDIENTE)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prestamos_creados')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha_prestamo']

    def __str__(self):
        return f'{self.cliente} - {self.monto} ({self.get_estado_display()})'

    def get_absolute_url(self):
        return reverse('prestamos:detalle', kwargs={'pk': self.pk})
