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

    def test_email_secure_protocol_ssl(self):
        with patch.dict(project_settings.os.environ, {"EMAIL_SECURE_PROTOCOL": "ssl"}, clear=False):
            use_ssl, use_tls = project_settings.resolve_email_secure_flags("ssl")
            self.assertTrue(use_ssl)
            self.assertFalse(use_tls)

    def test_email_secure_protocol_tls(self):
        with patch.dict(project_settings.os.environ, {"EMAIL_SECURE_PROTOCOL": "tls"}, clear=False):
            use_ssl, use_tls = project_settings.resolve_email_secure_flags("tls")
            self.assertFalse(use_ssl)
            self.assertTrue(use_tls)

    def test_email_secure_protocol_none(self):
        with patch.dict(project_settings.os.environ, {"EMAIL_SECURE_PROTOCOL": "none"}, clear=False):
            use_ssl, use_tls = project_settings.resolve_email_secure_flags("none")
            self.assertFalse(use_ssl)
            self.assertFalse(use_tls)

    def test_email_secure_protocol_invalid_falls_back_by_port(self):
        with patch.dict(
            project_settings.os.environ,
            {"EMAIL_SECURE_PROTOCOL": "invalid", "EMAIL_PORT": "587"},
            clear=False,
        ):
            self.assertEqual(project_settings.resolve_email_secure_protocol(587), "tls")

    def test_email_secure_protocol_defaults_by_port(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("EMAIL_SECURE_PROTOCOL", None)
            self.assertEqual(project_settings.resolve_email_secure_protocol(465), "ssl")
            self.assertEqual(project_settings.resolve_email_secure_protocol(587), "tls")

    def test_is_production_defaults_false_in_local_context(self):
        with patch.dict(project_settings.os.environ, {}, clear=False):
            project_settings.os.environ.pop("DJANGO_ENV", None)
            project_settings.os.environ.pop("DJANGO_PRODUCTION", None)
            self.assertFalse(project_settings.resolve_is_production(False))

    def test_is_production_true_for_production_env(self):
        with patch.dict(project_settings.os.environ, {"DJANGO_ENV": "production"}, clear=False):
            project_settings.os.environ.pop("DJANGO_PRODUCTION", None)
            self.assertTrue(project_settings.resolve_is_production(False))

    def test_is_production_respects_explicit_override(self):
        with patch.dict(
            project_settings.os.environ,
            {"DJANGO_ENV": "production", "DJANGO_PRODUCTION": "false"},
            clear=False,
        ):
            self.assertFalse(project_settings.resolve_is_production(False))

    def test_security_settings_enabled_only_for_production_without_debug(self):
        self.assertTrue(project_settings.should_enable_security(True, False))
        self.assertFalse(project_settings.should_enable_security(False, False))
        self.assertFalse(project_settings.should_enable_security(True, True))
