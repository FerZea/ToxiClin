"""
Vistas de administración: gestión de usuarios.
Solo accesibles para el grupo Administrador y superusuarios.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from expedientes.decoradores import login_requerido, solo_admin


@login_requerido
@solo_admin
def lista_usuarios(request):
    """Muestra todos los usuarios del sistema con su rol y estado."""
    usuarios = User.objects.all().order_by('username').prefetch_related('groups')
    return render(request, 'expedientes/admin/usuarios.html', {
        'usuarios': usuarios,
    })


@login_requerido
@solo_admin
def crear_usuario(request):
    """Formulario para crear un nuevo usuario (admin o capturista)."""
    grupos = Group.objects.all()

    if request.method == 'POST':
        username    = request.POST.get('username', '').strip()
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        password1   = request.POST.get('password1', '')
        password2   = request.POST.get('password2', '')
        grupo_id    = request.POST.get('grupo')

        # Validaciones básicas
        errores = []
        if not username:
            errores.append('El nombre de usuario es obligatorio.')
        if User.objects.filter(username=username).exists():
            errores.append(f'El usuario "{username}" ya existe.')
        if not password1:
            errores.append('La contraseña es obligatoria.')
        if password1 != password2:
            errores.append('Las contraseñas no coinciden.')
        if len(password1) < 8:
            errores.append('La contraseña debe tener al menos 8 caracteres.')
        if not grupo_id:
            errores.append('Debes seleccionar un rol.')

        if errores:
            for error in errores:
                messages.error(request, error)
            return render(request, 'expedientes/admin/crear_usuario.html', {
                'grupos': grupos,
                'valores': request.POST,  # Para repoblar el formulario
            })

        # Crear el usuario
        user = User.objects.create_user(
            username=username,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        grupo = Group.objects.get(pk=grupo_id)
        user.groups.add(grupo)

        # Si es Administrador, darle acceso al admin de Django también
        if grupo.name == 'Administrador':
            user.is_staff = True
            user.save()

        messages.success(request, f'Usuario "{username}" creado correctamente con rol {grupo.name}.')
        return redirect('lista_usuarios')

    return render(request, 'expedientes/admin/crear_usuario.html', {
        'grupos': grupos,
    })


@login_requerido
@solo_admin
def editar_usuario(request, user_id):
    """Permite cambiar el rol y estado activo de un usuario."""
    usuario = get_object_or_404(User, pk=user_id)
    grupos  = Group.objects.all()

    # No permitir editar el propio superusuario desde aquí
    if usuario.is_superuser:
        messages.warning(request, 'El superusuario se gestiona desde el admin de Django.')
        return redirect('lista_usuarios')

    if request.method == 'POST':
        grupo_id = request.POST.get('grupo')
        activo   = request.POST.get('activo') == 'on'

        usuario.groups.clear()
        if grupo_id:
            grupo = Group.objects.get(pk=grupo_id)
            usuario.groups.add(grupo)
            usuario.is_staff = (grupo.name == 'Administrador')

        usuario.is_active = activo
        usuario.save()

        messages.success(request, f'Usuario "{usuario.username}" actualizado.')
        return redirect('lista_usuarios')

    grupo_actual = usuario.groups.first()
    return render(request, 'expedientes/admin/editar_usuario.html', {
        'usuario': usuario,
        'grupos': grupos,
        'grupo_actual': grupo_actual,
    })


@login_requerido
@solo_admin
def cambiar_contrasena(request, user_id):
    """Permite al admin cambiar la contraseña de cualquier usuario."""
    usuario = get_object_or_404(User, pk=user_id)

    if usuario.is_superuser:
        messages.warning(request, 'El superusuario se gestiona desde el admin de Django.')
        return redirect('lista_usuarios')

    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not password1:
            messages.error(request, 'La contraseña no puede estar vacía.')
        elif password1 != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
        elif len(password1) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres.')
        else:
            usuario.set_password(password1)
            usuario.save()
            messages.success(request, f'Contraseña de "{usuario.username}" actualizada.')
            return redirect('lista_usuarios')

    return render(request, 'expedientes/admin/cambiar_contrasena.html', {
        'usuario': usuario,
    })
