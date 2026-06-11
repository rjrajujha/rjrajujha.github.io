from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(env_path: Path) -> None:
    """Load key=value pairs from a local .env file into process env."""
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"").strip("'")
        os.environ.setdefault(key, value)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_int(name: str, default: int, min_value: int | None = None) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return default
    if min_value is not None and value < min_value:
        return min_value
    return value


def resolve_email_backend() -> str:
    backend = (os.getenv("EMAIL_BACKEND") or "").strip()
    return backend or "django.core.mail.backends.smtp.EmailBackend"


def derive_email_use_tls(email_use_ssl: bool, email_port: int) -> bool:
    return (not email_use_ssl) and email_port == 587


def resolve_contact_min_submit_interval() -> int:
    return env_int(
        "CONTACT_MIN_SUBMIT_INTERVAL_SECONDS",
        45,
        min_value=10,
    )


def resolve_chatbot_min_submit_interval() -> int:
    return env_int(
        "CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS",
        2,
        min_value=1,
    )


def resolve_is_production(is_vercel: bool) -> bool:
    env_name = (os.getenv("DJANGO_ENV") or "").strip().lower()
    inferred_production = is_vercel or env_name in {"production", "prod"}
    return env_bool("DJANGO_PRODUCTION", inferred_production)


def should_enable_security(is_production: bool, debug: bool) -> bool:
    return is_production and not debug


from portfolio.database_config import build_databases, database_apps, use_database

load_env_file(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
USE_DATABASE = use_database()
IS_VERCEL = bool(os.getenv("VERCEL"))
DEBUG = env_bool("DJANGO_DEBUG", not IS_VERCEL)
IS_PRODUCTION = resolve_is_production(IS_VERCEL)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.projects",
    "apps.contact",
    "apps.chatbot",
]
if USE_DATABASE:
    INSTALLED_APPS = database_apps() + INSTALLED_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portfolio.urls"
CSRF_FAILURE_VIEW = "apps.core.error_views.csrf_failure"
ENABLE_ERROR_TEST_ROUTES = env_bool("ENABLE_ERROR_TEST_ROUTES", False)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_profile",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio.wsgi.application"
ASGI_APPLICATION = "portfolio.asgi.application"

if USE_DATABASE:
    DATABASES = build_databases(BASE_DIR, IS_VERCEL)
else:
    # In-memory SQLite satisfies Django internals only; no app models or migrations are used.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "portfolio-cache",
    }
}

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email settings used by the contact form workflow.
EMAIL_BACKEND = resolve_email_backend()
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = env_int("EMAIL_PORT", 465, min_value=1)
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", True)
EMAIL_USE_TLS = derive_email_use_tls(EMAIL_USE_SSL, EMAIL_PORT)
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER or "no-reply@localhost"
EMAIL_TO = os.getenv("EMAIL_TO", EMAIL_HOST_USER)
CONTACT_MIN_SUBMIT_INTERVAL_SECONDS = resolve_contact_min_submit_interval()

# AI chatbot provider configuration.
CHATBOT_PROVIDER = os.getenv("CHATBOT_PROVIDER", "local").lower()
CHATBOT_TIMEOUT_SECONDS = int(os.getenv("CHATBOT_TIMEOUT_SECONDS", "20"))
CHATBOT_STORE_LOGS = env_bool("CHATBOT_STORE_LOGS", False)
CHATBOT_MAX_CONTEXT_CHARS = int(os.getenv("CHATBOT_MAX_CONTEXT_CHARS", "6500"))
CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS = resolve_chatbot_min_submit_interval()
RESUME_URL = os.getenv("RESUME_URL", "").strip()
RESUME_ACCESS_KEY = os.getenv("RESUME_ACCESS_KEY", "").strip()
RESUME_SECRET_KEY = os.getenv("RESUME_SECRET_KEY", "RESUME-LINK").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

ENABLE_SECURITY_SETTINGS = should_enable_security(IS_PRODUCTION, DEBUG)
if ENABLE_SECURITY_SETTINGS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
