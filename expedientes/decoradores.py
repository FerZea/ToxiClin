"""
Decoradores de acceso para ToxiClin.

Un decorador es una función que "envuelve" una vista para agregar lógica
antes de ejecutarla. Se usa con @nombre_decorador encima de la función.

Ejemplo:
    @login_required          <- de Django, redirige al login si no hay sesión
    @solo_admin              <- nuestro, redirige si no es administrador
    def mi_vista(request):
        ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def solo_admin(vista):
    """
    Permite acceso solo a usuarios del grupo 'Administrador' o superusuarios.
    Si el usuario es capturista, lo manda al dashboard con un mensaje de error.
    """
    @wraps(vista)  # Preserva el nombre y docstring de la vista original
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser or request.user.groups.filter(name='Administrador').exists():
            return vista(request, *args, **kwargs)
        messages.error(request, 'No tienes permiso para acceder a esa sección.')
        return redirect('dashboard')
    return wrapper


def login_requerido(vista):
    """
    Versión propia de @login_required.
    Redirige al login si el usuario no tiene sesión activa.
    Usamos esta en lugar de la de Django para tener el mensaje en español.
    """
    @wraps(vista)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, 'Debes iniciar sesión para continuar.')
            return redirect('login')
        return vista(request, *args, **kwargs)
    return wrapper
