from django.shortcuts import render
from expedientes.decoradores import login_requerido


@login_requerido
def dashboard(request):
    """Página de inicio — muestra resumen rápido del sistema."""
    return render(request, 'expedientes/dashboard.html')
