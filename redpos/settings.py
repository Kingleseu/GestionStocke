# redpos/settings.py

import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,gestionstocke.onrender.com,.onrender.com').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Nos applications
    'accounts',
    'products',
    'sales',
    'purchases',
    'inventory',
    'reports',
    'store',  # E-commerce Storefront
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'redpos.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier templates global
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

WSGI_APPLICATION = 'redpos.wsgi.application'



# Database
# Use PostgreSQL in production (Render), SQLite in development
import dj_database_url
import os

DATABASES = {
    "default": dj_database_url.parse(
        os.environ.get(
            "DATABASE_URL",
            "postgresql://redpos_postgres_user:D6RQ1GiQZEqMYWr9pgAPwvQCnsZu3xp5@dpg-d54tjau3jp1c739gf5jg-a/redpos_postgres"
        ),
        conn_max_age=600,
        ssl_require=not os.environ.get("DEBUG", False)
    )
}




    # Development: Local PostgreSQL
""" DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'redpos_db',
            'USER': 'redpos_user',
            'PASSWORD': 'Eben@1999',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }
 """



# Password validation
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
LANGUAGE_CODE = 'fr-fr'  # Français

TIME_ZONE = 'Europe/Paris'  # Fuseau horaire France

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Pour la production

# WhiteNoise configuration for static files in production
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# Media files (uploads utilisateurs - images produits)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model (on le configurera dans accounts plus tard)
# AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'sales:pos'
LOGOUT_REDIRECT_URL = 'accounts:login'

# Currency settings
CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'Dollar Américain', 'code': 'USD'},
    'FC': {'symbol': 'FC', 'name': 'Franc Congolais', 'code': 'FC'},
}
DEFAULT_CURRENCY = 'USD'  # Devise par défaut

# Security settings for production
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # HSTS settings
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# CSRF Trusted Origins for Railway and Render
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 
    'https://*.railway.app,https://*.onrender.com'
).split(',')
