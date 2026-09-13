from unittest.mock import patch

from django.test import SimpleTestCase

from portfolio.cache_config import CACHE_TABLE, build_caches


class CacheConfigTests(SimpleTestCase):
    def test_tests_use_locmem_cache(self):
        caches = build_caches()
        self.assertEqual(
            caches["default"]["BACKEND"],
            "django.core.cache.backends.locmem.LocMemCache",
        )

    def test_production_uses_database_cache(self):
        with patch("portfolio.cache_config._is_test_run", return_value=False):
            caches = build_caches()
        self.assertEqual(
            caches["default"]["BACKEND"],
            "django.core.cache.backends.db.DatabaseCache",
        )
        self.assertEqual(caches["default"]["LOCATION"], CACHE_TABLE)
