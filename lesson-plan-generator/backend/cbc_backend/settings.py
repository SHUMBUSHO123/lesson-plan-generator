from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url



BASE_DIR = Path(__file__).resolve().parent.parent

if os.path.exists(BASE_DIR / '.env.local'):
    load_dotenv(BASE_DIR / '.env.local')
else:
    load_dotenv()


# ---------------------------
# SECURITY
# ---------------------------
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-for-dev')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS')
if ALLOWED_HOSTS:
    ALLOWED_HOSTS = ALLOWED_HOSTS.split(',')
else:
    # fallback if env var is missing
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'lesson-plan-generator-va4h.onrender.com']


# ---------------------------
# APPLICATIONS
# ---------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'lessons',
    'corsheaders',
]

# ---------------------------
# MIDDLEWARE
# ---------------------------
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # for static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True  # for dev only, restrict in production
ROOT_URLCONF = 'cbc_backend.urls'

# ---------------------------
# TEMPLATES
# ---------------------------
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

WSGI_APPLICATION = 'cbc_backend.wsgi.application'

# ---------------------------
# DATABASE CONFIGURATION
# ---------------------------

USE_SUPABASE = os.getenv('USE_SUPABASE', 'False') == 'True'
SUPABASE_DATABASE_URL = os.getenv('SUPABASE_DATABASE_URL')

if USE_SUPABASE and SUPABASE_DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            SUPABASE_DATABASE_URL,
            conn_max_age=600,
            ssl_require=not DEBUG
        )
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# ---------------------------
# PASSWORD VALIDATION
# ---------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ---------------------------
# INTERNATIONALIZATION
# ---------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------
# STATIC FILES
# ---------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # dev
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # for collectstatic

# Use normal static storage in development for instant updates
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    # Production storage with cache-busting
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ---------------------------
# PWA / SERVICE WORKER
# ---------------------------
PWA_APP_NAME = os.getenv('PWA_APP_NAME', 'CBC Lesson Generator')
PWA_APP_DESCRIPTION = os.getenv('PWA_APP_DESCRIPTION', 'Offline-enabled lesson plan app')
PWA_SERVICE_WORKER_PATH = '/sw.js'

# ---------------------------
# DJANGO REST FRAMEWORK
# ---------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}
