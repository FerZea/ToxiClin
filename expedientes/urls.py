from django.urls import path
from expedientes.views.auth import vista_login, vista_logout
from expedientes.views.inicio import dashboard
from expedientes.views.admin_custom import (
    lista_usuarios, crear_usuario, editar_usuario, cambiar_contrasena,
    respaldos, crear_respaldo, restaurar_respaldo, actividad,
)
from expedientes.views.captura import (
    nueva_historia, editar_historia, circunstancias_nivel2
)
from expedientes.views.consulta import detalle_historia, listado_historias
from expedientes.views.estadisticas import estadisticas, exportar_grafica

urlpatterns = [
    # Dashboard
    path('', dashboard, name='dashboard'),

    # Autenticación
    path('login/', vista_login, name='login'),
    path('logout/', vista_logout, name='logout'),

    # Gestión de usuarios (solo admins)
    path('admin-ciat/usuarios/', lista_usuarios, name='lista_usuarios'),
    path('admin-ciat/usuarios/nuevo/', crear_usuario, name='crear_usuario'),
    path('admin-ciat/usuarios/<int:user_id>/editar/', editar_usuario, name='editar_usuario'),
    path('admin-ciat/usuarios/<int:user_id>/contrasena/', cambiar_contrasena, name='cambiar_contrasena'),

    # Captura de historias clínicas
    path('historias/nueva/', nueva_historia, name='nueva_historia'),
    path('historias/<int:pk>/editar/', editar_historia, name='editar_historia'),

    # Listado y detalle
    path('historias/', listado_historias, name='listado_historias'),
    path('historias/<int:pk>/', detalle_historia, name='detalle_historia'),

    # AJAX: circunstancias nivel 2
    path('ajax/circunstancias-n2/', circunstancias_nivel2, name='circunstancias_nivel2'),

    # Estadísticas y gráficas (RF-22, RF-25, RF-26)
    path('estadisticas/', estadisticas, name='estadisticas'),
    path('estadisticas/exportar/', exportar_grafica, name='exportar_grafica'),

    # Respaldos (RF-32)
    path('admin-ciat/respaldos/', respaldos, name='respaldos'),
    path('admin-ciat/respaldos/crear/', crear_respaldo, name='crear_respaldo'),
    path('admin-ciat/respaldos/restaurar/', restaurar_respaldo, name='restaurar_respaldo'),

    # Bitácora de actividad (RF-35)
    path('admin-ciat/actividad/', actividad, name='actividad'),
]
