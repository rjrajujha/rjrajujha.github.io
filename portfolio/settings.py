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


def resolve_contact_min_submit_interval() -> int:
    return env_int("CONTACT_MIN_SUBMIT_INTERVAL_SECONDS", 45, min_value=10)


def resolve_chatbot_min_submit_interval() -> int:
    return env_int("CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS", 2, min_value=1)


def resolve_chatbot_model(provider: str, configured_model: str = "") -> str:
    model = (configured_model or os.getenv("CHATBOT_MODEL") or "").strip()
    if model:
        return model
    provider_name = (provider or "").strip().lower()
    if provider_name == "gemini":
        return "gemini-1.5-flash"
    if provider_name in {"openai", "auto"}:
        return "gpt-4o-mini"
    return ""


def resolve_is_production(is_vercel: bool) -> bool:
    """Single production switch: DJANGO_ENV=production|prod (plus Vercel inference)."""
    env_name = (os.getenv("DJANGO_ENV") or "").strip().lower()
    if env_name in {"production", "prod"}:
        return True
    if env_name in {"development", "dev", "local", "test"}:
        return False
    return is_vercel


def should_enable_security(is_production: bool, debug: bool) -> bool:
    return is_production and not debug


from portfolio.cache_config import build_caches
from portfolio.database_config import build_databases, database_apps
from portfolio.email_config import resolve_email_security, validate_email_configuration

load_env_file(BASE_DIR / ".env")
validate_email_configuration()

SECRET_KEY = (os.getenv("DJANGO_SECRET_KEY") or "").strip() or "django-insecure-change-me"
IS_VERCEL = bool(os.getenv("VERCEL"))
DEBUG = env_bool("DJANGO_DEBUG", not IS_VERCEL)
IS_PRODUCTION = resolve_is_production(IS_VERCEL)

if IS_PRODUCTION and (SECRET_KEY.startswith("django-insecure-") or len(SECRET_KEY) < 50):
    from django.core.exceptions import ImproperlyConfigured

    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be a long random value (50+ characters) in production."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "")

INSTALLED_APPS = database_apps() + [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.projects",
    "apps.contact",
    "apps.chatbot",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "portfolio.urls"
CSRF_FAILURE_VIEW = "apps.core.error_views.csrf_failure"
# Disabled by default; enable only for local debugging of custom error pages.
ENABLE_ERROR_TEST_ROUTES = env_bool("ENABLE_ERROR_TEST_ROUTES", False)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_profile",
            ],
        },
    },
]

WSGI_APPLICATION = "portfolio.wsgi.application"
ASGI_APPLICATION = "portfolio.asgi.application"

DATABASES = build_databases()
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
CACHES = build_caches(BASE_DIR)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
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

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or "").strip()

TURNSTILE_SITE_KEY = (os.getenv("TURNSTILE_SITE_KEY") or "").strip()
TURNSTILE_SECRET_KEY = (os.getenv("TURNSTILE_SECRET_KEY") or "").strip()

EMAIL_BACKEND = resolve_email_backend()
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
_smtp = resolve_email_security()
EMAIL_PORT = _smtp.port
EMAIL_USE_SSL = _smtp.use_ssl
EMAIL_USE_TLS = _smtp.use_tls
EMAIL_USE_SECURITY = _smtp.mode
DEFAULT_FROM_EMAIL = (
    (os.getenv("DEFAULT_FROM_EMAIL") or "").strip() or EMAIL_HOST_USER or "no-reply@localhost"
)
EMAIL_TO = os.getenv("EMAIL_TO", EMAIL_HOST_USER)
CONTACT_MIN_SUBMIT_INTERVAL_SECONDS = resolve_contact_min_submit_interval()
CONTACT_OTP_TTL_SECONDS = env_int("CONTACT_OTP_TTL_SECONDS", 600, min_value=60)
CONTACT_OTP_LENGTH = env_int("CONTACT_OTP_LENGTH", 6, min_value=4)
CONTACT_OTP_MAX_ATTEMPTS = env_int("CONTACT_OTP_MAX_ATTEMPTS", 5, min_value=1)
SITE_DISPLAY_NAME = os.getenv("SITE_DISPLAY_NAME", "Raju Jha").strip() or "Raju Jha"

CHATBOT_PROVIDER = os.getenv("CHATBOT_PROVIDER", "local").lower()
CHATBOT_MODEL = (os.getenv("CHATBOT_MODEL") or "").strip()
CHATBOT_TIMEOUT_SECONDS = int(os.getenv("CHATBOT_TIMEOUT_SECONDS", "20"))
CHATBOT_MAX_CONTEXT_CHARS = int(os.getenv("CHATBOT_MAX_CONTEXT_CHARS", "6500"))
CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS = resolve_chatbot_min_submit_interval()
RESUME_URL = os.getenv("RESUME_URL", "").strip()
RESUME_ACCESS_KEY = os.getenv("RESUME_ACCESS_KEY", "").strip()
RESUME_SECRET_KEY = os.getenv("RESUME_SECRET_KEY", "RESUME-LINK").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if not DEBUG else "DEBUG",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

ENABLE_SECURITY_SETTINGS = should_enable_security(IS_PRODUCTION, DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

if ENABLE_SECURITY_SETTINGS:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 31536000, min_value=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", True)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", True)
else:
    # Safe development defaults; optional overrides still honored.
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)
    SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", False)
    CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", False)
    SECURE_HSTS_SECONDS = env_int("SECURE_HSTS_SECONDS", 0, min_value=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
    SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)
