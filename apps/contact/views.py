import logging

from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic.edit import FormView

from .forms import CONTACT_EMAIL_SUBJECT, ContactForm, ContactOtpForm
from .otp import create_challenge, verify_challenge
from .models import ContactSubmission
from .services import (
    build_otp_email,
    create_pending_submission,
    deliver_submission,
    mark_submission_verified,
)
from .turnstile import extract_turnstile_token, verify_turnstile_token

logger = logging.getLogger(__name__)

# Separate buckets so OTP verify is never blocked by the form-submit cooldown.
SUBMIT_RATE_PREFIX = "contact:submit"
OTP_FAIL_RATE_PREFIX = "contact:otp-fail"
OTP_FAIL_COOLDOWN_SECONDS = 2


def _wants_json(request) -> bool:
    requested_with = request.headers.get("X-Requested-With", "")
    accepts = request.headers.get("Accept", "")
    return requested_with == "XMLHttpRequest" or "application/json" in accepts


def _client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _rate_limit_key(prefix: str, request) -> str:
    return f"{prefix}:{_client_ip(request) or 'unknown'}"


def _is_rate_limited(request, prefix: str, interval: int) -> bool:
    """Return True when the caller must wait; stamp the bucket only when allowing."""
    if interval <= 0:
        return False
    cache_key = _rate_limit_key(prefix, request)
    now_ts = int(timezone.now().timestamp())
    last_ts = cache.get(cache_key)
    if last_ts and now_ts - int(last_ts) < interval:
        return True
    cache.set(cache_key, now_ts, timeout=max(interval * 2, interval + 1))
    return False


def _otp_fail_rate_limited(request) -> bool:
    """Short cooldown after failed OTP attempts only (never blocks first verify)."""
    cache_key = _rate_limit_key(OTP_FAIL_RATE_PREFIX, request)
    last_ts = cache.get(cache_key)
    if not last_ts:
        return False
    now_ts = int(timezone.now().timestamp())
    return now_ts - int(last_ts) < OTP_FAIL_COOLDOWN_SECONDS


def _mark_otp_failure(request) -> None:
    cache.set(
        _rate_limit_key(OTP_FAIL_RATE_PREFIX, request),
        int(timezone.now().timestamp()),
        timeout=OTP_FAIL_COOLDOWN_SECONDS * 3,
    )


