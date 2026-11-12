import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-cambia-esta-clave-en-produccion-haze-studios')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['hstudios.pythonanywhere.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dashboard.apps.DashboardConfig',
    'tienda',
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

ROOT_URLCONF = 'haze_studios.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'dashboard' / 'templates',
            BASE_DIR / 'tienda' / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'dashboard.context_processors.user_es_admin',
                'tienda.context_processors.tienda_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'haze_studios.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
 

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/' 
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

try:
    from decouple import config
except ImportError:
    _env_dict = {}
    _env_file = BASE_DIR / '.env'
    if _env_file.exists():
        try:
            with open(_env_file, 'r', encoding='utf-8') as _f:
                for _line in _f:
                    _line = _line.strip()
                    if _line and not _line.startswith('#') and '=' in _line:
                        _k, _v = _line.split('=', 1)
                        _env_dict[_k.strip()] = _v.strip().strip("'\"")
        except Exception:
            pass

    def config(key, default=''):
        return _env_dict.get(key, os.environ.get(key, default))

EXCHANGE_RATE_API_KEY = config('EXCHANGE_RATE_API_KEY', default=os.environ.get('EXCHANGE_RATE_API_KEY', ''))

_email_user = config('EMAIL_HOST_USER', default=os.environ.get('EMAIL_HOST_USER', ''))
_email_pass = config('EMAIL_HOST_PASSWORD', default=os.environ.get('EMAIL_HOST_PASSWORD', ''))

if _email_user and _email_pass:
    # Producción: enviar correos reales por Gmail SMTP
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = 'smtp.gmail.com'
    EMAIL_PORT          = 587
    EMAIL_USE_TLS       = True
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = _email_pass
    DEFAULT_FROM_EMAIL  = f'Haze Studios <{_email_user}>'
    EMAIL_TIMEOUT       = 10  # evita que el sitio se congele si Gmail no responde
else:
    # Local / sin credenciales: imprimir en consola (sin riesgo de error 500)
    EMAIL_BACKEND      = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'Haze Studios <noreply@hazestudios.com>'

# PayPal
PAYPAL_CLIENT_ID = config('PAYPAL_CLIENT_ID', default=os.environ.get('PAYPAL_CLIENT_ID', ''))
PAYPAL_SECRET = config('PAYPAL_SECRET', default=os.environ.get('PAYPAL_SECRET', ''))
PAYPAL_MODE = str(config('PAYPAL_MODE', default=os.environ.get('PAYPAL_MODE', 'sandbox'))).lower()
