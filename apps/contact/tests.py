from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ContactForm
from .models import ContactSubmission


class ContactFormTests(TestCase):
    def test_honeypot_blocks_spam(self):
        form = ContactForm(
            data={
                "name": "Spam",
                "email": "spam@example.com",
                "subject": "Spam",
                "message": "This is a fake message with enough words.",
                "company": "bot-filled",
            }
        )
        self.assertFalse(form.is_valid())


class ContactViewTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_valid_submission_is_saved_and_emailed(self):
        response = self.client.post(
            reverse("contact:submit"),
            data={
                "name": "Raju",
                "email": "raju@example.com",
                "subject": "Project Collaboration",
                "message": "I would like to discuss a backend architecture engagement.",
                "company": "",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactSubmission.objects.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
