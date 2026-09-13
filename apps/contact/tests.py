from uuid import uuid4
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.cache import cache
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from .admin import ContactSubmissionAdmin
from .forms import CONTACT_EMAIL_SUBJECT, ContactForm
from .models import DeliveryStatus
from .otp import create_challenge, verify_challenge
from .services import (
    ContactPayload,
    build_otp_email,
    build_owner_notification,
    create_pending_submission,
    deliver_submission,
    mark_submission_verified,
)
from .turnstile import extract_turnstile_token, verify_turnstile_token


def _pending_record(**overrides):
    record = MagicMock()
    record.public_id = overrides.get("public_id", uuid4())
    record.name = overrides.get("name", "Raju")
    record.email = overrides.get("email", "raju@example.com")
    record.subject = overrides.get("subject", CONTACT_EMAIL_SUBJECT)
    record.message = overrides.get(
        "message",
        "I would like to discuss a backend architecture engagement.",
    )
    record.ip_address = overrides.get("ip_address", "127.0.0.1")
    record.user_agent = overrides.get("user_agent", "test")
    record.otp_verified = False
    record.turnstile_verified = True
    record.email_sent = False
    record.confirmation_sent = False
    record.delivery_status = DeliveryStatus.PENDING
    record.delivered_at = None
    return record


