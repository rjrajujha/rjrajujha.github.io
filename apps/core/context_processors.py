from apps.contact.forms import ContactForm

from .content import PROFILE


def site_profile(request):
    return {
        "profile": PROFILE,
        "contact_form": ContactForm(),
    }
