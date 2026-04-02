"""
Comando: crear_grupos
Uso: python manage.py crear_grupos

Crea los dos grupos de usuarios del sistema:
  - Administrador: acceso total (Dra. Evelyn, Dra. Susana)
  - Capturista:    solo captura de historias clínicas (alumnos rotantes)

Es seguro ejecutarlo varias veces — usa get_or_create.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Crea los grupos de usuarios: Administrador y Capturista'

    def handle(self, *args, **options):
        admin_grupo, creado = Group.objects.get_or_create(name='Administrador')
        if creado:
            self.stdout.write(self.style.SUCCESS('  Grupo "Administrador" creado'))
        else:
            self.stdout.write('  Grupo "Administrador" ya existía')

        cap_grupo, creado = Group.objects.get_or_create(name='Capturista')
        if creado:
            self.stdout.write(self.style.SUCCESS('  Grupo "Capturista" creado'))
        else:
            self.stdout.write('  Grupo "Capturista" ya existía')

        self.stdout.write(self.style.SUCCESS('\n¡Grupos creados correctamente!'))
