"""Strict resume secret gate — exact env equality only, no NLP."""

from __future__ import annotations

import os


def try_resume_access_reply(user_message: str) -> str | None:
    """Return resume URL only when user_message equals RESUME_SECRET_KEY byte-for-byte."""
    secret_key = os.environ.get("RESUME_SECRET_KEY", "")
    if user_message != secret_key:
        return None

    resume_url = os.environ.get("RESUME_URL", "")
    access_key = os.environ.get("RESUME_ACCESS_KEY", "")
    if not resume_url or not access_key:
        return "Resume access is not configured on this deployment. Please use the contact section instead."

    if "key=" in resume_url:
        link = resume_url
    else:
        separator = "&" if "?" in resume_url else "?"
        link = f"{resume_url}{separator}key={access_key}"

    return f"Here is the secure resume link: {link}"
