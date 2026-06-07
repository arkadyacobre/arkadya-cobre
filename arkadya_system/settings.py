from pathlib import Path
# Configuración para archivos media (imágenes)
import os
import sys
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

IN_PRODUCTION = 'pythonanywhere' in sys.argv[0] or 'pythonanywhere' in sys.path[0] or 'PYTHONANYWHERE_SITE' in os.environ


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if IN_PRODUCTION:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY debe estar configurada en produccion.')
    SECRET_KEY = 'django-insecure-dev-only-change-me'

# SECURITY WARNING: don't run with debug turned on in production!


# Detectar si estamos en PythonAnywhere
if IN_PRODUCTION:
    # Configuración para PythonAnywhere (producción)
    DEBUG = False
    ALLOWED_HOSTS = ['arkadyacobre.pythonanywhere.com']
else:
    # Configuración para tu PC local (desarrollo)
    DEBUG = True
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Nuestras aplicaciones
    'ventas',
    'productos',
    'contabilidad',
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

ROOT_URLCONF = 'arkadya_system.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',  # ← Esta línea es clave
            ],
        },
    },
]

WSGI_APPLICATION = 'arkadya_system.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Token para acceso al formulario móvil de venta rápida
TOKEN_VENTA_RAPIDA = os.environ.get('TOKEN_VENTA_RAPIDA')
if not TOKEN_VENTA_RAPIDA:
    if IN_PRODUCTION:
        raise ImproperlyConfigured('TOKEN_VENTA_RAPIDA debe estar configurado en produccion.')
    TOKEN_VENTA_RAPIDA = 'dev-token-venta-rapida'

