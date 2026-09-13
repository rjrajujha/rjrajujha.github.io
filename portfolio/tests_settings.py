from unittest.mock import patch

from django.test import SimpleTestCase

from portfolio import settings as project_settings


class SettingsResolverTests(SimpleTestCase):
    def test_email_backend_defaults_to_smtp_when_env_missing(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("EMAIL_BACKEND", None)
            self.assertEqual(
                project_settings.resolve_email_backend(),
                "django.core.mail.backends.smtp.EmailBackend",
            )

    def test_email_backend_uses_env_value(self):
        with patch.dict(
            project_settings.os.environ,
            {"EMAIL_BACKEND": "django.core.mail.backends.console.EmailBackend"},
            clear=False,
        ):
            self.assertEqual(
                project_settings.resolve_email_backend(),
                "django.core.mail.backends.console.EmailBackend",
            )

    def test_contact_interval_defaults_to_45_when_env_missing(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("CONTACT_MIN_SUBMIT_INTERVAL_SECONDS", None)
            self.assertEqual(project_settings.resolve_contact_min_submit_interval(), 45)

    def test_contact_interval_uses_env_override(self):
        with patch.dict(
            project_settings.os.environ,
            {"CONTACT_MIN_SUBMIT_INTERVAL_SECONDS": "120"},
            clear=False,
        ):
            self.assertEqual(project_settings.resolve_contact_min_submit_interval(), 120)

    def test_contact_interval_invalid_value_falls_back_safely(self):
        with patch.dict(
            project_settings.os.environ,
            {"CONTACT_MIN_SUBMIT_INTERVAL_SECONDS": "invalid"},
            clear=False,
        ):
            self.assertEqual(project_settings.resolve_contact_min_submit_interval(), 45)

    def test_chatbot_interval_defaults_to_2_when_env_missing(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS", None)
            self.assertEqual(project_settings.resolve_chatbot_min_submit_interval(), 2)

    def test_chatbot_interval_uses_env_override(self):
        with patch.dict(
            project_settings.os.environ,
            {"CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS": "8"},
            clear=False,
        ):
            self.assertEqual(project_settings.resolve_chatbot_min_submit_interval(), 8)

    def test_chatbot_model_uses_explicit_value(self):
        self.assertEqual(
            project_settings.resolve_chatbot_model("openai", "gpt-4.1-mini"),
            "gpt-4.1-mini",
        )

    def test_chatbot_model_defaults_by_provider(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("CHATBOT_MODEL", None)
            self.assertEqual(
                project_settings.resolve_chatbot_model("gemini", ""),
                "gemini-1.5-flash",
            )
            self.assertEqual(
                project_settings.resolve_chatbot_model("openai", ""),
                "gpt-4o-mini",
            )
            self.assertEqual(project_settings.resolve_chatbot_model("local", ""), "")

    def test_is_production_defaults_false_in_local_context(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("DJANGO_ENV", None)
            self.assertFalse(project_settings.resolve_is_production(False))

    def test_is_production_true_for_production_env(self):
        with patch.dict(project_settings.os.environ, {"DJANGO_ENV": "production"}, clear=False):
            self.assertTrue(project_settings.resolve_is_production(False))

    def test_is_production_false_for_development_env(self):
        with patch.dict(project_settings.os.environ, {"DJANGO_ENV": "development"}, clear=False):
            self.assertFalse(project_settings.resolve_is_production(True))

    def test_is_production_infers_from_vercel_when_env_unset(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("DJANGO_ENV", None)
            self.assertTrue(project_settings.resolve_is_production(True))

    def test_security_settings_enabled_only_for_production_without_debug(self):
        self.assertTrue(project_settings.should_enable_security(True, False))
        self.assertFalse(project_settings.should_enable_security(False, False))
        self.assertFalse(project_settings.should_enable_security(True, True))
