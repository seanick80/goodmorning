"""Django settings for Good Morning Dashboard."""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-dev-key-change-me") # Verify: this is just fallback if not set in .env
DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "corsheaders",
    "django_apscheduler",
    # Project
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DATA_DIR = os.environ.get(
    "GOODMORNING_DATA_DIR",
    os.path.expanduser("~/goodmorning-data"),
)
os.makedirs(DATA_DIR, exist_ok=True)

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{os.path.join(DATA_DIR, 'db.sqlite3')}",
    )
}

# SQLite optimizations (applied only when using SQLite)
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["init_command"] = (
        "PRAGMA journal_mode=wal;"
        "PRAGMA busy_timeout=5000;"
    )
    DATABASES["default"]["OPTIONS"]["transaction_mode"] = "IMMEDIATE"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}

# CORS (Vite dev server + Pi kiosk)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://goodmorning.local",
    "http://goodmorning.local:80",
]
CORS_ALLOW_CREDENTIALS = True

# APScheduler
APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"
APSCHEDULER_RUN_NOW_TIMEOUT = 25

# External API keys
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY", "")

# Logging
LOGS_DIR = BASE_DIR / "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "general_file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "general.log",
            "formatter": "verbose",
        },
        "scheduler_file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "scheduler.log",
            "formatter": "verbose",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "errors.log",
            "formatter": "verbose",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "general_file", "error_file"],
            "level": "INFO",
            "propagate": True,
        },
        "dashboard": {
            "handlers": ["console", "general_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "dashboard.jobs": {
            "handlers": ["console", "scheduler_file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
