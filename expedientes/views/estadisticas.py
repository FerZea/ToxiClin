"""
Vistas de estadísticas y gráficas para ToxiClin.

RF-22: Selección de variables (hasta 4) y cruce entre ellas
RF-23: Barras, pastel, línea temporal y barras agrupadas
RF-24: Tabla de frecuencias y tabla cruzada
RF-25: Filtro temporal (último mes/trimestre/año/rango/todos)
RF-26: Exportar gráfica como PNG
RF-27: Dashboard con resumen de datos reales

Acceso restringido a administradoras (@solo_admin).
El dashboard (inicio.py) es para todos los usuarios autenticados.
"""

from datetime import date
from dateutil.relativedelta import relativedelta

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.utils import timezone

from expedientes.decoradores import solo_admin
from expedientes.models import HistoriaClinica
from expedientes.graficas import (
    VARIABLES_DISPONIBLES,
    VARIABLES_CRUZABLES,
    conteos_por_variable,
    conteos_cruzados,
    tabla_cruzada,
    grafica_barras, grafica_barras_bytes,
    grafica_pastel, grafica_pastel_bytes,
    grafica_linea_temporal, grafica_linea_temporal_bytes,
    grafica_barras_agrupadas, grafica_barras_agrupadas_bytes,
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
    ('barras',           'Barras horizontales'),
    ('pastel',           'Pastel / Dona'),
    ('linea',            'Línea temporal (casos por mes)'),
    ('barras_agrupadas', 'Barras agrupadas (cruce de 2 variables)'),
]


def _filtrar_por_periodo(qs, periodo, fecha_desde=None, fecha_hasta=None):
    """Recorta el queryset según el período seleccionado."""
    hoy = timezone.now().date()

    if periodo == 'mes':
        return qs.filter(fecha_hora_consulta__date__gte=hoy - relativedelta(months=1))
    elif periodo == 'trimestre':
        return qs.filter(fecha_hora_consulta__date__gte=hoy - relativedelta(months=3))
    elif periodo == 'anio':
        return qs.filter(fecha_hora_consulta__date__gte=hoy - relativedelta(years=1))
    elif periodo == 'rango':
        if fecha_desde:
            qs = qs.filter(fecha_hora_consulta__date__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha_hora_consulta__date__lte=fecha_hasta)
        return qs

    return qs  # 'todo'


def _parsear_fecha(texto):
    """Parsea una fecha ISO (YYYY-MM-DD) o devuelve None si falla."""
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


@solo_admin
def estadisticas(request):
    """
    Página principal de estadísticas (solo administradoras).

    Flujo principal:
    - Si tipo_grafica == 'barras_agrupadas' y hay 2+ variables cruzables:
        → genera una gráfica agrupada + tabla cruzada con las primeras 2
        → las variables restantes (3ª y 4ª) se grafican de forma simple
    - En todos los demás casos:
        → genera una gráfica independiente por cada variable seleccionada
    """
    periodo       = request.GET.get('periodo', 'todo')
    tipo_grafica  = request.GET.get('tipo_grafica', 'barras')
    fecha_desde   = _parsear_fecha(request.GET.get('fecha_desde', ''))
    fecha_hasta   = _parsear_fecha(request.GET.get('fecha_hasta', ''))
    variables_sel = [v for v in request.GET.getlist('variables')
                     if v in VARIABLES_DISPONIBLES][:4]

    qs = _filtrar_por_periodo(
        HistoriaClinica.objects.all(), periodo, fecha_desde, fecha_hasta
    )
    total_en_periodo = qs.count()

    resultados = []

    if tipo_grafica == 'barras_agrupadas':
        # Separar variables cruzables (FK simples) de no cruzables (M2M)
        cruzables    = [v for v in variables_sel if v in VARIABLES_CRUZABLES]
        no_cruzables = [v for v in variables_sel if v not in VARIABLES_CRUZABLES]

        if len(cruzables) >= 2:
            # Cruce de las dos primeras variables cruzables (RF-22/RF-24)
            var_x  = cruzables[0]
            var_g  = cruzables[1]
            tit_x  = VARIABLES_DISPONIBLES[var_x]
            tit_g  = VARIABLES_DISPONIBLES[var_g]
            titulo = f'{tit_x}  ×  {tit_g}'

            cruzado = conteos_cruzados(qs, var_x, var_g)
            grupos, filas = tabla_cruzada(cruzado)

            resultados.append({
                'variable':      f'{var_x}__x__{var_g}',
                'titulo':        titulo,
                'imagen':        grafica_barras_agrupadas(cruzado, tit_x, tit_g, titulo),
                'tabla':         None,      # la tabla cruzada reemplaza a la tabla simple
                'es_cruce':      True,
                'grupos_cruce':  grupos,
                'filas_cruce':   filas,
                'total':         sum(f['total'] for f in filas),
                'exportar_vars': f'variable={var_x}&variable2={var_g}',
            })

            # Variables 3ª y 4ª (y las no cruzables) van como barras simples
            for variable in cruzables[2:] + no_cruzables:
                resultados.append(_resultado_simple(qs, variable, 'barras'))
        else:
            # No hay 2 variables cruzables: fallback a barras simples
            for variable in variables_sel:
                resultados.append(_resultado_simple(qs, variable, 'barras'))
    else:
        # Gráficas independientes: barras, pastel o linea
        for variable in variables_sel:
            resultados.append(_resultado_simple(qs, variable, tipo_grafica))

    fecha_desde_str = request.GET.get('fecha_desde', '')
    fecha_hasta_str = request.GET.get('fecha_hasta', '')

    return render(request, 'expedientes/estadisticas/graficas.html', {
        'periodos':            PERIODOS,
        'tipos_grafica':       TIPOS_GRAFICA,
        'variables_disp':      VARIABLES_DISPONIBLES,
        'variables_cruzables': set(VARIABLES_CRUZABLES.keys()),
        'periodo_sel':         periodo,
        'tipo_sel':            tipo_grafica,
        'variables_sel':       variables_sel,
        'fecha_desde':         fecha_desde_str,
        'fecha_hasta':         fecha_hasta_str,
        'total_en_periodo':    total_en_periodo,
        'resultados':          resultados,
    })


