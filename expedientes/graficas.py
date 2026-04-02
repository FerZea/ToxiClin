"""
Módulo de generación de gráficas para ToxiClin.
Usa matplotlib para producir imágenes en memoria (sin guardar archivos).

Cada función recibe un queryset ya filtrado y devuelve:
  - Una imagen PNG como bytes (para descargar o incrustar en HTML como base64)
  - Una tabla de frecuencias como lista de dicts

Usamos matplotlib en modo no interactivo (backend 'Agg') para que funcione
en el servidor sin monitor ni entorno gráfico.
"""

import io
import os
import base64
from pathlib import Path
from collections import Counter
from django.utils import timezone

# Fijar una carpeta de caché writable para matplotlib dentro del proyecto.
# Evita warnings en entornos donde ~/.config/matplotlib no es escribible.
MPLCONFIGDIR = Path(__file__).resolve().parent.parent / '.matplotlib'
MPLCONFIGDIR.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(MPLCONFIGDIR))

# Configurar matplotlib para modo servidor (sin GUI)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Paleta de colores del CIAT (azul institucional como base)
COLORES = [
    '#1a3a5c', '#2a7ab8', '#4caf8a', '#f5a623',
    '#e05a5a', '#7b68ee', '#20b2aa', '#ff8c00',
    '#9370db', '#3cb371', '#cd5c5c', '#4169e1',
]

