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


def _ids_tratamientos_del_post(request):
    """Extrae los IDs de tratamientos A y B del POST como sets de enteros."""
    try:
        ids_a = set(int(x) for x in request.POST.getlist('tratamiento_a'))
    except (ValueError, TypeError):
        ids_a = set()
    try:
        ids_b = set(int(x) for x in request.POST.getlist('tratamiento_b'))
    except (ValueError, TypeError):
        ids_b = set()
    return ids_a, ids_b


@login_requerido
def nueva_historia(request):
    """Muestra y procesa el formulario de nueva historia clínica."""

    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST)
        ids_a, ids_b = _ids_tratamientos_del_post(request)

        if form.is_valid():
            historia = form.save(commit=False)
            historia.usuario_captura = request.user
            historia.save()
            form.save_m2m()
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
        ids_a, ids_b = set(), set()

    return render(request, 'expedientes/captura/formulario.html', {
        'form': form,
        'titulo': 'Nueva Historia Clínica',
        'modo': 'crear',
        'ids_a': ids_a,
        'ids_b': ids_b,
    })


@login_requerido
def editar_historia(request, pk):
    """Edita una historia clínica existente."""
    historia = get_object_or_404(HistoriaClinica, pk=pk)

    # Bug 2: solo admins/superusuario o el capturista original pueden editar
    es_admin = request.user.is_superuser or \
               request.user.groups.filter(name='Administrador').exists()
    es_autor = historia.usuario_captura == request.user

    if not (es_admin or es_autor):
        messages.error(request, 'Solo puedes editar expedientes que tú capturaste.')
        return redirect('detalle_historia', pk=historia.pk)

    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST, instance=historia)
        ids_a, ids_b = _ids_tratamientos_del_post(request)

        if form.is_valid():
            historia = form.save(commit=False)
            historia.save()
            form.save_m2m()
            # Reemplazar tratamientos solo si vienen en el POST
            # (evita borrar si se hace un post parcial o hay errores de widget)
            if 'tratamiento_a' in request.POST or 'tratamiento_a' in form.errors:
                 historia.tratamientos_detalle.filter(columna='A').delete()
                 _guardar_tratamientos_columna(historia, form, 'A')

            if 'tratamiento_b' in request.POST or 'tratamiento_b' in form.errors:
                 historia.tratamientos_detalle.filter(columna='B').delete()
                 _guardar_tratamientos_columna(historia, form, 'B')

            messages.success(request, f'Historia clínica #{historia.consulta_numero} actualizada.')
            return redirect('detalle_historia', pk=historia.pk)
        else:
            messages.error(request, 'Por favor corrige los errores marcados en el formulario.')

    else:
        form = HistoriaClinicaForm(instance=historia)
        # Precargar IDs para el template (GET inicial)
        ids_a = set(
            historia.tratamientos_detalle
            .filter(columna='A').values_list('tratamiento_id', flat=True)
        )
        ids_b = set(
            historia.tratamientos_detalle
            .filter(columna='B').values_list('tratamiento_id', flat=True)
        )

    return render(request, 'expedientes/captura/formulario.html', {
        'form': form,
        'titulo': f'Editar Historia #{historia.consulta_numero}',
        'modo': 'editar',
        'historia': historia,
        'ids_a': ids_a,
        'ids_b': ids_b,
    })


def _guardar_tratamientos_columna(historia, form, columna):
    """Guarda los tratamientos de una columna específica (A/B)."""
    field_name = f'tratamiento_{columna.lower()}'
    especificar_field = f'tratamiento_{columna.lower()}_especificar'
    
    especificar_texto = form.cleaned_data.get(especificar_field, '')
    
    for tratamiento in form.cleaned_data.get(field_name, []):
        HistoriaClinicaTratamiento.objects.create(
            historia=historia,
            tratamiento=tratamiento,
            columna=columna,
            especificar=especificar_texto if tratamiento.requiere_especificar else ''
        )


def _guardar_tratamientos(historia, form):
    """Guarda ambas columnas (A y B)."""
    _guardar_tratamientos_columna(historia, form, 'A')
    _guardar_tratamientos_columna(historia, form, 'B')


@login_requerido
def circunstancias_nivel2(request):
    """Vista AJAX: opciones de circunstancia nivel 2 según nivel 1."""
    nivel1_id = request.GET.get('nivel1_id')
    opciones = []
    if nivel1_id:
        qs = CatCircunstanciaNivel2.objects.filter(
            nivel1_id=nivel1_id, activo=True
        ).values('id', 'nombre')
        opciones = list(qs)
    return JsonResponse({'opciones': opciones})
