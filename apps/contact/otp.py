"""Durable OTP challenges keyed to ContactSubmission rows.

Postgres is the source of truth (``otp_challenge_id`` / ``otp_hash`` on the
submission). A cache mirror keeps multi-worker reads fast and supports unit
tests that do not touch the database. Verification prefers the database and
falls back to the cache mirror.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import uuid
from dataclasses import asdict, dataclass
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import ContactSubmission

logger = logging.getLogger(__name__)


@dataclass
class ContactChallenge:
    challenge_id: str
    submission_id: str
    name: str
    email: str
    subject: str
    message: str
    ip_address: str | None
    user_agent: str
    otp_hash: str
    created_at: float
    expires_at: float
    attempts: int = 0
    used: bool = False
    turnstile_verified: bool = True


def _cache_key(challenge_id: str) -> str:
    return f"contact-otp:{challenge_id}"


def _otp_ttl() -> int:
    return max(int(getattr(settings, "CONTACT_OTP_TTL_SECONDS", 600)), 60)


def _otp_length() -> int:
    return max(int(getattr(settings, "CONTACT_OTP_LENGTH", 6)), 4)


def _max_attempts() -> int:
    return max(int(getattr(settings, "CONTACT_OTP_MAX_ATTEMPTS", 5)), 1)


def _hash_otp(otp: str, challenge_id: str) -> str:
    secret = settings.SECRET_KEY.encode("utf-8")
    message = f"{challenge_id}:{otp}".encode("utf-8")
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def _debug(event: str, **fields) -> None:
    if not settings.DEBUG:
        return
    # Never log the raw OTP code.
    safe = {k: v for k, v in fields.items() if k != "otp"}
    logger.debug("contact_otp_debug event=%s %s", event, safe)


def generate_otp() -> str:
    length = _otp_length()
    return f"{secrets.randbelow(10**length):0{length}d}"


def _challenge_from_submission(submission: ContactSubmission, *, challenge_id: str | None = None) -> ContactChallenge:
    expires = submission.otp_expires_at or timezone.now()
    created = submission.submitted_at or timezone.now()
    return ContactChallenge(
        challenge_id=challenge_id or submission.otp_challenge_id,
        submission_id=str(submission.public_id),
        name=submission.name,
        email=submission.email,
        subject=submission.subject,
        message=submission.message,
        ip_address=submission.ip_address,
        user_agent=submission.user_agent,
        otp_hash=submission.otp_hash,
        created_at=created.timestamp(),
        expires_at=expires.timestamp(),
        attempts=int(submission.otp_attempts or 0),
        used=bool(submission.otp_verified),
        turnstile_verified=bool(submission.turnstile_verified),
    )


def _mirror_cache(challenge: ContactChallenge, ttl: int) -> None:
    key = _cache_key(challenge.challenge_id)
    try:
        cache.set(key, asdict(challenge), timeout=max(int(ttl), 1))
        _debug(
            "cache_mirror_set",
            challenge_id=challenge.challenge_id[:8],
            submission_id=(challenge.submission_id or "")[:8],
            cache_key=key,
            cache_ttl=ttl,
        )
    except Exception:  # noqa: BLE001
        logger.warning(
            "Contact OTP cache mirror failed id=%s",
            challenge.challenge_id[:8],
            exc_info=True,
        )


def _clear_cache(challenge_id: str) -> None:
    try:
        cache.delete(_cache_key(challenge_id))
    except Exception:  # noqa: BLE001
        logger.warning(
            "Contact OTP cache delete failed id=%s",
            challenge_id[:8],
            exc_info=True,
        )


def _load_cache_challenge(challenge_id: str) -> ContactChallenge | None:
    raw = cache.get(_cache_key(challenge_id))
    if not isinstance(raw, dict):
        return None
    try:
        data = dict(raw)
        data.setdefault("turnstile_verified", True)
        data.setdefault("submission_id", "")
        if "expires_at" not in data:
            created = float(data.get("created_at") or timezone.now().timestamp())
            data["expires_at"] = created + _otp_ttl()
        return ContactChallenge(**data)
    except (TypeError, ValueError, KeyError):
        logger.exception("Contact OTP cache payload corrupt id=%s", challenge_id[:8])
        return None


def create_challenge(
    *,
    submission_id: str,
    name: str,
    email: str,
    subject: str,
    message: str,
    ip_address: str | None,
    user_agent: str,
    turnstile_verified: bool = True,
    submission: ContactSubmission | None = None,
) -> tuple[str, str]:
    """Create an OTP challenge.

    When ``submission`` is provided (production path), the challenge is written
    to the submission row and mirrored to cache. Without a submission instance
    (unit tests), the challenge is cache-only.
    """
    ttl = _otp_ttl()
    now = timezone.now()
    challenge_id = uuid.uuid4().hex
    otp = generate_otp()
    otp_hash = _hash_otp(otp, challenge_id)
    expires_at = now + timedelta(seconds=ttl)

    if isinstance(submission, ContactSubmission):
        with transaction.atomic():
            locked = ContactSubmission.objects.select_for_update().get(pk=submission.pk)
            locked.otp_challenge_id = challenge_id
            locked.otp_hash = otp_hash
            locked.otp_expires_at = expires_at
            locked.otp_attempts = 0
            locked.otp_verified = False
            locked.turnstile_verified = turnstile_verified
            locked.save(
                update_fields=[
                    "otp_challenge_id",
                    "otp_hash",
                    "otp_expires_at",
                    "otp_attempts",
                    "otp_verified",
                    "turnstile_verified",
                ]
            )
            submission = locked
    else:
        submission = None

    challenge = ContactChallenge(
        challenge_id=challenge_id,
        submission_id=str(getattr(submission, "public_id", None) or submission_id),
        name=name,
        email=email,
        subject=subject,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
        otp_hash=otp_hash,
        created_at=now.timestamp(),
        expires_at=expires_at.timestamp(),
        turnstile_verified=turnstile_verified,
    )
    _mirror_cache(challenge, ttl)
    logger.info(
        "Contact OTP challenge created id=%s submission=%s expires_in=%ss durable=%s",
        challenge_id[:8],
        str(challenge.submission_id)[:8],
        ttl,
        submission is not None,
    )
    _debug(
        "challenge_created",
        challenge_id=challenge_id[:8],
        submission_id=str(challenge.submission_id),
        cache_key=_cache_key(challenge_id),
        cache_ttl=ttl,
        durable=submission is not None,
    )
    return challenge_id, otp


def _verify_against_challenge(
    challenge: ContactChallenge,
    otp: str,
    *,
    submission: ContactSubmission | None,
) -> tuple[ContactChallenge | None, str]:
    if challenge.used:
        _clear_cache(challenge.challenge_id)
        return None, "Verification code expired. Please start again."

    if timezone.now().timestamp() >= challenge.expires_at:
        if submission is not None:
            submission.otp_challenge_id = ""
            submission.otp_hash = ""
            submission.otp_expires_at = None
            submission.save(update_fields=["otp_challenge_id", "otp_hash", "otp_expires_at"])
        _clear_cache(challenge.challenge_id)
        _debug("verify_expired", challenge_id=challenge.challenge_id[:8])
        return None, "Verification code expired. Please start again."

    if challenge.attempts >= _max_attempts():
        if submission is not None:
            submission.otp_challenge_id = ""
            submission.otp_hash = ""
            submission.otp_expires_at = None
            submission.otp_attempts = challenge.attempts
            submission.save(
                update_fields=["otp_challenge_id", "otp_hash", "otp_expires_at", "otp_attempts"]
            )
        _clear_cache(challenge.challenge_id)
        return None, "Too many attempts. Please request a new code."

    provided = _hash_otp((otp or "").strip(), challenge.challenge_id)
    challenge.attempts += 1

    if not hmac.compare_digest(challenge.otp_hash, provided):
        remaining = _max_attempts() - challenge.attempts
        if submission is not None:
            submission.otp_attempts = challenge.attempts
            if remaining <= 0:
                submission.otp_challenge_id = ""
                submission.otp_hash = ""
                submission.otp_expires_at = None
                submission.save(
                    update_fields=[
                        "otp_challenge_id",
                        "otp_hash",
                        "otp_expires_at",
                        "otp_attempts",
                    ]
                )
                _clear_cache(challenge.challenge_id)
                return None, "Too many attempts. Please request a new code."
            submission.save(update_fields=["otp_attempts"])
        remaining_ttl = max(int(challenge.expires_at - timezone.now().timestamp()), 1)
        if remaining <= 0:
            _clear_cache(challenge.challenge_id)
            return None, "Too many attempts. Please request a new code."
        _mirror_cache(challenge, remaining_ttl)
        _debug(
            "verify_invalid",
            challenge_id=challenge.challenge_id[:8],
            submission_id=(challenge.submission_id or "")[:8],
            attempts=challenge.attempts,
        )
        return None, "Invalid verification code. Please try again."

    if submission is not None:
        submission.otp_verified = True
        submission.verified_at = timezone.now()
        submission.otp_hash = ""
        submission.otp_challenge_id = ""
        submission.otp_expires_at = None
        submission.otp_attempts = challenge.attempts
        submission.save(
            update_fields=[
                "otp_verified",
                "verified_at",
                "otp_hash",
                "otp_challenge_id",
                "otp_expires_at",
                "otp_attempts",
            ]
        )
        _debug(
            "verify_success_db",
            challenge_id=challenge.challenge_id[:8],
            submission_id=str(submission.public_id),
            db_update="otp_verified",
        )

    _clear_cache(challenge.challenge_id)
    challenge.used = True
    challenge.otp_hash = ""
    logger.info(
        "Contact OTP challenge verified id=%s submission=%s",
        challenge.challenge_id[:8],
        (challenge.submission_id or "")[:8],
    )
    _debug(
        "verify_success",
        challenge_id=challenge.challenge_id[:8],
        submission_id=(challenge.submission_id or "")[:8],
    )
    return challenge, ""


def verify_challenge(challenge_id: str, otp: str) -> tuple[ContactChallenge | None, str]:
    challenge_id = (challenge_id or "").strip()
    if not challenge_id:
        return None, "Verification code expired. Please start again."

    # Prefer durable DB state (works across Gunicorn workers / serverless).
    try:
        with transaction.atomic():
            submission = (
                ContactSubmission.objects.select_for_update()
                .filter(otp_challenge_id=challenge_id)
                .first()
            )
            if submission is not None:
                challenge = _challenge_from_submission(submission, challenge_id=challenge_id)
                return _verify_against_challenge(challenge, otp, submission=submission)
    except Exception:  # noqa: BLE001
        # DB unavailable in some unit-test contexts; fall through to cache.
        logger.debug("Contact OTP DB lookup skipped id=%s", challenge_id[:8], exc_info=True)

    cached = _load_cache_challenge(challenge_id)
    if cached is None:
        logger.warning("Contact OTP challenge missing id=%s", challenge_id[:8])
        _debug("verify_missing", challenge_id=challenge_id[:8], cache_key=_cache_key(challenge_id))
        return None, "Verification code expired. Please start again."

    _debug(
        "verify_cache_fallback",
        challenge_id=challenge_id[:8],
        submission_id=(cached.submission_id or "")[:8],
    )
    return _verify_against_challenge(cached, otp, submission=None)
