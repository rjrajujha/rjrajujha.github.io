"""Supabase PostgreSQL database configuration for Django."""

from __future__ import annotations

import os
import sys
from typing import Any
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


def database_apps() -> list[str]:
    return [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
    ]


def _is_test_run() -> bool:
    return "test" in sys.argv


def _database_from_url(database_url: str) -> dict[str, Any]:
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise ImproperlyConfigured(
            "DATABASE_URL must use the postgres:// or postgresql:// scheme."
        )
    if not parsed.hostname:
        raise ImproperlyConfigured("DATABASE_URL is missing a host.")

    name = (parsed.path or "").lstrip("/") or "postgres"
    config: dict[str, Any] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(name),
        "USER": unquote(parsed.username or ""),
        "PASSWORD": unquote(parsed.password or ""),
        "HOST": parsed.hostname,
        "PORT": str(parsed.port or "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {},
    }
    if str(config["PORT"]) == "6543" or "pooler.supabase.com" in (parsed.hostname or ""):
        config["OPTIONS"]["sslmode"] = os.getenv("DB_SSLMODE", "require")
    elif os.getenv("DB_SSLMODE"):
        config["OPTIONS"]["sslmode"] = os.getenv("DB_SSLMODE")
    return config


def _database_from_parts() -> dict[str, Any] | None:
    host = (os.getenv("DB_HOST") or "").strip()
    if not host:
        return None
    config: dict[str, Any] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (os.getenv("DB_NAME") or "postgres").strip(),
        "USER": (os.getenv("DB_USER") or "postgres").strip(),
        "PASSWORD": os.getenv("DB_PASSWORD") or "",
        "HOST": host,
        "PORT": (os.getenv("DB_PORT") or "5432").strip(),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {},
    }
    sslmode = (os.getenv("DB_SSLMODE") or "").strip()
    if sslmode:
        config["OPTIONS"]["sslmode"] = sslmode
    elif "supabase.co" in host or "pooler.supabase.com" in host:
        config["OPTIONS"]["sslmode"] = "require"
    return config


def _placeholder_test_database() -> dict[str, Any]:
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "portfolio_test",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": "127.0.0.1",
        "PORT": "5432",
        "CONN_MAX_AGE": 0,
        "OPTIONS": {},
    }


def build_databases() -> dict[str, dict[str, Any]]:
    """Build Django DATABASES for Supabase Postgres only."""
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if database_url:
        return {"default": _database_from_url(database_url)}

    from_parts = _database_from_parts()
    if from_parts:
        return {"default": from_parts}

    if _is_test_run():
        return {"default": _placeholder_test_database()}

    raise ImproperlyConfigured(
        "Supabase Postgres is required. Set DATABASE_URL "
        "or DB_HOST / DB_NAME / DB_USER / DB_PASSWORD."
    )
