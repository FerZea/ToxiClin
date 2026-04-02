"""
Vistas de consulta: listado con filtros y detalle de historias clínicas.
"""

from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from expedientes.decoradores import login_requerido
from expedientes.forms.filtrado import FiltroHistoriaForm
from expedientes.models import HistoriaClinica


def _q_rango_edad(edad_min_años, edad_max_años):
    """
    Corrección 2: construye un Q que cubre las tres unidades de edad
    (días, meses, años) para no excluir lactantes ni niños < 1 año.

    Conversiones aproximadas usadas:
      1 año  ≈ 365 días  ≈ 12 meses
    """
    if edad_min_años is None and edad_max_años is None:
        return Q()  # Sin restricción

    condiciones = Q()

    # ── Registros en AÑOS ─────────────────────────────────────────────────
    q_años = Q(edad_unidad='a')
    if edad_min_años is not None:
        q_años &= Q(edad_valor__gte=edad_min_años)
    if edad_max_años is not None:
        q_años &= Q(edad_valor__lte=edad_max_años)
    condiciones |= q_años

    # ── Registros en MESES ────────────────────────────────────────────────
    q_meses = Q(edad_unidad='m')
    if edad_min_años is not None:
        q_meses &= Q(edad_valor__gte=edad_min_años * 12)
    if edad_max_años is not None:
        q_meses &= Q(edad_valor__lte=edad_max_años * 12)
    condiciones |= q_meses

    # ── Registros en DÍAS ─────────────────────────────────────────────────
    q_dias = Q(edad_unidad='d')
    if edad_min_años is not None:
        q_dias &= Q(edad_valor__gte=edad_min_años * 365)
    if edad_max_años is not None:
        q_dias &= Q(edad_valor__lte=edad_max_años * 365)
    condiciones |= q_dias

    return condiciones


@login_requerido
def listado_historias(request):
    """
    Listado de historias clínicas con filtros, búsqueda y paginación.
    Todos los filtros son opcionales y se combinan entre sí (AND).
    """
    form = FiltroHistoriaForm(request.GET or None)

    qs = HistoriaClinica.objects.select_related(
        'sexo', 'tipo_agente', 'severidad', 'tipo_contacto',
        'motivo_consulta', 'circunstancia_nivel1', 'usuario_captura',
    ).order_by('-fecha_captura')

    hay_filtros = bool(request.GET)

    if form.is_valid():
        d = form.cleaned_data

        # ── Búsqueda por folio ────────────────────────────────────────────
        if d.get('folio'):
            qs = qs.filter(folio_expediente__icontains=d['folio'])

        # ── Búsqueda por paciente (RF-19: nombre + folio combinados) ──────
        # Si el usuario escribe texto en "paciente", buscamos en nombre,
        # apellido Y folio con OR, para encontrar todas las consultas de
        # un mismo paciente aunque varíe la ortografía o se ingrese el folio.
        if d.get('paciente'):
            texto = d['paciente']
            qs = qs.filter(
                Q(nombre__icontains=texto) |
                Q(apellido__icontains=texto) |
                Q(folio_expediente__icontains=texto)
            )

        # ── Búsqueda por agente ───────────────────────────────────────────
        if d.get('agente'):
            qs = qs.filter(agente_principio_activo__icontains=d['agente'])

        # ── Filtros por catálogo ──────────────────────────────────────────
        if d.get('sexo'):
            qs = qs.filter(sexo=d['sexo'])
        if d.get('tipo_contacto'):
            qs = qs.filter(tipo_contacto=d['tipo_contacto'])
        if d.get('motivo_consulta'):
            qs = qs.filter(motivo_consulta=d['motivo_consulta'])
        if d.get('circunstancia'):
            qs = qs.filter(circunstancia_nivel1=d['circunstancia'])
        if d.get('tipo_agente'):
            qs = qs.filter(tipo_agente=d['tipo_agente'])
        if d.get('severidad'):
            qs = qs.filter(severidad=d['severidad'])
        if d.get('evolucion'):
            qs = qs.filter(evolucion=d['evolucion'])
        if d.get('via_ingreso'):
            qs = qs.filter(vias_ingreso=d['via_ingreso'])

        # Corrección 3 — RF-17: filtro por ubicación del evento
        if d.get('ubicacion_evento'):
            qs = qs.filter(ubicacion_evento=d['ubicacion_evento'])

        # ── Rango de fechas ───────────────────────────────────────────────
        if d.get('fecha_desde'):
            qs = qs.filter(fecha_hora_consulta__date__gte=d['fecha_desde'])
        if d.get('fecha_hasta'):
            qs = qs.filter(fecha_hora_consulta__date__lte=d['fecha_hasta'])

        # Corrección 2 — RF-17: rango de edad cubre días, meses y años
        edad_min = d.get('edad_min')
        edad_max = d.get('edad_max')
        if edad_min is not None or edad_max is not None:
            qs = qs.filter(_q_rango_edad(edad_min, edad_max))

    # distinct() evita duplicados cuando se filtra por ManyToMany (vias_ingreso)
    qs = qs.distinct()
    total = qs.count()

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
