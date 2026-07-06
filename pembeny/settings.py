# pembeny/settings.py - PEMBENY B2B Platform

import os
from pathlib import Path
import dj_database_url

def _env_bool(key, default=False):
    value = os.environ.get(key)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')

CLOUD_ENV_KEYS = ('RAILWAY_ENVIRONMENT', 'RAILWAY_PROJECT_ID', 'RENDER')
IS_CLOUD_ENV = any(os.environ.get(k) for k in CLOUD_ENV_KEYS)

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    ENV_DIR = Path(__file__).resolve().parent.parent  # Project root
    load_dotenv(ENV_DIR / '.env', override=not IS_CLOUD_ENV)
except ImportError:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = _env_bool('DEBUG', False)

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver,.railway.app,.up.railway.app,.onrender.com').split(',')
PUBLIC_APP_URL = os.environ.get('PUBLIC_APP_URL', '').strip().rstrip('/')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # PEMBENY B2B Platform Apps
    'accounts',      # Authentification OTP, profils boutiques
    'products',      # Produits et catégories
    'purchases',     # Achats / réapprovisionnement stock
    'inventory',     # Gestion de stock dynamique
    'supply',        # ⭐ PLATEFORME PEMBENY B2B (coeur)
    'promotions',    # Promotions B2B
    'reports',       # Rapports et analyses
    
    # Cloudinary pour médias
    'cloudinary_storage',
    'cloudinary',
]

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

ROOT_URLCONF = 'pembeny.urls'

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
                'supply.context_processors.supply_site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'pembeny.wsgi.application'


# Database configuration
database_url = os.environ.get("DATABASE_URL") or os.environ.get("INTERNAL_DATABASE_URL")

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    print(f"[DB] Found DATABASE_URL: {database_url[:20]}...")
    
    DATABASES = {
        "default": dj_database_url.parse(
            database_url,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})['sslmode'] = 'require'
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print("WARNING: DATABASE_URL not found! Falling back to SQLite.")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (uploads utilisateurs - images produits)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STATICFILES_BACKEND = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
    if (not DEBUG and IS_CLOUD_ENV)
    else "django.contrib.staticfiles.storage.StaticFilesStorage"
)

# Cloudinary Storage Configuration
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

if CLOUDINARY_URL and CLOUDINARY_URL.startswith('cloudinary://'):
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": STATICFILES_BACKEND,
        },
    }
    if not DEBUG:
        print("[STORAGE] Using Cloudinary for Media files")
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": STATICFILES_BACKEND,
        },
    }
    if not DEBUG:
        print("[STORAGE] WARNING: CLOUDINARY_URL is missing or invalid.")

SERVE_MEDIA_LOCALLY = (
    STORAGES["default"]["BACKEND"] == "django.core.files.storage.FileSystemStorage"
    and not IS_CLOUD_ENV
)


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'supply:dashboard'
LOGOUT_REDIRECT_URL = 'accounts:login'

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# OTP / Email authentication
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@pembeny.com')
OTP_CODE_EXPIRATION_MINUTES = int(os.environ.get('OTP_CODE_EXPIRATION_MINUTES', '10'))
OTP_CODE_RESEND_COOLDOWN_SECONDS = int(os.environ.get('OTP_CODE_RESEND_COOLDOWN_SECONDS', '60'))
OTP_CODE_MAX_ATTEMPTS = int(os.environ.get('OTP_CODE_MAX_ATTEMPTS', '5'))

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'ebenndombi99@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'kree pfxs hayb hdtj')
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', True)
EMAIL_USE_SSL = _env_bool('EMAIL_USE_SSL', False)

# Currency settings
CURRENCIES = {
    'CDF': {'symbol': 'FC', 'name': 'Franc Congolais', 'code': 'CDF'},
    'USD': {'symbol': '$', 'name': 'Dollar Américain', 'code': 'USD'},
}
DEFAULT_CURRENCY = 'CDF'

SECURE_SSL_REDIRECT = _env_bool('SECURE_SSL_REDIRECT', (not DEBUG and IS_CLOUD_ENV))
SESSION_COOKIE_SECURE = _env_bool('SESSION_COOKIE_SECURE', (not DEBUG and IS_CLOUD_ENV))
CSRF_COOKIE_SECURE = _env_bool('CSRF_COOKIE_SECURE', (not DEBUG and IS_CLOUD_ENV))

if IS_CLOUD_ENV:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False

X_FRAME_OPTIONS = 'SAMEORIGIN'

# CSRF Trusted Origins for Railway
CSRF_TRUSTED_ORIGINS = os.environ.get(
    'CSRF_TRUSTED_ORIGINS', 
    'https://*.railway.app,https://*.up.railway.app,https://*.onrender.com'
).split(',')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}