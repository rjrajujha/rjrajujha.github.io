"""Lazy Supabase client for optional portfolio persistence features."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseNotConfigured(RuntimeError):
    """Raised when Supabase credentials are missing."""


@lru_cache(maxsize=1)
def get_supabase_client() -> "Client":
    """Return a shared Supabase client, or raise if not configured."""
    url = (getattr(settings, "SUPABASE_URL", None) or "").strip()
    key = (getattr(settings, "SUPABASE_KEY", None) or "").strip()
    if not url or not key:
        raise SupabaseNotConfigured(
            "SUPABASE_URL and SUPABASE_KEY must be set to use Supabase."
        )

    try:
        from supabase import create_client
    except ImportError as exc:  # pragma: no cover
        raise SupabaseNotConfigured("The supabase package is not installed.") from exc

    return create_client(url, key)


def supabase_enabled() -> bool:
    url = (getattr(settings, "SUPABASE_URL", None) or "").strip()
    key = (getattr(settings, "SUPABASE_KEY", None) or "").strip()
    return bool(url and key)


def get_supabase_client_or_none() -> "Client | None":
    if not supabase_enabled():
        return None
    try:
        return get_supabase_client()
    except Exception:  # noqa: BLE001
        logger.exception("Failed to initialize Supabase client.")
        return None
