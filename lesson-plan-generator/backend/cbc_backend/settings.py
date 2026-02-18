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

CORS_ALLOW_ALL_ORIGINS = True  # restrict in production
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
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
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
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ---------------------------
# MEDIA FILES (screenshot uploads)
# ---------------------------
MEDIA_URL  = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


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
PWA_APP_NAME         = os.getenv('PWA_APP_NAME', 'CBC Lesson Generator')
PWA_APP_DESCRIPTION  = os.getenv('PWA_APP_DESCRIPTION', 'Offline-enabled lesson plan app')
PWA_SERVICE_WORKER_PATH = '/sw.js'


# ---------------------------
# DJANGO REST FRAMEWORK
# ---------------------------
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ]
}