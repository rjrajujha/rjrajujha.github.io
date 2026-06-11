from apps.contact.forms import ContactForm


def site_profile(request):
    return {
        "contact_form": ContactForm(),
    }
