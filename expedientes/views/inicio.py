from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required  # Redirige a /login/ si no hay sesión activa
def dashboard(request):
    """Página de inicio — muestra resumen rápido del sistema."""
    return render(request, 'expedientes/dashboard.html')
