from django.urls import path
from expedientes.views.auth import vista_login, vista_logout
from expedientes.views.inicio import dashboard
from expedientes.views.admin_custom import (
    lista_usuarios, crear_usuario, editar_usuario, cambiar_contrasena
)

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
]
