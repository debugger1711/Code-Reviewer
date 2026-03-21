from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"
GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_SECRET = os.environ.get("GOOGLE_OAUTH_SECRET", "").strip()


def csv_env(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]

ALLOWED_HOSTS = csv_env("DJANGO_ALLOWED_HOSTS") or [
    "code-review-tau-ebon.vercel.app",
    ".vercel.app",
    "localhost",
    "127.0.0.1",
]

CSRF_TRUSTED_ORIGINS = csv_env("DJANGO_CSRF_TRUSTED_ORIGINS") or [
    "https://code-review-tau-ebon.vercel.app",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "reviewer",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "codereviewer.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "codereviewer.wsgi.application"
ASGI_APPLICATION = "codereviewer.asgi.application"

# Database Configuration:
# - Production defaults to DATABASE_URL when DEBUG is false
# - Local development defaults to SQLite unless DJANGO_USE_REMOTE_DB=true
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_REMOTE_DATABASE = os.environ.get("DJANGO_USE_REMOTE_DB", "false").lower() == "true"

if DATABASE_URL and (not DEBUG or USE_REMOTE_DATABASE):
    # PostgreSQL (Neon) Configuration
    db_parsed = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_parsed.path.lstrip("/"),
            "USER": db_parsed.username,
            "PASSWORD": db_parsed.password,
            "HOST": db_parsed.hostname,
            "PORT": db_parsed.port or 5432,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {
                "sslmode": "require",
            },
        }
    }
else:
    # SQLite3 for development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "reviewer" / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GEMINI_DEFAULT_MODEL = os.environ.get("GEMINI_DEFAULT_MODEL", "gemini-2.5-flash")
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
]
SUPPORTED_LANGUAGES = [
    ("python", "Python"),
    ("javascript", "JavaScript"),
    ("cpp", "C++"),
    ("java", "Java"),
]
TERMINAL_TIMEOUT_SECONDS = int(os.environ.get("TERMINAL_TIMEOUT_SECONDS", "5"))
MAX_REVIEW_REQUEST_BYTES = int(os.environ.get("MAX_REVIEW_REQUEST_BYTES", str(10 * 1024 * 1024)))
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_REVIEW_REQUEST_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_REVIEW_REQUEST_BYTES

# Django-Allauth Configuration
SITE_ID = 1
SOCIALACCOUNT_ADAPTER = "reviewer.adapters.CodeReviewerSocialAccountAdapter"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Allauth Settings
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_SIGNUP_EMAIL_VERIFY = "optional"
SOCIALACCOUNT_AUTO_SIGNUP = True

# Google OAuth Provider Settings
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": (
            [
                {
                    "client_id": GOOGLE_OAUTH_CLIENT_ID,
                    "secret": GOOGLE_OAUTH_SECRET,
                    "key": "",
                    "settings": {
                        "scope": [
                            "profile",
                            "email",
                        ],
                        "auth_params": {
                            "access_type": "online",
                        },
                    },
                }
            ]
            if GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_SECRET
            else []
        ),
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
        "FETCH_USERINFO": True,
        "VERIFIED_EMAIL": True,
        "VERSION": "v2",
    }
}

# Login/Logout URLs
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

# Upload directory
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
