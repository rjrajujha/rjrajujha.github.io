from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ContactForm


class ContactFormTests(TestCase):
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


@override_settings(SECURE_SSL_REDIRECT=False)
class ContactViewTests(TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        EMAIL_HOST_USER="portfolio@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    def test_valid_submission_sends_emails(self):
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertEqual(mail.outbox[0].reply_to, ["raju@example.com"])
        self.assertIn("[Portfolio Contact] Message from Raju", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[1].to, ["raju@example.com"])
        self.assertIn("Thank you for reaching out.", mail.outbox[1].body)
        self.assertIn("as soon as possible", mail.outbox[1].body)
        self.assertIn("Thanks,\nRaju Jha", mail.outbox[1].body)
        self.assertNotIn("— Raju Jha", mail.outbox[1].body)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        EMAIL_HOST_USER="portfolio@example.com",
        DEFAULT_FROM_EMAIL="portfolio@example.com",
    )
    def test_ajax_submission_returns_success_json(self):
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "message": "I want to discuss an API platform architecture engagement.",
                "company": "",
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertTrue(payload["email_sent"])

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
        payload = response.json()
        self.assertFalse(payload["success"])
        self.assertIn("errors", payload)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_non_js_submission_redirects_to_contact_modal_query(self):
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

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_TO="owner@example.com",
        CONTACT_MIN_SUBMIT_INTERVAL_SECONDS=120,
    )
    def test_rate_limit_blocks_immediate_repeat_submission(self):
        payload = {
            "name": "Raju",
            "email": "raju@example.com",
            "message": "I would like to discuss a backend architecture engagement.",
            "company": "",
        }

        first = self.client.post(reverse("contact:submit"), data=payload, follow=True)
        second = self.client.post(reverse("contact:submit"), data=payload, follow=True)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)
