# redpos/settings.py

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-CHANGE-THIS-IN-PRODUCTION'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


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


# Database - SQLite (pour développement rapide)
# Pour passer à PostgreSQL plus tard, décommente la section ci-dessous

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration PostgreSQL (à utiliser en production)
# IMPORTANT : Créer d'abord la base de données dans PostgreSQL
# Commande SQL : CREATE DATABASE redpos_db;
# 
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'redpos_db',           # Nom de la base
#         'USER': 'postgres',             # Utilisateur PostgreSQL
#         'PASSWORD': 'votre_mot_de_passe',  # À CHANGER
#         'HOST': 'localhost',            # Serveur local
#         'PORT': '5432',                 # Port par défaut PostgreSQL
#     }
# }


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
