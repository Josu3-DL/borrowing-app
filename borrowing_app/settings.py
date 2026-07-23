"""
Django settings for borrowing_app project.

Every setting that differs between local development and a real
deployment is read from an environment variable, with a value that keeps
`manage.py runserver` working out of the box for local dev. See the
README for the full list of variables and recommended production values.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default):
    value = os.environ.get(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


DEBUG = _env_bool("DJANGO_DEBUG", True)

# Only used when DJANGO_SECRET_KEY is not set, and only while DEBUG is on:
# a real deployment must always provide its own secret via the environment.
_DEV_ONLY_SECRET_KEY = "django-insecure-ng5cquw!%&9io&%m_0e%th)fx^bu^2gq6^k3v!sf_a%pn_k)5b"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or _DEV_ONLY_SECRET_KEY

if not DEBUG and SECRET_KEY == _DEV_ONLY_SECRET_KEY:
    raise ImproperlyConfigured(
        "Define DJANGO_SECRET_KEY con un valor propio antes de desplegar "
        "con DJANGO_DEBUG=false."
    )

ALLOWED_HOSTS = _env_list(
    "DJANGO_ALLOWED_HOSTS",
    ["localhost", "127.0.0.1"] if DEBUG else [],
)

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',
    'loans.apps.LoansConfig',
    'payments.apps.PaymentsConfig',
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

ROOT_URLCONF = 'borrowing_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'borrowing_app.context_processors.money_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'borrowing_app.wsgi.application'

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
TIME_ZONE = 'America/Managua'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'loans:dashboard'
LOGOUT_REDIRECT_URL = 'users:login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Seguridad de cookies y transporte ---------------------------------
# Por defecto siguen el valor de DEBUG (activas solo cuando DEBUG es
# falso), pero cada una se puede fijar de forma explicita via entorno.
SESSION_COOKIE_SECURE = _env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = _env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_SSL_REDIRECT = _env_bool("DJANGO_SECURE_SSL_REDIRECT", False)

# HSTS queda apagado por defecto: activarlo mal (o con un valor alto antes
# de confirmar que HTTPS funciona en todos los subdominios) puede dejar el
# sitio inaccesible durante el tiempo configurado. Se activa a proposito
# via entorno, nunca automaticamente.
SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = _env_bool("DJANGO_SECURE_HSTS_PRELOAD", False)
