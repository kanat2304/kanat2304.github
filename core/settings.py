from pathlib import Path
import os
from dotenv import load_dotenv

# .env файлын жүктейміз (API кілттер үшін)
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# API кілттерді оқимыз
GEMINI_KEYS = os.getenv("GEMINI_API_KEYS").split(',') if os.getenv("GEMINI_API_KEYS") else []

SECRET_KEY = 'django-insecure-change-me-please'

# Дебаг режимі қосулы (қателерді көру үшін)
DEBUG = True

ALLOWED_HOSTS = []

# Қосымшалар тізімі
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'testing',  # <--- Біздің қосымша (Мұны ұмытпаңыз!)
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# --- МАҢЫЗДЫ ӨЗГЕРІС ---
# Пароль тексеруді өшірдік. Енді "123" паролін қабылдайды.
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'ru-ru' # Сайт тілі (орысша)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'