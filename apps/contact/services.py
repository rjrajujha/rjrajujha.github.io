"""Contact submission persistence, email delivery, and message templates."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from email.utils import formatdate
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone

from .models import ContactSubmission, DeliveryStatus
from .otp import ContactChallenge

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContactPayload:
    name: str
    email: str
    subject: str
    message: str
    ip_address: str | None
    user_agent: str
    public_id: str = ""


def build_otp_email(*, name: str, otp: str, ttl_seconds: int) -> tuple[str, str]:
    display_name = getattr(settings, "SITE_DISPLAY_NAME", "Raju Jha") or "Raju Jha"
    ttl_minutes = max(int(ttl_seconds) // 60, 1)
    subject = "Verify your email"
    body = (
        f"{display_name}\n\n"
        "Use this code to verify your email.\n\n"
        f"{otp}\n\n"
        f"Expires in {ttl_minutes} minutes.\n\n"
        "If you didn't request this, ignore this email."
    )
    return subject, body


def build_owner_notification(submission: ContactPayload, *, sent_at: str) -> tuple[str, str]:
    subject = "Contact - Portfolio"
    body = (
        f"Name: {submission.name}\n"
        f"Email: {submission.email}\n"
        f"Message:\n{submission.message}\n\n"
        f"Timestamp: {sent_at}\n"
        f"Submission UUID: {submission.public_id or '—'}\n"
    )
    return subject, body


def create_pending_submission(
    *,
    name: str,
    email: str,
    subject: str,
    message: str,
    ip_address: str | None,
    user_agent: str,
    turnstile_verified: bool,
) -> ContactSubmission:
    """Persist a submission immediately after successful Turnstile verification."""
    return ContactSubmission.objects.create(
        name=name,
        email=email,
        subject=subject,
        message=message,
        ip_address=ip_address,
        user_agent=user_agent,
        otp_verified=False,
        turnstile_verified=turnstile_verified,
        email_sent=False,
        confirmation_sent=False,
        delivery_status=DeliveryStatus.PENDING,
    )


def mark_submission_verified(challenge: ContactChallenge) -> ContactSubmission:
    """Load the submission linked to a verified challenge (OTP already consumed)."""
    submission_id = (challenge.submission_id or "").strip()
    if not submission_id:
        raise ContactSubmission.DoesNotExist("OTP challenge is missing submission_id.")

    try:
        public_id = UUID(str(submission_id))
    except (TypeError, ValueError) as exc:
        raise ContactSubmission.DoesNotExist("Invalid submission id on OTP challenge.") from exc

    record = ContactSubmission.objects.get(public_id=public_id)
    if record.otp_verified:
        return record

    # Cache-only challenges (or interrupted verify) still need a durable flag.
    record.otp_verified = True
    record.turnstile_verified = bool(challenge.turnstile_verified)
    record.verified_at = timezone.now()
    record.save(update_fields=["otp_verified", "turnstile_verified", "verified_at"])
    logger.info("Contact submission marked verified id=%s", str(record.public_id)[:8])
    return record


def deliver_submission(record: ContactSubmission) -> bool:
    """Send the owner notification only. The visitor already received the OTP email."""
    payload = ContactPayload(
        name=record.name,
        email=record.email,
        subject=record.subject,
        message=record.message,
        ip_address=record.ip_address,
        user_agent=record.user_agent,
        public_id=str(record.public_id),
    )
    notify_sent = _send_owner_email(payload)

    record.email_sent = notify_sent
    record.confirmation_sent = False
    if notify_sent:
        record.delivery_status = DeliveryStatus.DELIVERED
        record.delivered_at = timezone.now()
    else:
        record.delivery_status = DeliveryStatus.FAILED
    record.save(
        update_fields=[
            "email_sent",
            "confirmation_sent",
            "delivery_status",
            "delivered_at",
        ]
    )
    return notify_sent


def _send_owner_email(submission: ContactPayload) -> bool:
    sent_at = timezone.localtime().strftime("%Y-%m-%d %H:%M %Z")
    notify_subject, notify_body = build_owner_notification(submission, sent_at=sent_at)

    if not settings.EMAIL_TO:
        logger.warning("EMAIL_TO is not configured. Contact notification email skipped.")
        return False

    try:
        notification = EmailMessage(
            subject=notify_subject,
            body=notify_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_TO],
            reply_to=[submission.email],
            headers={"Date": formatdate(localtime=True)},
        )
        notification.send(fail_silently=False)
        return True
    except Exception:  # noqa: BLE001
        logger.warning(
            "Failed to send contact submission notification email.",
            exc_info=True,
        )
        return False
