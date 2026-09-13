"""Strict resume secret gate — exact equality only, no NLP."""

from __future__ import annotations

from django.conf import settings


def try_resume_access_reply(user_message: str) -> str | None:
    """Return resume URL only when user_message equals RESUME_SECRET_KEY byte-for-byte."""
    secret_key = (getattr(settings, "RESUME_SECRET_KEY", None) or "").strip()
    if not secret_key or user_message != secret_key:
        return None

    resume_url = (getattr(settings, "RESUME_URL", None) or "").strip()
    access_key = (getattr(settings, "RESUME_ACCESS_KEY", None) or "").strip()
    if not resume_url or not access_key:
        return (
            "Resume access is not configured on this deployment. "
            "Please use the contact section instead."
        )

    if "key=" in resume_url:
        link = resume_url
    else:
        separator = "&" if "?" in resume_url else "?"
        link = f"{resume_url}{separator}key={access_key}"

    return f"You can view my resume here:\n\n[Resume PDF]({link})"
