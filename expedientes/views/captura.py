"""
Vistas de captura de historia clínica.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from expedientes.decoradores import login_requerido
from expedientes.forms.captura import HistoriaClinicaForm
from expedientes.models import (
    HistoriaClinica, HistoriaClinicaTratamiento, CatCircunstanciaNivel2
)


@login_requerido
def nueva_historia(request):
    """Muestra y procesa el formulario de nueva historia clínica."""

    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST)

        if form.is_valid():
            # Guardamos sin commit=True para poder modificar antes de guardar en BD
            historia = form.save(commit=False)

            # Registrar automáticamente quién capturó
            historia.usuario_captura = request.user

            # Guardar en la base de datos (aquí se calcula edad y latencia en save())
            historia.save()

            # Guardar la relación ManyToMany de vías de ingreso
            # (se hace después del save() inicial)
            form.save_m2m()

            # Guardar tratamientos A y B
            _guardar_tratamientos(historia, form)

            messages.success(
                request,
                f'Historia clínica #{historia.consulta_numero} guardada correctamente.'
            )
            return redirect('detalle_historia', pk=historia.pk)

        else:
            messages.error(request, 'Por favor corrige los errores marcados en el formulario.')

    else:
        form = HistoriaClinicaForm()

    return render(request, 'expedientes/captura/formulario.html', {
        'form': form,
        'titulo': 'Nueva Historia Clínica',
        'modo': 'crear',
    })


@login_requerido
def editar_historia(request, pk):
    """Edita una historia clínica existente."""
    historia = get_object_or_404(HistoriaClinica, pk=pk)

    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST, instance=historia)

        if form.is_valid():
            historia = form.save(commit=False)
            historia.save()
            form.save_m2m()

            # Reemplazar tratamientos
            historia.tratamientos_detalle.all().delete()
            _guardar_tratamientos(historia, form)

            messages.success(request, f'Historia clínica #{historia.consulta_numero} actualizada.')
            return redirect('detalle_historia', pk=historia.pk)
        else:
            messages.error(request, 'Por favor corrige los errores marcados en el formulario.')

    else:
        form = HistoriaClinicaForm(instance=historia)

    return render(request, 'expedientes/captura/formulario.html', {
        'form': form,
        'titulo': f'Editar Historia #{historia.consulta_numero}',
        'modo': 'editar',
        'historia': historia,
    })


def _guardar_tratamientos(historia, form):
    """
    Guarda los tratamientos A (previo) y B (recomendado) en la tabla intermedia.
    Función privada — solo se usa dentro de este módulo.
    """
    especificar_a = form.cleaned_data.get('tratamiento_a_especificar', '')
    especificar_b = form.cleaned_data.get('tratamiento_b_especificar', '')

    for tratamiento in form.cleaned_data.get('tratamiento_a', []):
        HistoriaClinicaTratamiento.objects.get_or_create(
            historia=historia,
            tratamiento=tratamiento,
            columna='A',
            defaults={'especificar': especificar_a if tratamiento.requiere_especificar else ''}
        )

    for tratamiento in form.cleaned_data.get('tratamiento_b', []):
        HistoriaClinicaTratamiento.objects.get_or_create(
            historia=historia,
            tratamiento=tratamiento,
            columna='B',
            defaults={'especificar': especificar_b if tratamiento.requiere_especificar else ''}
        )


@login_requerido
def circunstancias_nivel2(request):
    """
    Vista AJAX: devuelve las opciones de circunstancia nivel 2
    según el nivel 1 seleccionado.
    Se llama desde JavaScript cuando el usuario cambia el dropdown nivel 1.
    """
    nivel1_id = request.GET.get('nivel1_id')
    opciones = []

    if nivel1_id:
        qs = CatCircunstanciaNivel2.objects.filter(
            nivel1_id=nivel1_id, activo=True
        ).values('id', 'nombre')
        opciones = list(qs)

    # JsonResponse convierte el diccionario Python a formato JSON automáticamente
    return JsonResponse({'opciones': opciones})
