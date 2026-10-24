
"""
Django settings for AI Sertifikat.

Deployment:
    Ubuntu VPS
    Python virtual environment
    Gunicorn
    Nginx
    systemd

Secrets must be provided through environment variables or .env.
"""

import os
from pathlib import Path

import environ


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

FRONTEND_DIR = PROJECT_ROOT / "frontend"


# =========================================================
# ENVIRONMENT
# =========================================================

env = environ.Env(
    DEBUG=(bool, False),
)

# Read .env from the Django project root.
# Do not commit the actual .env file to GitHub.
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.is_file():
    environ.Env.read_env(str(ENV_FILE))


# =========================================================
# SECURITY
# =========================================================

SECRET_KEY = env("SECRET_KEY", default="")

if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is missing. Set it in the environment or .env file."
    )

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "aisertifikat.uz",
        "www.aisertifikat.uz",
        "localhost",
        "127.0.0.1",
    ],
)

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://aisertifikat.uz",
        "https://www.aisertifikat.uz",
    ],
)

# Use only when Nginx is the trusted HTTPS reverse proxy.
# Nginx must set X-Forwarded-Proto correctly.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# Enable HSTS only after HTTPS has been verified on the domain.
SECURE_HSTS_SECONDS = env.int(
    "SECURE_HSTS_SECONDS",
    default=0,
)
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


# =========================================================
# OPENAI
# =========================================================

OPENAI_API_KEY = env(
    "OPENAI_API_KEY",
    default="",
)


# =========================================================
# APPLICATIONS
# =========================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    # Third-party applications
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",

    # Local applications
    "essays",
    "userprofile",
]


# =========================================================
# MIDDLEWARE
# =========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# =========================================================
# URL CONFIGURATION
# =========================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# =========================================================
# TEMPLATES
# =========================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": (
            [FRONTEND_DIR]
            if FRONTEND_DIR.is_dir()
            else []
        ),
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


# =========================================================
# DATABASE
# =========================================================

SQLITE_PATH = env(
    "SQLITE_PATH",
    default=str(BASE_DIR / "db.sqlite3"),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_PATH,
        "OPTIONS": {
            "timeout": 20,
        },
    },
}


# =========================================================
# PASSWORD VALIDATION
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# =========================================================
# LANGUAGE AND TIME
# =========================================================

LANGUAGE_CODE = "uz"

TIME_ZONE = "Asia/Tashkent"

USE_I18N = True
USE_TZ = True


# =========================================================
# STATIC FILES
# =========================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = (
    [FRONTEND_DIR]
    if FRONTEND_DIR.is_dir()
    else []
)

# Django 4.2+ storage configuration.
# Run python manage.py collectstatic during deployment.
STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": (
            "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}


# =========================================================
# MEDIA FILES
# =========================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# =========================================================
# EMAIL
# =========================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp.EmailBackend"
)

EMAIL_HOST = env(
    "EMAIL_HOST",
    default="smtp.gmail.com",
)

EMAIL_PORT = env.int(
    "EMAIL_PORT",
    default=587,
)

EMAIL_USE_TLS = env.bool(
    "EMAIL_USE_TLS",
    default=True,
)

EMAIL_USE_SSL = env.bool(
    "EMAIL_USE_SSL",
    default=False,
)

if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise RuntimeError(
        "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be True."
    )

EMAIL_HOST_USER = env(
    "EMAIL_HOST_USER",
    default="",
)

EMAIL_HOST_PASSWORD = env(
    "EMAIL_HOST_PASSWORD",
    default="",
)

DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default=(
        EMAIL_HOST_USER
        or "noreply@aisertifikat.uz"
    ),
)

EMAIL_TIMEOUT = 20


# =========================================================
# CORS
# =========================================================

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://aisertifikat.uz",
        "https://www.aisertifikat.uz",
    ],
)

# Do not enable CORS_ALLOW_ALL_ORIGINS in production.


# =========================================================
# DJANGO SITES
# =========================================================

SITE_ID = 1


# =========================================================
# AUTHENTICATION
# =========================================================

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"

SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_AUTO_SIGNUP = True


# =========================================================
# DJANGO REST FRAMEWORK
# =========================================================

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}

# Important:
# Change AllowAny to IsAuthenticated for protected APIs,
# or configure permissions individually in your API views.
# Do not assume all endpoints are protected by this setting.


# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# =========================================================
# LOGGING
# =========================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": (
                "{levelname} {asctime} "
                "{name} {message}"
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "allauth": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