# Tamaño de fuente para que las etiquetas sean legibles al exportar
plt.rcParams.update({
    'font.size': 10,
    'axes.titlesize': 12,
    'figure.facecolor': 'white',
    'axes.facecolor': '#f8f9ff',
})


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _fig_a_base64(fig):
    """Convierte una figura matplotlib a string base64 para incrustar en HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110)
    buf.seek(0)
    imagen_b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return imagen_b64


def _fig_a_bytes(fig, formato='png'):
    """Convierte una figura matplotlib a bytes PNG/JPG para descarga."""
    buf = io.BytesIO()
    if formato == 'jpg':
        fig.savefig(buf, format='jpeg', bbox_inches='tight', dpi=150)
    else:
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    datos = buf.read()
    plt.close(fig)
    return datos


def _tabla_frecuencias(conteos):
    """
    Convierte un dict {etiqueta: conteo} a lista de dicts con porcentaje.
    Ordena de mayor a menor.
    """
    total = sum(conteos.values())
    if total == 0:
        return []
    tabla = [
        {
            'etiqueta': etiqueta,
            'conteo': conteo,
            'porcentaje': round(conteo * 100 / total, 1),
        }
        for etiqueta, conteo in sorted(conteos.items(), key=lambda x: -x[1])
    ]
    return tabla


def _truncar(texto, max_chars=25):
    """Trunca etiquetas largas para que quepan en el gráfico."""
    return texto[:max_chars] + '…' if len(texto) > max_chars else texto


# ─── Obtener conteos por variable ────────────────────────────────────────────

VARIABLES_DISPONIBLES = {
    'tipo_agente':       'Tipo de agente',
    'edad_rango':        'Edad (rangos)',
    'circunstancia':     'Circunstancia (Nivel 1)',
    'severidad':         'Severidad',
    'sexo':              'Sexo',
    'motivo_consulta':   'Motivo de consulta',
    'via_ingreso':       'Vía de ingreso',
    'evolucion':         'Evolución',
    'tipo_contacto':     'Tipo de contacto',
    'ubicacion_evento':  'Ubicación del evento',
}

# Via de ingreso es ManyToMany; no se puede cruzar con .values() simple.
# El cruce (barras agrupadas) solo funciona con las 8 variables FK simples.
VARIABLES_CRUZABLES = {k: v for k, v in VARIABLES_DISPONIBLES.items()
                       if k != 'via_ingreso'}

# Mapa de clave de variable → campo ORM para usar en .values()
_CAMPO_ORM = {
    'tipo_agente':      'tipo_agente__nombre',
    'circunstancia':    'circunstancia_nivel1__nombre',
    'severidad':        'severidad__nombre',
    'sexo':             'sexo__nombre',
    'motivo_consulta':  'motivo_consulta__nombre',
    'evolucion':        'evolucion__nombre',
    'tipo_contacto':    'tipo_contacto__nombre',
    'ubicacion_evento': 'ubicacion_evento__nombre',
}

# Mapa de clave de variable → campo FK del modelo (para exclude isnull)
_CAMPO_FK = {
    'tipo_agente':      'tipo_agente',
    'circunstancia':    'circunstancia_nivel1',
    'severidad':        'severidad',
    'sexo':             'sexo',
    'motivo_consulta':  'motivo_consulta',
    'evolucion':        'evolucion',
    'tipo_contacto':    'tipo_contacto',
    'ubicacion_evento': 'ubicacion_evento',
}


def _etiqueta_edad_rango(edad_valor, edad_unidad):
    """
    Convierte la edad almacenada (días/meses/años) a un rango clínico legible.
    """
    if edad_valor is None or not edad_unidad:
        return None

    if edad_unidad in ('d', 'm'):
        return '<1 año'

    if edad_unidad != 'a':
        return None

    if edad_valor < 1:
        return '<1 año'
    if edad_valor <= 4:
        return '1-4 años'
    if edad_valor <= 14:
        return '5-14 años'
    if edad_valor <= 24:
        return '15-24 años'
    if edad_valor <= 44:
        return '25-44 años'
    if edad_valor <= 64:
        return '45-64 años'
    return '65+ años'


def conteos_por_variable(qs, variable):
    """
    Devuelve un dict {nombre_opción: conteo} para la variable seleccionada.
    """
    if variable == 'tipo_agente':
        datos = qs.exclude(tipo_agente__isnull=True).values_list(
            'tipo_agente__nombre', flat=True
        )
    elif variable == 'edad_rango':
        datos = [
            etiqueta
            for edad_valor, edad_unidad in qs.values_list('edad_valor', 'edad_unidad')
            for etiqueta in [_etiqueta_edad_rango(edad_valor, edad_unidad)]
            if etiqueta
        ]
    elif variable == 'circunstancia':
        datos = qs.exclude(circunstancia_nivel1__isnull=True).values_list(
            'circunstancia_nivel1__nombre', flat=True
        )
    elif variable == 'severidad':
        datos = qs.exclude(severidad__isnull=True).values_list(
            'severidad__nombre', flat=True
        )
    elif variable == 'sexo':
        datos = qs.exclude(sexo__isnull=True).values_list(
            'sexo__nombre', flat=True
        )
    elif variable == 'motivo_consulta':
        datos = qs.exclude(motivo_consulta__isnull=True).values_list(
            'motivo_consulta__nombre', flat=True
        )
    elif variable == 'via_ingreso':
        # ManyToMany: un registro puede tener varias vías
        datos = qs.values_list('vias_ingreso__nombre', flat=True).exclude(
            vias_ingreso__isnull=True
        )
    elif variable == 'evolucion':
        datos = qs.exclude(evolucion__isnull=True).values_list(
            'evolucion__nombre', flat=True
        )
    elif variable == 'tipo_contacto':
        datos = qs.exclude(tipo_contacto__isnull=True).values_list(
            'tipo_contacto__nombre', flat=True
        )
    elif variable == 'ubicacion_evento':
        datos = qs.exclude(ubicacion_evento__isnull=True).values_list(
            'ubicacion_evento__nombre', flat=True
        )
    else:
        return {}

    return dict(Counter(datos))


# ─── Gráfica de barras ───────────────────────────────────────────────────────

def grafica_barras(conteos, titulo, max_barras=15):
    """
    Genera una gráfica de barras horizontales.
    Horizontal porque los nombres de los catálogos son largos.
    """
    if not conteos:
        return None

    # Tomar las N más frecuentes
    items = sorted(conteos.items(), key=lambda x: x[1], reverse=True)[:max_barras]
    etiquetas = [_truncar(k) for k, _ in items]
    valores   = [v for _, v in items]

    fig, ax = plt.subplots(figsize=(9, max(4, len(etiquetas) * 0.45)))
    barras = ax.barh(etiquetas[::-1], valores[::-1],
                     color=COLORES[0], edgecolor='white')

    # Añadir el número al final de cada barra
    for barra, val in zip(barras, valores[::-1]):
        ax.text(barra.get_width() + 0.1, barra.get_y() + barra.get_height() / 2,
                str(val), va='center', fontsize=9)

    ax.set_title(titulo, pad=12, fontweight='bold')
    ax.set_xlabel('Número de casos')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    return _fig_a_base64(fig)


def grafica_barras_bytes(conteos, titulo, max_barras=15, formato='png'):
    if not conteos:
        return None
    items = sorted(conteos.items(), key=lambda x: x[1], reverse=True)[:max_barras]
    etiquetas = [_truncar(k) for k, _ in items]
    valores   = [v for _, v in items]
    fig, ax = plt.subplots(figsize=(9, max(4, len(etiquetas) * 0.45)))
    barras = ax.barh(etiquetas[::-1], valores[::-1],
                     color=COLORES[0], edgecolor='white')
    for barra, val in zip(barras, valores[::-1]):
        ax.text(barra.get_width() + 0.1, barra.get_y() + barra.get_height() / 2,
                str(val), va='center', fontsize=9)
    ax.set_title(titulo, pad=12, fontweight='bold')
    ax.set_xlabel('Número de casos')
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return _fig_a_bytes(fig, formato=formato)


# ─── Gráfica de pastel ───────────────────────────────────────────────────────

def grafica_pastel(conteos, titulo, max_sectores=10):
    """
    Genera una gráfica de pastel/dona.
    Agrupa en "Otros" los sectores menos frecuentes si hay más de max_sectores.
    """
    if not conteos:
        return None

    items = sorted(conteos.items(), key=lambda x: x[1], reverse=True)
    if len(items) > max_sectores:
        principales = items[:max_sectores - 1]
        otros_total = sum(v for _, v in items[max_sectores - 1:])
        items = principales + [('Otros', otros_total)]
    else:
        items = items

    etiquetas = [_truncar(k, 20) for k, _ in items]
    valores   = [v for _, v in items]
    colores   = COLORES[:len(items)]

    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, textos, autotextos = ax.pie(
        valores,
        labels=None,
        colors=colores,
        autopct=lambda p: f'{p:.1f}%' if p >= 3 else '',
        startangle=90,
        pctdistance=0.75,
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
    )
    for at in autotextos:
        at.set_fontsize(8)

    ax.legend(
        wedges,
        [f'{e} ({v})' for e, v in zip(etiquetas, valores)],
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        fontsize=8,
    )
    ax.set_title(titulo, pad=12, fontweight='bold')
    fig.tight_layout()

    return _fig_a_base64(fig)


def grafica_pastel_bytes(conteos, titulo, max_sectores=10, formato='png'):
    if not conteos:
        return None
    items = sorted(conteos.items(), key=lambda x: x[1], reverse=True)
    if len(items) > max_sectores:
        principales = items[:max_sectores - 1]
        otros_total = sum(v for _, v in items[max_sectores - 1:])
        items = principales + [('Otros', otros_total)]
    etiquetas = [_truncar(k, 20) for k, _ in items]
    valores   = [v for _, v in items]
    colores   = COLORES[:len(items)]
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, _, autotextos = ax.pie(
        valores, labels=None, colors=colores,
        autopct=lambda p: f'{p:.1f}%' if p >= 3 else '',
        startangle=90, pctdistance=0.75,
        wedgeprops={'linewidth': 1, 'edgecolor': 'white'},
    )
    for at in autotextos:
        at.set_fontsize(8)
    ax.legend(wedges, [f'{e} ({v})' for e, v in zip(etiquetas, valores)],
              loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
    ax.set_title(titulo, pad=12, fontweight='bold')
    fig.tight_layout()
    return _fig_a_bytes(fig, formato=formato)


# ─── Gráfica de línea temporal (casos por mes) ───────────────────────────────

def grafica_linea_temporal(qs, titulo='Casos por mes'):
    """
    Genera una gráfica de línea con el número de casos por mes.
    El eje X muestra los meses en orden cronológico.
    """
    from django.db.models import Count
    from django.db.models.functions import TruncMonth

    datos = (
        qs.exclude(fecha_hora_consulta__isnull=True)
        .annotate(mes=TruncMonth('fecha_hora_consulta'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    if not datos:
        return None

    meses  = [d['mes'] for d in datos]
    totales = [d['total'] for d in datos]
    etiquetas = [m.strftime('%b %Y') for m in meses]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(len(meses)), totales, color=COLORES[0],
            linewidth=2, marker='o', markersize=5)
    ax.fill_between(range(len(meses)), totales,
                    alpha=0.15, color=COLORES[0])

    ax.set_xticks(range(len(meses)))
    ax.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_title(titulo, pad=12, fontweight='bold')
    ax.set_ylabel('Número de casos')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    return _fig_a_base64(fig)


# ─── Cruce de dos variables (RF-22 / RF-24) ─────────────────────────────────

def conteos_cruzados(qs, variable_x, variable_grupo):
    """
    Cruza dos variables categóricas en el queryset.
    Devuelve un dict anidado: {cat_x: {cat_grupo: conteo}}.

    Solo funciona con variables de VARIABLES_CRUZABLES (ForeignKey simples).
    Ejemplo: variable_x='tipo_agente', variable_grupo='sexo'
    →  {'Medicamentos': {'Masculino': 10, 'Femenino': 8}, ...}
    """
    from django.db.models import Count

    if variable_x not in _CAMPO_ORM or variable_grupo not in _CAMPO_ORM:
        return {}

    campo_x = _CAMPO_ORM[variable_x]
    campo_g = _CAMPO_ORM[variable_grupo]
    fk_x    = _CAMPO_FK[variable_x]
    fk_g    = _CAMPO_FK[variable_grupo]

    datos = (
        qs
        .exclude(**{fk_x + '__isnull': True})
        .exclude(**{fk_g + '__isnull': True})
        .values(campo_x, campo_g)
        .annotate(total=Count('id'))
    )

    resultado = {}
    for d in datos:
        cat_x = d[campo_x] or '(sin dato)'
        cat_g = d[campo_g] or '(sin dato)'
        if cat_x not in resultado:
            resultado[cat_x] = {}
        resultado[cat_x][cat_g] = d['total']

    return resultado


def tabla_cruzada(cruzado):
    """
    Convierte el dict {cat_x: {cat_grupo: conteo}} a una estructura
    lista-de-filas + lista-de-encabezados para renderizar en la plantilla.

    Devuelve:
        grupos  — list de nombres de columnas del grupo
        filas   — list de dicts {etiqueta, valores: [int...], total: int}
    """
    if not cruzado:
        return [], []

    # Recopilar todos los valores del grupo para los encabezados de columna
    grupos = sorted({g for cats in cruzado.values() for g in cats.keys()})

    # Ordenar filas de mayor a menor total
    filas = []
    for cat_x, desglose in sorted(
        cruzado.items(), key=lambda kv: -sum(kv[1].values())
    ):
        filas.append({
            'etiqueta': cat_x,
            'valores':  [desglose.get(g, 0) for g in grupos],
            'total':    sum(desglose.values()),
        })

    return grupos, filas


# ─── Gráfica de barras agrupadas (RF-23) ─────────────────────────────────────

def grafica_barras_agrupadas(cruzado, titulo_x, titulo_grupo, titulo='', max_cats=10):
    """
    Genera barras agrupadas para cruzar dos variables (RF-23).

    - Eje X: categorías de variable_x (las N más frecuentes).
    - Grupos de barras por colores: categorías de variable_grupo.

    Ejemplo: circunstancia × sexo → barras de hombres/mujeres por circunstancia.
    """
    import numpy as np

    if not cruzado:
        return None

    # Recopilar grupos (colores) y categorías del eje X
    grupos = sorted({g for cats in cruzado.values() for g in cats.keys()})
    # Tomar las max_cats categorías del eje X con más casos totales
    cats_x = sorted(
        cruzado.keys(),
        key=lambda k: -sum(cruzado[k].values())
    )[:max_cats]

    n_cats  = len(cats_x)
    n_grups = len(grupos)
    if n_cats == 0 or n_grups == 0:
        return None

    ancho_barra = 0.75 / n_grups   # todas las barras de un grupo caben en 0.75
    x = np.arange(n_cats)

    fig, ax = plt.subplots(figsize=(max(9, n_cats * 0.9), 5))

    for i, grupo in enumerate(grupos):
        valores = [cruzado[cat].get(grupo, 0) for cat in cats_x]
        offset  = (i - n_grups / 2 + 0.5) * ancho_barra
        ax.bar(x + offset, valores, ancho_barra * 0.92,
               label=_truncar(grupo, 20),
               color=COLORES[i % len(COLORES)],
               edgecolor='white')

    etiquetas_x = [_truncar(k, 18) for k in cats_x]
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas_x, rotation=35, ha='right', fontsize=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_title(titulo or f'{titulo_x} por {titulo_grupo}',
                 pad=12, fontweight='bold')
    ax.set_ylabel('Número de casos')
    ax.legend(
        title=titulo_grupo,
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        fontsize=8,
        title_fontsize=8,
    )
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()

    return _fig_a_base64(fig)


def grafica_barras_agrupadas_bytes(cruzado, titulo_x, titulo_grupo,
                                   titulo='', max_cats=10, formato='png'):
    """Igual que grafica_barras_agrupadas pero devuelve bytes PNG para descarga."""
    import numpy as np

    if not cruzado:
        return None

    grupos = sorted({g for cats in cruzado.values() for g in cats.keys()})
    cats_x = sorted(cruzado.keys(), key=lambda k: -sum(cruzado[k].values()))[:max_cats]
    n_cats  = len(cats_x)
    n_grups = len(grupos)
    if n_cats == 0 or n_grups == 0:
        return None

    ancho_barra = 0.75 / n_grups
    x = np.arange(n_cats)

    fig, ax = plt.subplots(figsize=(max(9, n_cats * 0.9), 5))
    for i, grupo in enumerate(grupos):
        valores = [cruzado[cat].get(grupo, 0) for cat in cats_x]
        offset  = (i - n_grups / 2 + 0.5) * ancho_barra
        ax.bar(x + offset, valores, ancho_barra * 0.92,
               label=_truncar(grupo, 20),
               color=COLORES[i % len(COLORES)],
               edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels([_truncar(k, 18) for k in cats_x],
                       rotation=35, ha='right', fontsize=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_title(titulo or f'{titulo_x} por {titulo_grupo}', pad=12, fontweight='bold')
    ax.set_ylabel('Número de casos')
    ax.legend(title=titulo_grupo, bbox_to_anchor=(1.02, 1), loc='upper left',
              fontsize=8, title_fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return _fig_a_bytes(fig, formato=formato)


def grafica_linea_temporal_bytes(qs, titulo='Casos por mes', formato='png'):
    from django.db.models import Count
    from django.db.models.functions import TruncMonth
    datos = (
        qs.exclude(fecha_hora_consulta__isnull=True)
        .annotate(mes=TruncMonth('fecha_hora_consulta'))
        .values('mes').annotate(total=Count('id')).order_by('mes')
    )
    if not datos:
        return None
    meses   = [d['mes'] for d in datos]
    totales = [d['total'] for d in datos]
    etiquetas = [m.strftime('%b %Y') for m in meses]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(range(len(meses)), totales, color=COLORES[0],
            linewidth=2, marker='o', markersize=5)
    ax.fill_between(range(len(meses)), totales, alpha=0.15, color=COLORES[0])
    ax.set_xticks(range(len(meses)))
    ax.set_xticklabels(etiquetas, rotation=45, ha='right', fontsize=8)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_title(titulo, pad=12, fontweight='bold')
    ax.set_ylabel('Número de casos')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    fig.tight_layout()
    return _fig_a_bytes(fig, formato=formato)
