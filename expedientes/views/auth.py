from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from expedientes.models import RegistroActividad


def _ip(request):
    """Extrae la IP del cliente desde el request."""
    return request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR'))


def vista_login(request):
    """Muestra el formulario de login y procesa las credenciales."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        usuario = request.POST.get('username')
        contrasena = request.POST.get('password')
        user = authenticate(request, username=usuario, password=contrasena)

        if user is not None:
            login(request, user)
            # RF-35: registrar inicio de sesión en la bitácora
            RegistroActividad.objects.create(
                usuario=user,
                accion='login',
                descripcion=f'Inicio de sesión: {user.username}',
                ip=_ip(request),
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'expedientes/login.html')


def vista_logout(request):
    """Cierra la sesión del usuario."""
    if request.user.is_authenticated:
        # RF-35: registrar cierre de sesión
        RegistroActividad.objects.create(
            usuario=request.user,
            accion='logout',
            descripcion=f'Cierre de sesión: {request.user.username}',
            ip=_ip(request),
        )
    logout(request)
    return redirect('login')
