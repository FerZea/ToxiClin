"""
Vistas de consulta: listado con filtros y detalle de historias clínicas.
"""

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from expedientes.decoradores import login_requerido
from expedientes.forms.filtrado import FiltroHistoriaForm
from expedientes.models import HistoriaClinica


@login_requerido
def listado_historias(request):
    """
    Listado de historias clínicas con filtros, búsqueda y paginación.
    Todos los filtros son opcionales y se combinan entre sí (AND).
    """
    form = FiltroHistoriaForm(request.GET or None)

    # Empezamos con todos los registros, ordenados por más reciente
    qs = HistoriaClinica.objects.select_related(
        'sexo', 'tipo_agente', 'severidad', 'tipo_contacto',
        'motivo_consulta', 'circunstancia_nivel1', 'usuario_captura',
    ).order_by('-fecha_captura')

    hay_filtros = bool(request.GET)

    if form.is_valid():
        # ── Búsquedas textuales ───────────────────────────────────────────
        folio = form.cleaned_data.get('folio')
        if folio:
            # icontains: búsqueda sin importar mayúsculas/minúsculas
            qs = qs.filter(folio_expediente__icontains=folio)

        paciente = form.cleaned_data.get('paciente')
        if paciente:
            # Busca en nombre Y apellido con el mismo texto
            from django.db.models import Q
            qs = qs.filter(
                Q(nombre__icontains=paciente) | Q(apellido__icontains=paciente)
            )

        agente = form.cleaned_data.get('agente')
        if agente:
            qs = qs.filter(agente_principio_activo__icontains=agente)

        # ── Filtros por catálogo ──────────────────────────────────────────
        if form.cleaned_data.get('sexo'):
            qs = qs.filter(sexo=form.cleaned_data['sexo'])

        if form.cleaned_data.get('tipo_contacto'):
            qs = qs.filter(tipo_contacto=form.cleaned_data['tipo_contacto'])

        if form.cleaned_data.get('motivo_consulta'):
            qs = qs.filter(motivo_consulta=form.cleaned_data['motivo_consulta'])

        if form.cleaned_data.get('circunstancia'):
            qs = qs.filter(circunstancia_nivel1=form.cleaned_data['circunstancia'])

        if form.cleaned_data.get('tipo_agente'):
            qs = qs.filter(tipo_agente=form.cleaned_data['tipo_agente'])

        if form.cleaned_data.get('severidad'):
            qs = qs.filter(severidad=form.cleaned_data['severidad'])

        if form.cleaned_data.get('evolucion'):
            qs = qs.filter(evolucion=form.cleaned_data['evolucion'])

        if form.cleaned_data.get('via_ingreso'):
            # ManyToMany: filter por vías que incluyan la seleccionada
            qs = qs.filter(vias_ingreso=form.cleaned_data['via_ingreso'])

        # ── Rango de fechas ───────────────────────────────────────────────
        if form.cleaned_data.get('fecha_desde'):
            qs = qs.filter(
                fecha_hora_consulta__date__gte=form.cleaned_data['fecha_desde']
            )
        if form.cleaned_data.get('fecha_hasta'):
            qs = qs.filter(
                fecha_hora_consulta__date__lte=form.cleaned_data['fecha_hasta']
            )

        # ── Rango de edad ─────────────────────────────────────────────────
        # Filtra solo sobre registros con unidad 'a' (años) para simplificar.
        # Para edades menores de 1 año, el usuario puede buscar edad_min=0.
        edad_min = form.cleaned_data.get('edad_min')
        edad_max = form.cleaned_data.get('edad_max')
        if edad_min is not None or edad_max is not None:
            qs = qs.filter(edad_unidad='a')
            if edad_min is not None:
                qs = qs.filter(edad_valor__gte=edad_min)
            if edad_max is not None:
                qs = qs.filter(edad_valor__lte=edad_max)

    total = qs.count()

    # ── Paginación: 20 registros por página ───────────────────────────────
    # Paginator divide el queryset en páginas automáticamente
    paginator = Paginator(qs, 20)
    pagina_num = request.GET.get('pagina', 1)
    try:
        pagina = paginator.page(pagina_num)
    except Exception:
        pagina = paginator.page(1)

    return render(request, 'expedientes/consulta/listado.html', {
        'form': form,
        'historias': pagina,
        'total': total,
        'hay_filtros': hay_filtros,
        'paginator': paginator,
    })


@login_requerido
def detalle_historia(request, pk):
    """Vista de detalle completa de una historia clínica."""
    historia = get_object_or_404(HistoriaClinica, pk=pk)
    tratamientos_a = historia.tratamientos_detalle.filter(
        columna='A'
    ).select_related('tratamiento')
    tratamientos_b = historia.tratamientos_detalle.filter(
        columna='B'
    ).select_related('tratamiento')

    return render(request, 'expedientes/consulta/detalle.html', {
        'historia': historia,
        'tratamientos_a': tratamientos_a,
        'tratamientos_b': tratamientos_b,
    })
