"""
Vistas de consulta: listado y detalle de historias clínicas.
(Fase 4 — por ahora solo el detalle básico para el redirect del formulario)
"""

from django.shortcuts import render, get_object_or_404
from expedientes.decoradores import login_requerido
from expedientes.models import HistoriaClinica


@login_requerido
def detalle_historia(request, pk):
    """Vista de detalle completa de una historia clínica."""
    historia = get_object_or_404(HistoriaClinica, pk=pk)
    tratamientos_a = historia.tratamientos_detalle.filter(columna='A').select_related('tratamiento')
    tratamientos_b = historia.tratamientos_detalle.filter(columna='B').select_related('tratamiento')

    return render(request, 'expedientes/consulta/detalle.html', {
        'historia': historia,
        'tratamientos_a': tratamientos_a,
        'tratamientos_b': tratamientos_b,
    })
