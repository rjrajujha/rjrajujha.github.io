from django.conf import settings

from apps.contact.forms import ContactForm
from apps.contact.turnstile import turnstile_configured


def site_profile(request):
    return {
        "contact_form": ContactForm(),
        "turnstile_site_key": settings.TURNSTILE_SITE_KEY,
        "turnstile_enabled": turnstile_configured(),
        "contact_otp_ttl_seconds": max(int(getattr(settings, "CONTACT_OTP_TTL_SECONDS", 600)), 60),
    }
