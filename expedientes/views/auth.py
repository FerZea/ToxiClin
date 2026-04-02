from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def vista_login(request):
    """Muestra el formulario de login y procesa las credenciales."""
    # Si ya está autenticado, manda directo al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        usuario = request.POST.get('username')
        contrasena = request.POST.get('password')
        user = authenticate(request, username=usuario, password=contrasena)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'expedientes/login.html')


def vista_logout(request):
    """Cierra la sesión del usuario."""
    logout(request)
    return redirect('login')
