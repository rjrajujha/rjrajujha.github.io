"""Database configuration helpers for optional persistence.

Set ``USE_DATABASE=true`` in the environment to enable ORM-backed models.
When disabled (default), the portfolio runs without database startup or migrations.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def use_database() -> bool:
    return env_bool("USE_DATABASE", False)


def sqlite_database(base_dir: Path, is_vercel: bool) -> dict[str, Any]:
    default_path = "/tmp/db.sqlite3" if is_vercel else str(base_dir / "db.sqlite3")
    sqlite_path = os.getenv("SQLITE_PATH", default_path)
    return {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": sqlite_path,
    }


def postgresql_database() -> dict[str, Any]:
    return {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME", "portfolio"),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {},
    }


def build_databases(base_dir: Path, is_vercel: bool) -> dict[str, dict[str, Any]]:
    """Build DATABASES dict from environment (SQLite or PostgreSQL)."""
    engine = (os.getenv("DB_ENGINE") or "django.db.backends.sqlite3").strip()
    if "postgresql" in engine:
        return {"default": postgresql_database()}
    return {"default": sqlite_database(base_dir, is_vercel)}


def database_apps() -> list[str]:
    """Django apps required when database-backed features are enabled."""
    return [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
    ]


def vector_database_notes() -> str:
    """Documentation hook for future vector DB integration (pgvector, etc.)."""
    return (
        "For vector search, enable PostgreSQL with pgvector or add a dedicated "
        "VECTOR_DATABASE_URL service. Wire retrieval in apps.chatbot.services "
        "without changing the provider fallback chain."
    )
