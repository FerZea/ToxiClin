"""
Vistas de estadísticas y gráficas para ToxiClin.

RF-22: Selección de variables (hasta 4 simultáneas)
RF-25: Filtro temporal (último mes/trimestre/año/rango/todos)
RF-26: Exportar gráfica como PNG
RF-27: Dashboard con resumen de datos reales
"""

import io
from datetime import date
from dateutil.relativedelta import relativedelta

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.utils import timezone

from expedientes.decoradores import login_requerido
from expedientes.models import HistoriaClinica
from expedientes.graficas import (
    VARIABLES_DISPONIBLES,
    conteos_por_variable,
    grafica_barras, grafica_barras_bytes,
    grafica_pastel, grafica_pastel_bytes,
    grafica_linea_temporal, grafica_linea_temporal_bytes,
    _tabla_frecuencias,
)


# ─── Períodos de tiempo disponibles ─────────────────────────────────────────

PERIODOS = [
    ('todo',       'Todos los registros'),
    ('mes',        'Último mes'),
    ('trimestre',  'Último trimestre (3 meses)'),
    ('anio',       'Último año (12 meses)'),
    ('rango',      'Rango personalizado'),
]

TIPOS_GRAFICA = [
    ('barras', 'Barras horizontales'),
    ('pastel', 'Pastel / Dona'),
    ('linea',  'Línea temporal (casos por mes)'),
]


def _filtrar_por_periodo(qs, periodo, fecha_desde=None, fecha_hasta=None):
    """
    Recorta el queryset según el período seleccionado.
    Usa fecha_hora_consulta como referencia.
    """
    hoy = timezone.now().date()

    if periodo == 'mes':
        inicio = hoy - relativedelta(months=1)
        return qs.filter(fecha_hora_consulta__date__gte=inicio)

    elif periodo == 'trimestre':
        inicio = hoy - relativedelta(months=3)
        return qs.filter(fecha_hora_consulta__date__gte=inicio)

    elif periodo == 'anio':
        inicio = hoy - relativedelta(years=1)
        return qs.filter(fecha_hora_consulta__date__gte=inicio)

    elif periodo == 'rango':
        if fecha_desde:
            qs = qs.filter(fecha_hora_consulta__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_hora_consulta__date__lte=fecha_hasta)
        return qs

    # 'todo' u otro valor: sin restricción de tiempo
    return qs


@login_requerido
def estadisticas(request):
    """
    Página principal de estadísticas.
    El usuario selecciona período, tipo de gráfica y hasta 4 variables.
    Se genera una gráfica + tabla de frecuencias por cada variable.
    """
    # Leer parámetros GET del formulario
    periodo       = request.GET.get('periodo', 'todo')
    tipo_grafica  = request.GET.get('tipo_grafica', 'barras')
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')
    variables_sel = request.GET.getlist('variables')  # lista de hasta 4

    # Parsear fechas del rango personalizado
    fecha_desde = None
    fecha_hasta = None
    if periodo == 'rango':
        try:
            if fecha_desde_str:
                fecha_desde = date.fromisoformat(fecha_desde_str)
        except ValueError:
            pass
        try:
            if fecha_hasta_str:
                fecha_hasta = date.fromisoformat(fecha_hasta_str)
        except ValueError:
            pass

    # Limitar a 4 variables (RF-22)
    variables_sel = [v for v in variables_sel if v in VARIABLES_DISPONIBLES][:4]

    # Queryset base filtrado por período
    qs = HistoriaClinica.objects.all()
    qs = _filtrar_por_periodo(qs, periodo, fecha_desde, fecha_hasta)
    total_en_periodo = qs.count()

    # Generar una gráfica + tabla por cada variable seleccionada
    resultados = []
    for variable in variables_sel:
        titulo = VARIABLES_DISPONIBLES[variable]
        conteos = conteos_por_variable(qs, variable)
        tabla   = _tabla_frecuencias(conteos)

        # La gráfica de línea no depende de la variable (siempre casos/mes)
        if tipo_grafica == 'linea':
            imagen_b64 = grafica_linea_temporal(qs, titulo=f'Casos por mes — {titulo}')
        elif tipo_grafica == 'pastel':
            imagen_b64 = grafica_pastel(conteos, titulo)
        else:  # barras (default)
            imagen_b64 = grafica_barras(conteos, titulo)

        resultados.append({
            'variable':  variable,
            'titulo':    titulo,
            'imagen':    imagen_b64,
            'tabla':     tabla,
            'total':     sum(conteos.values()) if conteos else 0,
        })

    contexto = {
        'periodos':       PERIODOS,
        'tipos_grafica':  TIPOS_GRAFICA,
        'variables_disp': VARIABLES_DISPONIBLES,
        'periodo_sel':    periodo,
        'tipo_sel':       tipo_grafica,
        'variables_sel':  variables_sel,
        'fecha_desde':    fecha_desde_str,
        'fecha_hasta':    fecha_hasta_str,
        'total_en_periodo': total_en_periodo,
        'resultados':     resultados,
    }
    return render(request, 'expedientes/estadisticas/graficas.html', contexto)


@login_requerido
def exportar_grafica(request):
    """
    RF-26: Descarga una gráfica como archivo PNG.
    Recibe los mismos parámetros GET que la vista principal
    más 'variable' (una sola) para saber qué exportar.
    """
    periodo      = request.GET.get('periodo', 'todo')
    tipo_grafica = request.GET.get('tipo_grafica', 'barras')
    variable     = request.GET.get('variable', '')
    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')

    if variable not in VARIABLES_DISPONIBLES:
        raise Http404('Variable no válida')

    fecha_desde = None
    fecha_hasta = None
    if periodo == 'rango':
        try:
            if fecha_desde_str:
                fecha_desde = date.fromisoformat(fecha_desde_str)
        except ValueError:
            pass
        try:
            if fecha_hasta_str:
                fecha_hasta = date.fromisoformat(fecha_hasta_str)
        except ValueError:
            pass

    qs = HistoriaClinica.objects.all()
    qs = _filtrar_por_periodo(qs, periodo, fecha_desde, fecha_hasta)

    titulo  = VARIABLES_DISPONIBLES[variable]
    conteos = conteos_por_variable(qs, variable)

    if tipo_grafica == 'linea':
        datos_png = grafica_linea_temporal_bytes(qs, titulo=f'Casos por mes — {titulo}')
    elif tipo_grafica == 'pastel':
        datos_png = grafica_pastel_bytes(conteos, titulo)
    else:
        datos_png = grafica_barras_bytes(conteos, titulo)

    if datos_png is None:
        raise Http404('No hay datos para generar la gráfica')

    nombre_archivo = f'grafica_{variable}_{periodo}.png'
    respuesta = HttpResponse(datos_png, content_type='image/png')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return respuesta
