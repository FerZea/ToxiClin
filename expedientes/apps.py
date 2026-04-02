from django.apps import AppConfig


class ExpedientesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expedientes'
    verbose_name = 'Expedientes Clínicos'  # Nombre legible en el admin de Django
