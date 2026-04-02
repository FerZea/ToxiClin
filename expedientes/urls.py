from django.urls import path
from expedientes.views.auth import vista_login, vista_logout
from expedientes.views.inicio import dashboard

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', vista_login, name='login'),
    path('logout/', vista_logout, name='logout'),
]
