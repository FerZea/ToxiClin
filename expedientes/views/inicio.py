"""
Vista del dashboard (página de inicio).
RF-27: Muestra resumen real de la base de datos.
"""

from datetime import datetime

from django.shortcuts import render
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db.models import Count

from expedientes.decoradores import login_requerido
from expedientes.models import HistoriaClinica, ConfigSistema
from expedientes.graficas import grafica_linea_temporal

# Días sin respaldar antes de mostrar el recordatorio (RF-33)
DIAS_ALERTA_RESPALDO = 7


@login_requerido
def dashboard(request):
    """
    Página de inicio con resumen estadístico (RF-27).

    Datos que se calculan aquí:
    - Total de registros en la base de datos
    - Cantidad de registros ingresados en el último mes
    - Top 5 agentes tóxicos más frecuentes
    - Top 3 circunstancias más frecuentes
    - Gráfica de línea con tendencia mensual del año actual
    """
    hoy = timezone.now().date()
    inicio_mes = hoy - relativedelta(months=1)
    inicio_anio = hoy.replace(month=1, day=1)

    # Total de historias en la BD
    total = HistoriaClinica.objects.count()

    # Registros del último mes
    este_mes = HistoriaClinica.objects.filter(
        fecha_hora_consulta__date__gte=inicio_mes
    ).count()

    # Top 5 agentes tóxicos (excluye nulos)
    top_agentes = (
        HistoriaClinica.objects
        .exclude(tipo_agente__isnull=True)
        .values('tipo_agente__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    # Top 3 circunstancias nivel 1 (excluye nulos)
    top_circunstancias = (
        HistoriaClinica.objects
        .exclude(circunstancia_nivel1__isnull=True)
        .values('circunstancia_nivel1__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')[:3]
    )

    # Gráfica de tendencia mensual del año actual
    qs_anio = HistoriaClinica.objects.filter(
        fecha_hora_consulta__date__gte=inicio_anio
    )
    grafica_tendencia = grafica_linea_temporal(qs_anio, titulo='Casos por mes (año actual)')

    # RF-33: recordatorio de respaldo para administradoras
    alerta_respaldo = False
    es_admin = request.user.is_superuser or \
               request.user.groups.filter(name='Administrador').exists()
    if es_admin:
        ultimo_str = ConfigSistema.get('ultimo_respaldo')
        if ultimo_str is None:
            alerta_respaldo = True  # nunca se ha hecho un respaldo
        else:
            try:
                ultimo = datetime.fromisoformat(ultimo_str)
                dias_sin_respaldo = (datetime.now() - ultimo).days
                alerta_respaldo = dias_sin_respaldo >= DIAS_ALERTA_RESPALDO
            except ValueError:
                alerta_respaldo = True

    return render(request, 'expedientes/dashboard.html', {
        'total': total,
        'este_mes': este_mes,
        'top_agentes': top_agentes,
        'top_circunstancias': top_circunstancias,
        'grafica_tendencia': grafica_tendencia,
        'alerta_respaldo': alerta_respaldo,
    })
