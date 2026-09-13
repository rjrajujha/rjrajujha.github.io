"""SMTP security mode resolution from EMAIL_USE_SECURITY.

Supported values (case-insensitive): ssl | tls | plain.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

VALID_SECURITY_MODES = frozenset({"ssl", "tls", "plain"})
DEFAULT_PORTS = {"ssl": 465, "tls": 587, "plain": 25}


def _env_int_optional(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            f"Invalid {name}={raw!r}. Expected a positive integer port."
        ) from exc


def _normalize_security_mode(raw: str) -> str:
    mode = raw.strip().lower()
    if mode not in VALID_SECURITY_MODES:
        raise ImproperlyConfigured(
            f"Invalid EMAIL_USE_SECURITY={raw!r}. "
            f"Supported values: {', '.join(sorted(VALID_SECURITY_MODES))}."
        )
    return mode


@dataclass(frozen=True)
class ResolvedEmailSettings:
    mode: str
    port: int
    use_ssl: bool
    use_tls: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "port": self.port,
            "use_ssl": self.use_ssl,
            "use_tls": self.use_tls,
        }


def resolve_email_security() -> ResolvedEmailSettings:
    """Resolve SMTP security from EMAIL_USE_SECURITY (default: ssl)."""
    explicit_port = _env_int_optional("EMAIL_PORT")
    if explicit_port is not None and (explicit_port < 1 or explicit_port > 65535):
        raise ImproperlyConfigured(
            f"Invalid EMAIL_PORT={explicit_port}. Expected an integer from 1 to 65535."
        )

    security_raw = (os.getenv("EMAIL_USE_SECURITY") or "ssl").strip()
    mode = _normalize_security_mode(security_raw)
    port = explicit_port if explicit_port is not None else DEFAULT_PORTS[mode]

    return ResolvedEmailSettings(
        mode=mode,
        port=port,
        use_ssl=mode == "ssl",
        use_tls=mode == "tls",
    )


def validate_email_configuration() -> None:
    """Run at startup; raises ImproperlyConfigured on invalid SMTP config."""
    resolved = resolve_email_security()
    backend = (os.getenv("EMAIL_BACKEND") or "").strip() or (
        "django.core.mail.backends.smtp.EmailBackend"
    )
    if not backend.endswith("smtp.EmailBackend"):
        return

    user = (os.getenv("EMAIL_HOST_USER") or "").strip()
    password = (os.getenv("EMAIL_HOST_PASSWORD") or "").strip()
    env_name = (os.getenv("DJANGO_ENV") or "").strip().lower()
    is_production = env_name in {"production", "prod"} or bool(os.getenv("VERCEL"))

    if not user or not password:
        message = (
            "SMTP backend is configured but EMAIL_HOST_USER / EMAIL_HOST_PASSWORD "
            "are incomplete."
        )
        if is_production:
            raise ImproperlyConfigured(message)
        logger.warning(message)

    if resolved.mode == "plain" and is_production:
        logger.warning(
            "EMAIL_USE_SECURITY=plain is enabled in production. Prefer ssl or tls."
        )