class ContactSubmitView(FormView):
    """Step 1: validate form + Turnstile, email OTP, return challenge."""

    form_class = ContactForm
    http_method_names = ["post"]
    success_url = reverse_lazy("core:home")

    def form_valid(self, form):
        interval = max(settings.CONTACT_MIN_SUBMIT_INTERVAL_SECONDS, 10)
        if _is_rate_limited(self.request, SUBMIT_RATE_PREFIX, interval):
            return self._error_response(
                "Please wait a short moment before sending another message.",
                status=429,
            )

        remote_ip = _client_ip(self.request)
        turnstile_token = extract_turnstile_token(
            self.request,
            form.cleaned_data.get("cf_turnstile_response", ""),
        )
        turnstile_ok, turnstile_error = verify_turnstile_token(
            turnstile_token,
            remote_ip=remote_ip,
        )
        if not turnstile_ok:
            if _wants_json(self.request):
                return JsonResponse(
                    {
                        "success": False,
                        "message": turnstile_error,
                        "errors": {"cf_turnstile_response": [turnstile_error]},
                    },
                    status=400,
                )
            messages.error(self.request, turnstile_error)
            return self._redirect_to_contact()

        pending = create_pending_submission(
            name=form.cleaned_data["name"],
            email=form.cleaned_data["email"],
            subject=CONTACT_EMAIL_SUBJECT,
            message=form.cleaned_data["message"],
            ip_address=remote_ip,
            user_agent=(self.request.META.get("HTTP_USER_AGENT") or "")[:255],
            turnstile_verified=True,
        )

        challenge_id, otp = create_challenge(
            submission_id=str(pending.public_id),
            name=pending.name,
            email=pending.email,
            subject=pending.subject,
            message=pending.message,
            ip_address=pending.ip_address,
            user_agent=pending.user_agent,
            turnstile_verified=True,
            submission=pending,
        )

        if not self._send_otp_email(pending.name, pending.email, otp):
            return self._error_response(
                "Could not send the verification code. Please try again shortly.",
                status=502,
            )

        ttl_seconds = max(int(getattr(settings, "CONTACT_OTP_TTL_SECONDS", 600)), 60)
        ttl_minutes = max(ttl_seconds // 60, 1)
        response_message = (
            f"Code sent to {pending.email}. "
            f"It expires in {ttl_minutes} minute(s)."
        )

        if _wants_json(self.request):
            return JsonResponse(
                {
                    "success": True,
                    "requires_otp": True,
                    "challenge_id": challenge_id,
                    "submission_id": str(pending.public_id),
                    "message": response_message,
                    "otp_expires_in_seconds": ttl_seconds,
                    "errors": {},
                }
            )

        messages.info(self.request, response_message)
        return HttpResponseRedirect(
            f"{self.get_success_url()}?open=contact&verify={challenge_id}"
        )

    def form_invalid(self, form):
        if _wants_json(self.request):
            field_errors = {
                field_name: [str(error) for error in errors]
                for field_name, errors in form.errors.items()
            }
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

    def _error_response(self, message: str, status: int = 400):
        if _wants_json(self.request):
            return JsonResponse(
                {"success": False, "message": message, "errors": {}},
                status=status,
            )
        level = messages.warning if status == 429 else messages.error
        level(self.request, message)
        return self._redirect_to_contact()

    def _redirect_to_contact(self):
        return HttpResponseRedirect(f"{self.get_success_url()}?open=contact")

    def _send_otp_email(self, name: str, email: str, otp: str) -> bool:
        ttl_seconds = max(int(getattr(settings, "CONTACT_OTP_TTL_SECONDS", 600)), 60)
        subject, body = build_otp_email(name=name, otp=otp, ttl_seconds=ttl_seconds)
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception:  # noqa: BLE001
            logger.warning("Failed to send contact OTP email.", exc_info=True)
            return False


class ContactVerifyOtpView(View):
    """Step 2: verify OTP, persist submission, then deliver emails."""

    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        form = ContactOtpForm(request.POST)
        if not form.is_valid():
            return self._invalid(form)

        # Do not share the form-submit cooldown. Only throttle rapid failed attempts.
        if _otp_fail_rate_limited(request):
            return self._json_or_redirect(
                success=False,
                message="Please wait a moment before trying again.",
                status=429,
            )

        challenge, error = verify_challenge(
            form.cleaned_data["challenge_id"],
            form.cleaned_data["otp"],
        )
        if challenge is None:
            _mark_otp_failure(request)
            return self._json_or_redirect(success=False, message=error, status=400)

        try:
            record = mark_submission_verified(challenge)
        except ContactSubmission.DoesNotExist:
            logger.warning(
                "OTP verified but submission missing id=%s",
                (challenge.submission_id or "")[:8],
            )
            return self._json_or_redirect(
                success=False,
                message="Verification session expired. Please start again.",
                status=400,
            )

        notify_sent = deliver_submission(record)

        if not notify_sent:
            return self._json_or_redirect(
                success=False,
                message="Verification succeeded, but message delivery failed. Please retry later.",
                status=502,
            )

        response_message = "Thanks for reaching out. Your message was delivered successfully."

        if _wants_json(request):
            return JsonResponse(
                {
                    "success": True,
                    "email_sent": True,
                    "message": response_message,
                    "errors": {},
                }
            )

        messages.success(request, response_message)
        return HttpResponseRedirect(f"{reverse('core:home')}?open=contact")

    def _invalid(self, form: ContactOtpForm):
        if _wants_json(self.request):
            field_errors = {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            }
            return JsonResponse(
                {
                    "success": False,
                    "message": "Please enter a valid verification code.",
                    "errors": field_errors,
                },
                status=400,
            )
        messages.error(self.request, "Please enter a valid verification code.")
        return HttpResponseRedirect(f"{reverse('core:home')}?open=contact")

    def _json_or_redirect(self, *, success: bool, message: str, status: int = 200):
        if _wants_json(self.request):
            return JsonResponse(
                {"success": success, "message": message, "errors": {}},
                status=status if not success else 200,
            )
        if success:
            messages.success(self.request, message)
        else:
            messages.error(self.request, message)
        return HttpResponseRedirect(f"{reverse('core:home')}?open=contact")
