import logging
from dataclasses import dataclass

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import EmailMessage, send_mail
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic.edit import FormView

from .forms import ContactForm

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContactPayload:
    name: str
    email: str
    subject: str
    message: str
    ip_address: str | None
    user_agent: str


class ContactSubmitView(FormView):
    form_class = ContactForm
    http_method_names = ["post"]
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        if self._is_rate_limited():
            message = "Please wait a short moment before sending another message."
            if self._wants_json():
                return JsonResponse(
                    {
                        "success": False,
                        "message": message,
                        "errors": {},
                    },
                    status=429,
                )
            messages.warning(self.request, message)
            return self._redirect_to_contact()

        submission = ContactPayload(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            subject=form.cleaned_data["subject"],
            message=form.cleaned_data["message"],
            ip_address=self._client_ip(),
            user_agent=(self.request.META.get("HTTP_USER_AGENT") or "")[:255],
        )

        notify_sent, ack_sent = self._send_contact_emails(submission)
        response_message = "Thanks for reaching out. Your message was delivered successfully."
        response_level = "success"
        if notify_sent and ack_sent:
            response_message = (
                "Thanks for reaching out. Your message was delivered and confirmation email sent."
            )
            messages.success(self.request, response_message)
        elif notify_sent:
            messages.success(self.request, response_message)
        else:
            response_message = "Message delivery failed. Please retry or reach out on LinkedIn."
            messages.warning(self.request, response_message)
            response_level = "error"

        if self._wants_json():
            return JsonResponse(
                {
                    "success": response_level == "success",
                    "email_sent": notify_sent,
                    "message": response_message,
                    "errors": {},
                },
                status=200 if notify_sent else 502,
            )

        return self._redirect_to_contact()

    def form_invalid(self, form):
        if self._wants_json():
            field_errors: dict[str, list[str]] = {}
            for field_name, errors in form.errors.items():
                field_errors[field_name] = [str(error) for error in errors]
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please correct the highlighted fields and try again.",
                    "errors": field_errors,
                },
                status=400,
            )

        for field_name, field_errors in form.errors.items():
            label = form.fields[field_name].label if field_name in form.fields else "Form"
            messages.error(self.request, f"{label}: {field_errors[0]}")
        return self._redirect_to_contact()

    def _redirect_to_contact(self):
        return HttpResponseRedirect(f"{self.get_success_url()}?open=contact")

    def _wants_json(self) -> bool:
        requested_with = self.request.headers.get("X-Requested-With", "")
        accepts = self.request.headers.get("Accept", "")
        return requested_with == "XMLHttpRequest" or "application/json" in accepts

    def _client_ip(self):
        forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")

    def _is_rate_limited(self) -> bool:
        client_ip = self._client_ip() or "unknown"
        cache_key = f"contact-rate-limit:{client_ip}"
        interval = max(settings.CONTACT_MIN_SUBMIT_INTERVAL_SECONDS, 10)
        now_ts = int(timezone.now().timestamp())
        last_ts = cache.get(cache_key)
        if last_ts and now_ts - int(last_ts) < interval:
            return True
        cache.set(cache_key, now_ts, timeout=interval * 2)
        return False

    def _send_contact_emails(self, submission: ContactPayload) -> tuple[bool, bool]:
        notify_subject = f"[Portfolio Contact] {submission.subject}"
        notify_body = (
            f"Name: {submission.name}\n"
            f"Email: {submission.email}\n"
            f"IP: {submission.ip_address or 'Unknown'}\n\n"
            f"Message:\n{submission.message}"
        )

        notify_sent = False
        ack_sent = False
        if settings.EMAIL_TO:
            try:
                notification = EmailMessage(
                    subject=notify_subject,
                    body=notify_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[settings.EMAIL_TO],
                    reply_to=[submission.email],
                )
                notification.send(fail_silently=False)
                notify_sent = True
            except Exception:  # noqa: BLE001
                logger.warning("Failed to send contact submission notification email.")
        else:
            logger.warning("EMAIL_TO is not configured. Contact notification email skipped.")

        ack_subject = "Thanks for contacting Raju Jha"
        ack_body = (
            f"Hi {submission.name},\n\n"
            "Thank you for reaching out.\n\n"
            "Your message has been received and I will get back to you as soon as possible.\n\n"
            "Thanks,\n"
            "Raju Jha"
        )

        try:
            send_mail(
                subject=ack_subject,
                message=ack_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.email],
                fail_silently=False,
            )
            ack_sent = True
        except Exception:  # noqa: BLE001
            logger.warning("Failed to send contact acknowledgement email.")

        return notify_sent, ack_sent
