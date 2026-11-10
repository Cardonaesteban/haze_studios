import os
from pathlib import Path
import dj_database_url

# 1. Definición de rutas base (Usando pathlib)
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Clave secreta (Toma la variable de entorno en producción o usa la local por defecto)
SECRET_KEY = os.environ.get(
    'SECRET_KEY', 
    'django-insecure-local-dev-key-reemplazar-en-produccion'
)

# 3. Modo depuración (False en producción por seguridad)
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# 4. Hosts permitidos
ALLOWED_HOSTS = ['*']

# 5. Aplicaciones instaladas
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # ⚠️ APLICACIONES LOCALES DEL PROYECTO HAZE STUDIOS
    'dashboard',
    'productos',
    'tienda',
]

# 6. Middleware (WhiteNoise ubicado justo debajo de SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 7. Configuración de URLs y WSGI
ROOT_URLCONF = 'haze_studios.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'haze_studios.wsgi.application'

# 8. Base de datos (PostgreSQL en producción vía DATABASE_URL, SQLite en desarrollo local)
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}

# 9. Validación de contraseñas
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 10. Internacionalización
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# 11. Archivos estáticos (CSS, JavaScript, Imágenes)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

# Compresión y caché optimizada para WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 12. Clave primaria predeterminada
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'