import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView

from .forms import ContactForm

logger = logging.getLogger(__name__)


class ContactSubmitView(FormView):
    form_class = ContactForm
    http_method_names = ["post"]
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        submission = form.save(commit=False)
        submission.ip_address = self._client_ip()
        submission.user_agent = (self.request.META.get("HTTP_USER_AGENT") or "")[:255]
        submission.save()

        email_sent = self._send_contact_email(submission)
        if email_sent:
            submission.sent_to_email = True
            submission.save(update_fields=["sent_to_email"])
            messages.success(self.request, "Thanks for reaching out. I will get back to you shortly.")
        else:
            messages.warning(
                self.request,
                "Your message was saved, but email delivery failed. You can also reach me on LinkedIn.",
            )

        return self._redirect_to_contact()

    def form_invalid(self, form):
        for field_name, field_errors in form.errors.items():
            label = form.fields[field_name].label if field_name in form.fields else "Form"
            messages.error(self.request, f"{label}: {field_errors[0]}")
        return self._redirect_to_contact()

    def _redirect_to_contact(self):
        return HttpResponseRedirect(f"{self.get_success_url()}#contact")

    def _client_ip(self):
        forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")

    def _send_contact_email(self, submission) -> bool:
        subject = f"[Portfolio Contact] {submission.subject}"
        body = (
            f"Name: {submission.name}\n"
            f"Email: {submission.email}\n"
            f"IP: {submission.ip_address or 'Unknown'}\n\n"
            f"Message:\n{submission.message}"
        )

        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_RECEIVER_EMAIL],
                fail_silently=False,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to send contact submission email: %s", exc)
            return False
