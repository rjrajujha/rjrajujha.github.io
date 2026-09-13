import os
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from portfolio.database_config import build_databases, database_apps


class DatabaseConfigTests(SimpleTestCase):
    def test_database_apps_include_admin_stack(self):
        self.assertIn("django.contrib.admin", database_apps())

    def test_build_from_database_url(self):
        url = "postgresql://user:pass@db.example.supabase.co:5432/postgres"
        with patch.dict(os.environ, {"DATABASE_URL": url}, clear=True):
            default = build_databases()["default"]
        self.assertEqual(default["ENGINE"], "django.db.backends.postgresql")
        self.assertEqual(default["HOST"], "db.example.supabase.co")

    def test_rejects_sqlite_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///tmp/db.sqlite3"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                build_databases()

    def test_missing_config_raises_outside_tests(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("portfolio.database_config._is_test_run", return_value=False):
                with self.assertRaises(ImproperlyConfigured):
                    build_databases()
