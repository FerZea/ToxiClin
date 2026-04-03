"""
Vistas de administración: gestión de usuarios, respaldos y bitácora.
Solo accesibles para el grupo Administrador y superusuarios.
"""

import os
import base64
import shutil
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib import messages
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from expedientes.decoradores import login_requerido, solo_admin
from expedientes.models import ConfigSistema, RegistroActividad


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
        # is_staff=False para todos — el admin de Django es solo para el superusuario técnico

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
        # is_staff siempre False — admin Django solo para superusuario

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


# ─── Helpers de cifrado ───────────────────────────────────────────────────────

def _derivar_clave(password: str, salt: bytes) -> bytes:
    """
    Deriva una clave Fernet de 32 bytes a partir de una contraseña y un salt
    usando PBKDF2-HMAC-SHA256 con 480,000 iteraciones (recomendado NIST 2023).
    Devuelve la clave en base64-url para que Fernet la acepte.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


# ─── Respaldos ────────────────────────────────────────────────────────────────

@login_requerido
@solo_admin
def respaldos(request):
    """
    Página de gestión de respaldos.
    Lista los archivos .toxiclin existentes en la carpeta backups/.
    """
    backups_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backups_dir, exist_ok=True)

    archivos = []
    for nombre in sorted(os.listdir(backups_dir), reverse=True):
        if nombre.endswith('.toxiclin'):
            ruta = os.path.join(backups_dir, nombre)
            archivos.append({
                'nombre': nombre,
                'tamano_kb': round(os.path.getsize(ruta) / 1024, 1),
                'fecha': datetime.fromtimestamp(os.path.getmtime(ruta)),
            })

    # Fecha del último respaldo (guardada en ConfigSistema)
    ultimo_respaldo_str = ConfigSistema.get('ultimo_respaldo')
    ultimo_respaldo = None
    if ultimo_respaldo_str:
        try:
            ultimo_respaldo = datetime.fromisoformat(ultimo_respaldo_str)
        except ValueError:
            pass

    return render(request, 'expedientes/admin/respaldos.html', {
        'archivos': archivos,
        'ultimo_respaldo': ultimo_respaldo,
    })


@login_requerido
@solo_admin
def crear_respaldo(request):
    """
    RF-32: Genera un respaldo cifrado de la base de datos y lo descarga.

    Proceso:
    1. Verifica la contraseña del admin.
    2. Lee el archivo db.sqlite3 completo.
    3. Genera un salt aleatorio de 16 bytes.
    4. Deriva una clave Fernet a partir de la contraseña + salt (PBKDF2-SHA256).
    5. Cifra los datos con Fernet (AES-128-CBC + HMAC-SHA256).
    6. Escribe: [16 bytes de salt] + [datos cifrados] en un archivo .toxiclin.
    7. Guarda una copia en backups/ y envía la descarga al navegador.
    """
    if request.method != 'POST':
        return redirect('respaldos')

    password = request.POST.get('password', '')
    if not request.user.check_password(password):
        messages.error(request, 'Contraseña incorrecta. No se generó el respaldo.')
        return redirect('respaldos')

    # Leer la base de datos completa
    db_path = settings.DATABASES['default']['NAME']
    try:
        with open(db_path, 'rb') as f:
            datos_db = f.read()
    except OSError as e:
        messages.error(request, f'No se pudo leer la base de datos: {e}')
        return redirect('respaldos')

    # Cifrar
    salt = os.urandom(16)
    clave = _derivar_clave(password, salt)
    fernet = Fernet(clave)
    datos_cifrados = fernet.encrypt(datos_db)

    # Formato del archivo: [salt 16 bytes][datos cifrados]
    contenido = salt + datos_cifrados

    # Nombre y guardado local
    fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f'respaldo_CIAT_{fecha_str}.toxiclin'
    backups_dir = os.path.join(settings.BASE_DIR, 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    with open(os.path.join(backups_dir, nombre_archivo), 'wb') as f:
        f.write(contenido)

    # Registrar en bitácora y actualizar fecha de último respaldo
    RegistroActividad.objects.create(
        usuario=request.user,
        accion='respaldo',
        descripcion=f'Respaldo generado: {nombre_archivo}',
        ip=request.META.get('REMOTE_ADDR'),
    )
    ConfigSistema.set('ultimo_respaldo', datetime.now().isoformat())

    # Enviar como descarga
    response = HttpResponse(contenido, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
    return response


@login_requerido
@solo_admin
def restaurar_respaldo(request):
    """
    RF-32: Restaura la base de datos desde un archivo .toxiclin cifrado.

    Proceso:
    1. Recibe el archivo y la contraseña via POST.
    2. Verifica la contraseña del admin.
    3. Extrae el salt (primeros 16 bytes) y los datos cifrados.
    4. Deriva la clave y descifra con Fernet.
    5. Hace copia de seguridad del db.sqlite3 actual (→ .pre_restore).
    6. Reemplaza db.sqlite3 con los datos descifrados.
    7. Avisa que hay que reiniciar el servidor.
    """
    if request.method != 'POST':
        return redirect('respaldos')

    archivo = request.FILES.get('archivo')
    password = request.POST.get('password', '')

    if not archivo:
        messages.error(request, 'Debes seleccionar un archivo de respaldo (.toxiclin).')
        return redirect('respaldos')

    if not request.user.check_password(password):
        messages.error(request, 'Contraseña incorrecta.')
        return redirect('respaldos')

    contenido = archivo.read()

    # El archivo debe tener al menos el salt (16 bytes) + algo de datos cifrados
    if len(contenido) < 100:
        messages.error(request, 'El archivo no parece un respaldo válido.')
        return redirect('respaldos')

    salt = contenido[:16]
    datos_cifrados = contenido[16:]

    # Descifrar
    clave = _derivar_clave(password, salt)
    fernet = Fernet(clave)
    try:
        datos_db = fernet.decrypt(datos_cifrados)
    except InvalidToken:
        messages.error(
            request,
            'No se pudo descifrar el archivo. '
            'Verifica que la contraseña sea correcta y que el archivo no esté dañado.'
        )
        return redirect('respaldos')

    # Hacer copia de seguridad del db actual antes de reemplazar
    db_path = settings.DATABASES['default']['NAME']
    shutil.copy2(db_path, str(db_path) + '.pre_restore')

    # Reemplazar la base de datos
    with open(db_path, 'wb') as f:
        f.write(datos_db)

    # Registrar en la bitácora (ya con la BD restaurada activa)
    try:
        RegistroActividad.objects.create(
            usuario=request.user,
            accion='restauracion',
            descripcion=f'Base de datos restaurada desde {archivo.name}',
            ip=request.META.get('REMOTE_ADDR'),
        )
    except Exception:
        pass  # Si la BD restaurada tiene estructura diferente, no interrumpir

    messages.success(
        request,
        '✓ Base de datos restaurada. '
        'IMPORTANTE: detén y vuelve a iniciar el servidor '
        '(Ctrl+C → python manage.py runserver) para que los cambios surtan efecto.'
    )
    return redirect('respaldos')


# ─── Importación Excel (stub Fase 6) ─────────────────────────────────────────

@login_requerido
@solo_admin
def importar_excel(request):
    """
    RF-28/RF-29: Stub para la importación desde Excel.
    La funcionalidad real se implementará cuando se disponga del archivo Excel del CIAT.
    """
    return render(request, 'expedientes/admin/importar_excel.html')


# ─── Bitácora de actividad ────────────────────────────────────────────────────

@login_requerido
@solo_admin
def actividad(request):
    """
    RF-35: Muestra el registro de actividad de los últimos 500 eventos.
    Solo accesible para administradoras.
    """
    registros = RegistroActividad.objects.select_related('usuario').all()[:500]
    return render(request, 'expedientes/admin/actividad.html', {
        'registros': registros,
    })