class ContactFormTests(SimpleTestCase):
    def test_honeypot_blocks_spam(self):
        form = ContactForm(
            data={
                "name": "Spam",
                "email": "spam@example.com",
                "message": "This is a fake message with enough words.",
                "company": "bot-filled",
            }
        )
        self.assertFalse(form.is_valid())

    def test_valid_form_does_not_require_subject(self):
        form = ContactForm(
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertEqual(CONTACT_EMAIL_SUBJECT, "Contact - Portfolio")


@override_settings(SECURE_SSL_REDIRECT=False, TURNSTILE_SITE_KEY="", TURNSTILE_SECRET_KEY="")
class ContactViewTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        EMAIL_HOST_USER="portfolio@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    @patch("apps.contact.views.create_pending_submission")
    def test_valid_submission_sends_otp_email(self, mock_pending):
        mock_pending.return_value = _pending_record()
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
                "cf_turnstile_response": "",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["requires_otp"])
        self.assertTrue(payload["challenge_id"])
        self.assertTrue(payload["submission_id"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("otp_expires_in_seconds", payload)
        mock_pending.assert_called_once()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        EMAIL_HOST_USER="portfolio@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    @patch("apps.contact.views.deliver_submission", return_value=True)
    @patch("apps.contact.views.mark_submission_verified")
    def test_otp_verification_delivers_message(self, mock_mark, mock_deliver):
        mock_mark.return_value = MagicMock()
        submission_id = str(uuid4())
        challenge_id, otp = create_challenge(
            submission_id=submission_id,
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        mail.outbox.clear()

        response = self.client.post(
            reverse("contact:verify-otp"),
            data={"challenge_id": challenge_id, "otp": otp},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        mock_mark.assert_called_once()
        mock_deliver.assert_called_once()
        challenge, error = verify_challenge(challenge_id, otp)
        self.assertIsNone(challenge)
        self.assertIn("expired", error.lower())

    def test_invalid_otp_fails(self):
        challenge_id, _otp = create_challenge(
            submission_id=str(uuid4()),
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        response = self.client.post(
            reverse("contact:verify-otp"),
            data={"challenge_id": challenge_id, "otp": "000000"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    @patch("apps.contact.services.EmailMessage.send", side_effect=OSError("smtp down"))
    def test_email_failure_preserves_submission_as_failed(self, _mock_send):
        record = MagicMock()
        record.name = "Raju"
        record.email = "fail@example.com"
        record.subject = CONTACT_EMAIL_SUBJECT
        record.message = "I would like to discuss a backend architecture engagement."
        record.ip_address = "127.0.0.1"
        record.user_agent = "test"
        record.public_id = uuid4()
        record.email_sent = False
        record.confirmation_sent = False
        record.delivery_status = DeliveryStatus.PENDING
        record.delivered_at = None

        notify_sent = deliver_submission(record)
        self.assertFalse(notify_sent)
        self.assertEqual(record.delivery_status, DeliveryStatus.FAILED)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        TURNSTILE_SITE_KEY="site",
        TURNSTILE_SECRET_KEY="secret",
    )
    @patch("apps.contact.views.create_pending_submission")
    @patch("apps.contact.views.verify_turnstile_token", return_value=(False, "Security check failed."))
    def test_turnstile_failure_blocks_submission(self, _mock, mock_pending):
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
                "cf_turnstile_response": "bad-token",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertEqual(len(mail.outbox), 0)
        mock_pending.assert_not_called()

    def test_extract_turnstile_token_prefers_form_field(self):
        request = MagicMock()
        request.POST = {"cf-turnstile-response": "from-cf"}
        self.assertEqual(extract_turnstile_token(request, "from-form"), "from-form")

    def test_extract_turnstile_token_falls_back_to_cloudflare_field(self):
        request = MagicMock()
        request.POST = {"cf-turnstile-response": "from-cf"}
        self.assertEqual(extract_turnstile_token(request, ""), "from-cf")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
        TURNSTILE_SITE_KEY="site",
        TURNSTILE_SECRET_KEY="secret",
    )
    @patch("apps.contact.views.create_pending_submission")
    @patch("apps.contact.views.verify_turnstile_token", return_value=(True, ""))
    def test_cloudflare_field_name_token_reaches_verifier(self, mock_verify, mock_pending):
        mock_pending.return_value = _pending_record()
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
                "cf-turnstile-response": "token-from-widget",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        mock_verify.assert_called_once()
        self.assertEqual(mock_verify.call_args.args[0], "token-from-widget")
        mock_pending.assert_called_once()

    @override_settings(TURNSTILE_SITE_KEY="site", TURNSTILE_SECRET_KEY="secret")
    @patch("apps.contact.turnstile.urllib.request.urlopen")
    def test_empty_token_skips_siteverify(self, mock_urlopen):
        ok, message = verify_turnstile_token("")
        self.assertFalse(ok)
        self.assertIn("security check", message.lower())
        mock_urlopen.assert_not_called()

    @override_settings(TURNSTILE_SITE_KEY="site", TURNSTILE_SECRET_KEY="secret")
    @patch("apps.contact.turnstile.urllib.request.urlopen")
    def test_valid_token_calls_siteverify(self, mock_urlopen):
        response = MagicMock()
        response.read.return_value = b'{"success": true}'
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response

        ok, message = verify_turnstile_token("valid-token", remote_ip="1.2.3.4")
        self.assertTrue(ok)
        self.assertEqual(message, "")
        mock_urlopen.assert_called_once()

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_ajax_submission_returns_validation_json_for_invalid_data(self):
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "R",
                "email": "invalid-email",
                "message": "Too short",
                "company": "",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
    )
    @patch("apps.contact.views.create_pending_submission")
    def test_non_js_submission_redirects_with_verify_challenge(self, mock_pending):
        mock_pending.return_value = _pending_record()
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I want to discuss an API platform architecture engagement.",
                "company": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("open=contact", response["Location"])
        self.assertIn("verify=", response["Location"])

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        CONTACT_MIN_SUBMIT_INTERVAL_SECONDS=120,
    )
    @patch("apps.contact.views.create_pending_submission")
    def test_rate_limit_blocks_immediate_repeat_submission(self, mock_pending):
        mock_pending.return_value = _pending_record()
        payload = {
            "name": "Raju",
            "email": "raju@example.com",
            "message": "I would like to discuss a backend architecture engagement.",
            "company": "",
        }
        first = self.client.post(
            reverse("contact:submit"),
            data=payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        second = self.client.post(
            reverse("contact:submit"),
            data=payload,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
        CONTACT_MIN_SUBMIT_INTERVAL_SECONDS=120,
        TURNSTILE_SITE_KEY="",
        TURNSTILE_SECRET_KEY="",
    )
    @patch("apps.contact.otp.generate_otp", return_value="112233")
    @patch("apps.contact.views.deliver_submission", return_value=True)
    @patch("apps.contact.views.mark_submission_verified")
    @patch("apps.contact.views.create_pending_submission")
    def test_submit_cooldown_does_not_block_immediate_otp_verify(
        self, mock_pending, mock_mark, mock_deliver, _mock_otp
    ):
        mock_pending.return_value = _pending_record()
        mock_mark.return_value = MagicMock()
        start = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(start.status_code, 200)
        challenge_id = start.json()["challenge_id"]

        verify = self.client.post(
            reverse("contact:verify-otp"),
            data={"challenge_id": challenge_id, "otp": "112233"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["success"])
        mock_mark.assert_called_once()
        mock_deliver.assert_called_once()
        self.assertEqual(mail.outbox[0].subject, "Verify your email")


class ContactAdminTests(SimpleTestCase):
    def test_admin_search_and_filters_configured(self):
        self.assertIn("email", ContactSubmissionAdmin.search_fields)
        self.assertIn("public_id", ContactSubmissionAdmin.search_fields)
        self.assertIn("delivery_status", ContactSubmissionAdmin.list_filter)
        self.assertIn("confirmation_sent", ContactSubmissionAdmin.list_display)


class ContactEmailTemplateTests(SimpleTestCase):
    def test_otp_email_is_minimal(self):
        subject, body = build_otp_email(name="Raju", otp="123456", ttl_seconds=600)
        self.assertEqual(subject, "Verify your email")
        self.assertIn("123456", body)
        self.assertIn("Use this code to verify your email.", body)
        self.assertIn("Expires in 10 minutes.", body)
        self.assertIn("ignore this email", body.lower())
        self.assertNotIn("Hi Raju", body)

    def test_owner_email_layout(self):
        public_id = str(uuid4())
        payload = ContactPayload(
            name="Raju",
            email="raju@example.com",
            subject="Contact - Portfolio",
            message="Hello there from the portfolio contact form.",
            ip_address="127.0.0.1",
            user_agent="test",
            public_id=public_id,
        )
        owner_subject, owner_body = build_owner_notification(
            payload, sent_at="2026-09-13 15:00 IST"
        )
        self.assertEqual(owner_subject, "Contact - Portfolio")
        self.assertIn("Name: Raju", owner_body)
        self.assertIn("Email: raju@example.com", owner_body)
        self.assertIn("Message:\nHello there from the portfolio contact form.", owner_body)
        self.assertIn("Timestamp: 2026-09-13 15:00 IST", owner_body)
        self.assertIn(f"Submission UUID: {public_id}", owner_body)
        self.assertNotIn("Thanks for reaching out", owner_body)


class ContactOtpChallengeTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_challenge_id_persists_and_verifies_immediately(self):
        submission_id = str(uuid4())
        challenge_id, otp = create_challenge(
            submission_id=submission_id,
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        self.assertTrue(challenge_id)
        challenge, error = verify_challenge(challenge_id, otp)
        self.assertEqual(error, "")
        self.assertIsNotNone(challenge)
        self.assertEqual(challenge.challenge_id, challenge_id)
        self.assertEqual(challenge.submission_id, submission_id)
        self.assertTrue(challenge.expires_at > challenge.created_at)

    def test_challenge_is_single_use(self):
        challenge_id, otp = create_challenge(
            submission_id=str(uuid4()),
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        first, _ = verify_challenge(challenge_id, otp)
        second, error = verify_challenge(challenge_id, otp)
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertIn("expired", error.lower())

    def test_expired_challenge_rejected(self):
        challenge_id, otp = create_challenge(
            submission_id=str(uuid4()),
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        raw = cache.get(f"contact-otp:{challenge_id}")
        raw["expires_at"] = raw["created_at"] - 1
        cache.set(f"contact-otp:{challenge_id}", raw, timeout=60)
        challenge, error = verify_challenge(challenge_id, otp)
        self.assertIsNone(challenge)
        self.assertIn("expired", error.lower())

    def test_unknown_challenge_id_is_expired(self):
        challenge, error = verify_challenge("missingchallengeid", "123456")
        self.assertIsNone(challenge)
        self.assertIn("expired", error.lower())

    def test_cache_persistence_allows_immediate_verify(self):
        challenge_id, otp = create_challenge(
            submission_id=str(uuid4()),
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        raw = cache.get(f"contact-otp:{challenge_id}")
        self.assertIsInstance(raw, dict)
        self.assertEqual(raw["challenge_id"], challenge_id)
        challenge, error = verify_challenge(challenge_id, otp)
        self.assertEqual(error, "")
        self.assertIsNotNone(challenge)

    def test_duplicate_verify_rejected_after_success(self):
        challenge_id, otp = create_challenge(
            submission_id=str(uuid4()),
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test",
        )
        first, err1 = verify_challenge(challenge_id, otp)
        second, err2 = verify_challenge(challenge_id, otp)
        self.assertEqual(err1, "")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertIn("expired", err2.lower())


class ContactPersistenceServiceTests(SimpleTestCase):
    @patch("apps.contact.services.ContactSubmission.objects.create")
    def test_create_pending_submission_after_turnstile(self, mock_create):
        mock_create.return_value = _pending_record()
        record = create_pending_submission(
            name="Raju",
            email="raju@example.com",
            subject=CONTACT_EMAIL_SUBJECT,
            message="I would like to discuss a backend architecture engagement.",
            ip_address="127.0.0.1",
            user_agent="test-agent",
            turnstile_verified=True,
        )
        mock_create.assert_called_once()
        kwargs = mock_create.call_args.kwargs
        self.assertFalse(kwargs["otp_verified"])
        self.assertTrue(kwargs["turnstile_verified"])
        self.assertEqual(kwargs["delivery_status"], DeliveryStatus.PENDING)
        self.assertTrue(record.turnstile_verified)

    @patch("apps.contact.services.ContactSubmission.objects.get")
    def test_mark_submission_verified_updates_existing_row(self, mock_get):
        public_id = uuid4()
        record = _pending_record(public_id=public_id)
        mock_get.return_value = record
        challenge = MagicMock(
            submission_id=str(public_id),
            turnstile_verified=True,
        )
        saved = mark_submission_verified(challenge)
        mock_get.assert_called_once_with(public_id=public_id)
        self.assertTrue(saved.otp_verified)
        record.save.assert_called_once()
        self.assertEqual(
            set(record.save.call_args.kwargs["update_fields"]),
            {"otp_verified", "turnstile_verified", "verified_at"},
        )

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    def test_deliver_submission_sends_owner_email_only(self):
        record = MagicMock()
        record.name = "Raju"
        record.email = "raju@example.com"
        record.subject = CONTACT_EMAIL_SUBJECT
        record.message = "I would like to discuss a backend architecture engagement."
        record.ip_address = "127.0.0.1"
        record.user_agent = "test"
        record.public_id = uuid4()
        notify_sent = deliver_submission(record)
        self.assertTrue(notify_sent)
        self.assertFalse(record.confirmation_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Contact - Portfolio")
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertIn(str(record.public_id), mail.outbox[0].body)


@override_settings(
    SECURE_SSL_REDIRECT=False,
    TURNSTILE_SITE_KEY="site",
    TURNSTILE_SECRET_KEY="secret",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    EMAIL_TO="owner@example.com",
    DEFAULT_FROM_EMAIL="portfolio@example.com",
)
class ContactEndToEndFlowTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

    @patch("apps.contact.otp.generate_otp", return_value="654321")
    @patch("apps.contact.views.verify_turnstile_token", return_value=(True, ""))
    @patch("apps.contact.views.deliver_submission", return_value=True)
    @patch("apps.contact.views.mark_submission_verified")
    @patch("apps.contact.views.create_pending_submission")
    def test_turnstile_otp_persist_deliver_pipeline(
        self, mock_pending, mock_mark, mock_deliver, mock_verify, _mock_otp
    ):
        pending = _pending_record()
        mock_pending.return_value = pending
        mock_mark.return_value = MagicMock()

        start = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
                "cf-turnstile-response": "live-token",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(start.status_code, 200)
        payload = start.json()
        self.assertTrue(payload["requires_otp"])
        self.assertEqual(payload["otp_expires_in_seconds"], 600)
        self.assertEqual(payload["submission_id"], str(pending.public_id))
        mock_verify.assert_called_once()
        self.assertEqual(mock_verify.call_args.args[0], "live-token")
        mock_pending.assert_called_once()
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("654321", mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].subject, "Verify your email")

        verify = self.client.post(
            reverse("contact:verify-otp"),
            data={"challenge_id": payload["challenge_id"], "otp": "654321"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(verify.status_code, 200)
        self.assertTrue(verify.json()["success"])
        mock_mark.assert_called_once()
        mock_deliver.assert_called_once()
        # One create on submit; verify updates — never create again.
        self.assertEqual(mock_pending.call_count, 1)
