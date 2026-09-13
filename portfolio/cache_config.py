"""Shared cache configuration for multi-worker production deploys.

LocMemCache is process-local. With Gunicorn ``--workers N`` (N>1) or serverless
instances, an OTP written by worker A is invisible to worker B, which surfaces as
"Verification code expired" while the browser countdown still runs.

Production uses Django's DatabaseCache on Supabase Postgres so every worker shares
OTP challenges and rate-limit keys. Tests keep LocMem for speed and isolation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


CACHE_TABLE = "portfolio_cache_table"


def _is_test_run() -> bool:
    return "test" in sys.argv


def build_caches(base_dir: Path | None = None) -> dict[str, dict[str, Any]]:
    if _is_test_run():
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "portfolio-test-cache",
            }
        }

    return {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": CACHE_TABLE,
            "TIMEOUT": 600,
            "OPTIONS": {"MAX_ENTRIES": 5000},
        }
    }
