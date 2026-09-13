from django.test import SimpleTestCase, override_settings

from portfolio.supabase import (
    SupabaseNotConfigured,
    get_supabase_client,
    get_supabase_client_or_none,
    supabase_enabled,
)


class SupabaseHelpersTests(SimpleTestCase):
    def setUp(self):
        get_supabase_client.cache_clear()

    @override_settings(SUPABASE_URL="", SUPABASE_KEY="")
    def test_disabled_without_credentials(self):
        self.assertFalse(supabase_enabled())
        self.assertIsNone(get_supabase_client_or_none())
        with self.assertRaises(SupabaseNotConfigured):
            get_supabase_client()

    @override_settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_KEY="test-key")
    def test_enabled_with_credentials(self):
        self.assertTrue(supabase_enabled())
