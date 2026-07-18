from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PrestamoForm
from .models import Prestamo


def lista_prestamos(request):
    prestamos = Prestamo.objects.select_related('cliente')

    estado = request.GET.get('estado', '')
    if estado in dict(Prestamo.ESTADO_CHOICES):
        prestamos = prestamos.filter(estado=estado)

    contexto = {
        'prestamos': prestamos,
        'estado_actual': estado,
        'estado_choices': Prestamo.ESTADO_CHOICES,
    }
    return render(request, 'prestamos/lista.html', contexto)


def crear_prestamo(request):
    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo creado correctamente.')
            return redirect('prestamos:lista')
    else:
        form = PrestamoForm()
    return render(request, 'prestamos/form.html', {'form': form, 'titulo': 'Nuevo préstamo'})


def editar_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == 'POST':
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            form.save()
            messages.success(request, 'Préstamo actualizado correctamente.')
            return redirect('prestamos:lista')
    else:
        form = PrestamoForm(instance=prestamo)
    return render(request, 'prestamos/form.html', {'form': form, 'titulo': 'Editar préstamo'})


def eliminar_prestamo(request, pk):
    prestamo = get_object_or_404(Prestamo, pk=pk)
    if request.method == 'POST':
        prestamo.delete()
        messages.success(request, 'Préstamo eliminado correctamente.')
        return redirect('prestamos:lista')
    return render(request, 'prestamos/confirmar_eliminar.html', {'prestamo': prestamo})