def _resultado_simple(qs, variable, tipo_grafica):
    """Genera el dict de resultado para una variable con gráfica individual."""
    titulo  = VARIABLES_DISPONIBLES[variable]
    conteos = conteos_por_variable(qs, variable)
    tabla   = _tabla_frecuencias(conteos)

    if tipo_grafica == 'linea':
        imagen = grafica_linea_temporal(qs, titulo=f'Casos por mes — {titulo}')
    elif tipo_grafica == 'pastel':
        imagen = grafica_pastel(conteos, titulo)
    else:
        imagen = grafica_barras(conteos, titulo)

    return {
        'variable':      variable,
        'titulo':        titulo,
        'imagen':        imagen,
        'tabla':         tabla,
        'es_cruce':      False,
        'total':         sum(conteos.values()) if conteos else 0,
        'exportar_vars': f'variable={variable}',
    }


@solo_admin
def exportar_grafica(request):
    """
    RF-26: Descarga una gráfica como archivo PNG.

    Parámetros GET:
        variable    — clave de VARIABLES_DISPONIBLES (requerido)
        variable2   — segunda variable para barras agrupadas (opcional)
        tipo_grafica — barras / pastel / linea / barras_agrupadas
        periodo     — todo / mes / trimestre / anio / rango
        fecha_desde / fecha_hasta — para periodo=rango
    """
    variable     = request.GET.get('variable', '')
    variable2    = request.GET.get('variable2', '')
    tipo_grafica = request.GET.get('tipo_grafica', 'barras')
    periodo      = request.GET.get('periodo', 'todo')
    fecha_desde  = _parsear_fecha(request.GET.get('fecha_desde', ''))
    fecha_hasta  = _parsear_fecha(request.GET.get('fecha_hasta', ''))

    if variable not in VARIABLES_DISPONIBLES:
        raise Http404('Variable no válida')

    qs = _filtrar_por_periodo(
        HistoriaClinica.objects.all(), periodo, fecha_desde, fecha_hasta
    )

    titulo    = VARIABLES_DISPONIBLES[variable]
    datos_png = None

    if (tipo_grafica == 'barras_agrupadas'
            and variable in VARIABLES_CRUZABLES
            and variable2 in VARIABLES_CRUZABLES):
        tit_x   = VARIABLES_DISPONIBLES[variable]
        tit_g   = VARIABLES_DISPONIBLES[variable2]
        cruzado = conteos_cruzados(qs, variable, variable2)
        datos_png = grafica_barras_agrupadas_bytes(
            cruzado, tit_x, tit_g, f'{tit_x}  ×  {tit_g}'
        )
        nombre_archivo = f'cruce_{variable}_{variable2}_{periodo}.png'

    elif tipo_grafica == 'linea':
        datos_png = grafica_linea_temporal_bytes(
            qs, titulo=f'Casos por mes — {titulo}'
        )
        nombre_archivo = f'linea_{variable}_{periodo}.png'

    elif tipo_grafica == 'pastel':
        conteos = conteos_por_variable(qs, variable)
        datos_png = grafica_pastel_bytes(conteos, titulo)
        nombre_archivo = f'pastel_{variable}_{periodo}.png'

    else:
        conteos = conteos_por_variable(qs, variable)
        datos_png = grafica_barras_bytes(conteos, titulo)
        nombre_archivo = f'barras_{variable}_{periodo}.png'

    if datos_png is None:
        raise Http404('No hay datos para generar la gráfica')

    respuesta = HttpResponse(datos_png, content_type='image/png')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return respuesta
