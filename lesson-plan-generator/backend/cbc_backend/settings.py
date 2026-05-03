# File: /lesson-plan-generator/backend/cbc_backend/settings.py

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
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'lesson-plan-generator-va4h.onrender.com']

# Fix session/cookie trust on Render.com (HTTPS proxy)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE   = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE      = not DEBUG
SESSION_ENGINE          = 'django.contrib.sessions.backends.db'


# ---------------------------
# CLOUDINARY — master switch
# ---------------------------
# How this works:
#   dev  (.env.local has USE_CLOUDINARY=False or key missing)
#        → USE_CLOUDINARY = False
#        → ImageField saves files to MEDIA_ROOT on local disk
#        → cloudinary_storage NOT added to INSTALLED_APPS
#        → DEFAULT_FILE_STORAGE stays as Django default
#        → no Cloudinary credentials needed at all
#
#   prod (Render env var USE_CLOUDINARY=True + credentials set)
#        → USE_CLOUDINARY = True
#        → CloudinaryField uploads to Cloudinary via API
#        → cloudinary_storage added to INSTALLED_APPS
#        → DEFAULT_FILE_STORAGE = MediaCloudinaryStorage
#
# Your .env.local for dev:         USE_CLOUDINARY=False  (or just omit it)
# Render environment variables:    USE_CLOUDINARY=True
#                                  CLOUDINARY_CLOUD_NAME=xxx
#                                  CLOUDINARY_API_KEY=xxx
#                                  CLOUDINARY_API_SECRET=xxx
# ---------------------------
USE_CLOUDINARY = os.getenv('USE_CLOUDINARY', 'False') == 'True'


# ---------------------------
# APPLICATIONS
# ---------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
]

# cloudinary_storage MUST come before django.contrib.staticfiles
# and ONLY when Cloudinary is active — adding it without credentials
# causes an import error on startup in dev.
if USE_CLOUDINARY:
    INSTALLED_APPS += [
        'cloudinary_storage',
        'django.contrib.staticfiles',
        'cloudinary',
    ]
else:
    INSTALLED_APPS += [
        'django.contrib.staticfiles',
    ]

INSTALLED_APPS += [
    'rest_framework',
    'lessons',
    'corsheaders',
]


# ---------------------------
# MIDDLEWARE
# ---------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True   # tighten in production if needed
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
# DATABASE
# ---------------------------
# How this works:
#   dev  (.env.local has USE_SUPABASE=False or key missing)
#        → SQLite on local disk — no network, no timeout errors
#
#   prod (Render env var USE_SUPABASE=True + URL set)
#        → PostgreSQL via Supabase pooler
#
# Your .env.local for dev: USE_SUPABASE=False  (or just omit it)
# Render environment variables: USE_SUPABASE=True
#                               SUPABASE_DATABASE_URL=postgresql://...
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
    # ✅ Dev: SQLite — zero config, works offline, no timeout errors
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
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------
# INTERNATIONALIZATION
# ---------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True


# ---------------------------
# STATIC FILES
# ---------------------------
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = os.path.join(BASE_DIR, 'staticfiles')

if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ---------------------------
# MEDIA FILES
# ---------------------------
# dev  (USE_CLOUDINARY=False):
#      Files saved to MEDIA_ROOT/  on local disk.
#      Django serves them via MEDIA_URL in development.
#      No Cloudinary account or credentials needed.
#
# prod (USE_CLOUDINARY=True):
#      Files uploaded to Cloudinary automatically.
#      {{ obj.image.url }} returns Cloudinary CDN URL.
#      MEDIA_ROOT is unused but kept so nothing breaks.
# ---------------------------
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

if USE_CLOUDINARY:
    # ── Cloudinary credentials (Render env vars only) ──────────────────────
    # Setup steps:
    #   1. https://cloudinary.com → free account → Dashboard
    #   2. Copy Cloud Name, API Key, API Secret
    #   3. Add to Render environment variables:
    #        USE_CLOUDINARY=True
    #        CLOUDINARY_CLOUD_NAME=your_cloud_name
    #        CLOUDINARY_API_KEY=your_api_key
    #        CLOUDINARY_API_SECRET=your_api_secret
    # ────────────────────────────────────────────────────────────────────────
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
        'API_KEY':    os.getenv('CLOUDINARY_API_KEY'),
        'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
    }
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    # ── expose USE_CLOUDINARY to models.py via settings ────────────────────
    # models.py reads:  USE_CLOUDINARY = getattr(settings, 'USE_CLOUDINARY', False)
    # This is the single source of truth. No duplication needed.

# If USE_CLOUDINARY is False, DEFAULT_FILE_STORAGE stays as Django's default:
#   django.core.files.storage.FileSystemStorage  → local disk


# ---------------------------
# EMAIL — Gmail SMTP
# ---------------------------
# Setup steps:
#   1. Google Account → Security → 2-Step Verification → enable
#   2. https://myaccount.google.com/apppasswords → create App Password for "Mail"
#   3. Add to .env.local / Render env vars:
#        EMAIL_HOST_USER=yourgmail@gmail.com
#        EMAIL_HOST_PASSWORD=xxxx xxxx xxxx xxxx   (16-char app password)
#        ADMIN_EMAIL=yourgmail@gmail.com
# ---------------------------
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = os.getenv('EMAIL_HOST_USER')


# ---------------------------
# TELEGRAM BOT
# ---------------------------
# Setup steps:
#   1. Telegram → @BotFather → /newbot → copy TOKEN
#   2. Create admin group → add bot → send any message
#   3. Visit https://api.telegram.org/bot<TOKEN>/getUpdates
#      Find "chat" → "id"  (negative number e.g. -1001234567890)
#   4. Add to .env.local / Render env vars:
#        TELEGRAM_BOT_TOKEN=7xxxxxxxxx:AAxxxxxxx...
#        TELEGRAM_CHAT_ID=-1001234567890
# ---------------------------
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID   = os.getenv('TELEGRAM_CHAT_ID')


# ---------------------------
# SITE URL (used in Telegram/email admin links)
# ---------------------------
SITE_URL = os.getenv('SITE_URL', 'https://lesson-plan-generator-va4h.onrender.com')


# ---------------------------
# PWA / SERVICE WORKER
# ---------------------------
PWA_APP_NAME            = os.getenv('PWA_APP_NAME', 'CBC Lesson Generator')
PWA_APP_DESCRIPTION     = os.getenv('PWA_APP_DESCRIPTION', 'Offline-enabled lesson plan app')
PWA_SERVICE_WORKER_PATH = '/sw.js'


# ---------------------------
# DJANGO REST FRAMEWORK
# ---------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}