import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from portfolio.email_config import resolve_email_security


class EmailSecurityResolverTests(SimpleTestCase):
    def _resolve(self, env: dict):
        with patch.dict(os.environ, env, clear=True):
            return resolve_email_security()

    def test_security_ssl(self):
        resolved = self._resolve({"EMAIL_USE_SECURITY": "ssl"})
        self.assertEqual(resolved.mode, "ssl")
        self.assertTrue(resolved.use_ssl)
        self.assertEqual(resolved.port, 465)

    def test_security_tls(self):
        resolved = self._resolve({"EMAIL_USE_SECURITY": "tls"})
        self.assertEqual(resolved.mode, "tls")
        self.assertTrue(resolved.use_tls)
        self.assertEqual(resolved.port, 587)

    def test_security_plain(self):
        resolved = self._resolve({"EMAIL_USE_SECURITY": "plain"})
        self.assertEqual(resolved.mode, "plain")
        self.assertEqual(resolved.port, 25)

    def test_security_case_insensitive(self):
        self.assertEqual(self._resolve({"EMAIL_USE_SECURITY": "TLS"}).mode, "tls")
        self.assertEqual(self._resolve({"EMAIL_USE_SECURITY": "Ssl"}).mode, "ssl")

    def test_invalid_raises(self):
        with self.assertRaises(ImproperlyConfigured):
            self._resolve({"EMAIL_USE_SECURITY": "smtp"})
