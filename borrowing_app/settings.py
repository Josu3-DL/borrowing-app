"""
Django settings for borrowing_app project.
"""

<<<<<<< Updated upstream
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ng5cquw!%&9io&%m_0e%th)fx^bu^2gq6^k3v!sf_a%pn_k)5b'

DEBUG = True

ALLOWED_HOSTS = []

=======
import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-ng5cquw!%&9io&%m_0e%th)fx^bu^2gq6^k3v!sf_a%pn_k)5b',
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
    'whitenoise.middleware.WhiteNoiseMiddleware',  # serve static files in production
>>>>>>> Stashed changes
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
            ],
        },
    },
]

WSGI_APPLICATION = 'borrowing_app.wsgi.application'

<<<<<<< Updated upstream
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

=======
# ---------------------------------------------------------------------------
# Database
# Uses DATABASE_URL env var on Render (PostgreSQL).
# Falls back to SQLite for local development.
# ---------------------------------------------------------------------------
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
>>>>>>> Stashed changes
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

<<<<<<< Updated upstream
=======
# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
>>>>>>> Stashed changes
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Managua'
USE_I18N = True
USE_TZ = True

<<<<<<< Updated upstream
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

=======
# ---------------------------------------------------------------------------
# Static files (WhiteNoise)
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
>>>>>>> Stashed changes
AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'users:login'
LOGIN_REDIRECT_URL = 'loans:dashboard'
LOGOUT_REDIRECT_URL = 'users:login'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
<<<<<<< Updated upstream
=======

# ---------------------------------------------------------------------------
# Production security hardening (only when DEBUG is off)
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
>>>>>>> Stashed changes
