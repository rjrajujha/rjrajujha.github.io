"""Cloudflare Turnstile verification for the contact form."""

from __future__ import annotations

import logging

import urllib.error
import urllib.parse
import urllib.request
import json

from django.conf import settings

logger = logging.getLogger(__name__)

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def turnstile_configured() -> bool:
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def extract_turnstile_token(request, form_token: str = "") -> str:
    """Prefer the Django form field, then Cloudflare's default response field name."""
    token = (form_token or "").strip()
    if token:
        return token
    return (request.POST.get("cf-turnstile-response") or "").strip()


def verify_turnstile_token(token: str, remote_ip: str | None = None) -> tuple[bool, str]:
    """Verify a Turnstile response token.

    When keys are unset (tests/local), verification is skipped.
    """
    if not turnstile_configured():
        return True, ""

    token = (token or "").strip()
    if not token:
        return False, "Please complete the security check."

    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(
        TURNSTILE_VERIFY_URL,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        logger.warning("Turnstile verification request failed.", exc_info=True)
        return False, "Security check temporarily unavailable. Please try again."

    if body.get("success") is True:
        logger.info("Turnstile siteverify succeeded.")
        return True, ""

    logger.warning("Turnstile verification rejected: %s", body.get("error-codes"))
    return False, "Security check failed. Please try again."
