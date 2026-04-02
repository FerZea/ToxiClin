"""
Configuración de Django para el proyecto ToxiClin.
Sistema de Gestión de Expedientes Clínicos Toxicológicos — CIAT
Hospital Central "Dr. Ignacio Morones Prieto", San Luis Potosí, México.
"""

from pathlib import Path

# Directorio raíz del proyecto (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta — NO compartir ni subir a repositorios públicos
SECRET_KEY = 'django-insecure-85z%8xdv6+a!(2g7h!fuve0bi-l9hnzzp%l5*-(g8rom01o!93'

# Modo debug activo para desarrollo local
DEBUG = True

# Solo se permite acceso desde la misma máquina (localhost)
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# --- Aplicaciones instaladas ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'expedientes',   # nuestra app principal
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'toxiclin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Django buscará templates dentro de cada app en su carpeta templates/
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'toxiclin.wsgi.application'


# --- Base de datos: SQLite (un solo archivo, sin instalar nada extra) ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- Validación de contraseñas ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- Internacionalización y zona horaria ---
LANGUAGE_CODE = 'es-mx'          # Interfaz de Django en español mexicano
TIME_ZONE = 'America/Mexico_City' # Zona horaria de San Luis Potosí
USE_I18N = True                   # Activar traducciones
USE_TZ = True                     # Usar timestamps con zona horaria


# --- Archivos estáticos (CSS, JS, imágenes) ---
# STATIC_URL: prefijo de URL para servir archivos estáticos
STATIC_URL = '/static/'
# STATICFILES_DIRS: carpetas adicionales donde Django busca archivos estáticos
# (además de cada app/static/)
STATICFILES_DIRS = []

# --- Archivos de media (gráficas exportadas) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- Tipo de clave primaria por defecto ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Ruta de login (para el decorador @login_required) ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
