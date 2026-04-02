from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),           # Admin de Django (solo superusuario)
    path('', include('expedientes.urls')),      # Todas las URLs de nuestra app
]

# Servir archivos de media en desarrollo (gráficas exportadas)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
