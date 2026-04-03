"""
Modelos de administración del sistema:
- ConfigSistema: clave-valor para guardar configuración persistente
  (p. ej. fecha del último respaldo).
- RegistroActividad: bitácora de acciones de los usuarios.
"""

from django.db import models
from django.contrib.auth.models import User


class ConfigSistema(models.Model):
    """
    Tabla de configuración tipo clave-valor (singleton por clave).
    Se usa para guardar cosas como la fecha del último respaldo.

    Ejemplo de uso:
        ConfigSistema.set('ultimo_respaldo', '2026-04-02T10:30:00')
        valor = ConfigSistema.get('ultimo_respaldo')
    """
    clave = models.CharField(max_length=100, unique=True)
    valor = models.TextField()

    class Meta:
        verbose_name = 'Configuración del sistema'
        verbose_name_plural = 'Configuración del sistema'

    def __str__(self):
        return f'{self.clave} = {self.valor}'

    @classmethod
    def get(cls, clave, default=None):
        """Devuelve el valor de la clave, o default si no existe."""
        try:
            return cls.objects.get(clave=clave).valor
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, clave, valor):
        """Crea o actualiza el valor de la clave."""
        cls.objects.update_or_create(clave=clave, defaults={'valor': str(valor)})


class RegistroActividad(models.Model):
    """
    Bitácora de acciones importantes:
    quién hizo qué, cuándo y desde qué IP.

    Se registra automáticamente en: login, nueva historia, edición,
    creación/restauración de respaldos.
    """

    ACCIONES = [
        ('login',        'Inicio de sesión'),
        ('logout',       'Cierre de sesión'),
        ('captura',      'Captura de historia clínica'),
        ('edicion',      'Edición de historia clínica'),
        ('respaldo',     'Generación de respaldo'),
        ('restauracion', 'Restauración de base de datos'),
    ]

    # SET_NULL para no perder el registro si el usuario es eliminado
    usuario     = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='actividades'
    )
    accion      = models.CharField(max_length=20, choices=ACCIONES)
    descripcion = models.TextField(blank=True)
    fecha       = models.DateTimeField(auto_now_add=True)
    # IP del cliente — útil en auditorías
    ip          = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de actividad'
        verbose_name_plural = 'Registro de actividad'

    def __str__(self):
        usuario_str = self.usuario.username if self.usuario else '(eliminado)'
        return f'{self.fecha:%Y-%m-%d %H:%M} — {usuario_str} — {self.get_accion_display()}'
