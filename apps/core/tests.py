from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.core.markdown_loader import load_site_context

SHELL_MARKERS = (
    "docs-sidebar",
    "docs-mobile-header",
    "docs-footer",
    "chatbot-root",
    "command-palette",
    "search-index-data",
)


class HomePageTests(TestCase):
    def test_home_page_renders_markdown_sections(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Raju Jha")
        self.assertContains(response, 'id="about"')
        self.assertNotContains(response, 'data-section="contact"')
        self.assertContains(response, "SyncWave")
        self.assertContains(response, "spa-config-gen")

    def test_home_includes_search_index(self):
        response = self.client.get(reverse("core:home"))
        self.assertContains(response, "search-index-data")
        site = load_site_context()
        self.assertGreater(len(site.search_index), 5)

    def test_health_check_reports_database_disabled(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["database"], "disabled")
        self.assertEqual(payload["status"], "ok")


@override_settings(DEBUG=False)
class RuntimeErrorPageTests(TestCase):
    NOT_FOUND_URLS = (
        "/random-page",
        "/abc",
        "/projects-that-do-not-exist",
        "/this-route-should-never-exist",
    )

    def _assert_app_shell(self, response, status_code):
        for marker in SHELL_MARKERS:
            self.assertContains(response, marker, status_code=status_code)

    def test_404_urls_return_shell_with_content_pane(self):
        for url in self.NOT_FOUND_URLS:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, "errors/error_page.html")
                self.assertTemplateUsed(response, "core/docs_layout.html")
                self._assert_app_shell(response, 404)
                self.assertContains(response, "Page not found", status_code=404)
                self.assertContains(response, "outdated link", status_code=404)
                self.assertContains(response, "Return Home", status_code=404)
                self.assertNotContains(response, "django-debug", status_code=404)

    def test_error_page_sidebar_links_point_to_home_sections(self):
        response = self.client.get("/missing-page")
        self.assertEqual(response.status_code, 404)
        for section_id in ("about", "experience", "projects", "opensource", "skills"):
            self.assertContains(response, f'href="/#{section_id}"', status_code=404)
        self.assertContains(response, 'data-contact-nav', status_code=404)

    def test_offline_page_renders_in_app_shell(self):
        response = self.client.get(reverse("core:offline"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/offline.html")
        self.assertTemplateUsed(response, "core/docs_layout.html")
        self._assert_app_shell(response, 200)
        self.assertContains(response, "<h1>Offline</h1>")
        self.assertContains(response, "Reconnect to the internet")

    def test_csrf_failure_uses_shell_error_page(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("contact:submit"), {})
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/error_page.html")
        self.assertTemplateUsed(response, "core/docs_layout.html")
        self._assert_app_shell(response, 403)
        self.assertContains(response, "Access denied", status_code=403)
        self.assertContains(response, "CSRF verification failed", status_code=403)

    def test_csrf_failure_with_invalid_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("contact:submit"),
            {"name": "Test", "email": "test@example.com", "subject": "Hello", "message": "one two three four five"},
            HTTP_X_CSRFTOKEN="invalid-token",
        )
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/error_page.html")

    def test_debug_raise_500_hidden_when_gate_disabled(self):
        response = self.client.get(reverse("core:debug-raise-500"))
        self.assertEqual(response.status_code, 404)

    @override_settings(DEBUG=False, ENABLE_ERROR_TEST_ROUTES=True)
    def test_500_handler_uses_shell_error_page(self):
        self.client.raise_request_exception = False
        with self.assertLogs("django.request", level="ERROR"):
            response = self.client.get(reverse("core:debug-raise-500"))
        self.assertEqual(response.status_code, 500)
        self.assertTemplateUsed(response, "errors/error_page.html")
        self.assertTemplateUsed(response, "core/docs_layout.html")
        self._assert_app_shell(response, 500)
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertContains(response, "Return Home", status_code=500)
        self.assertNotContains(response, "RuntimeError", status_code=500)

    def test_service_worker_caches_shell_assets(self):
        response = self.client.get(reverse("core:service-worker"))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("rj-portfolio-shell-v4", body)
        self.assertIn("/static/js/docs.js", body)
        self.assertIn("/static/js/chatbot.js", body)
        self.assertEqual(response["Cache-Control"], "no-cache")

    def test_manifest_fields_present(self):
        import json
        from pathlib import Path

        from django.conf import settings

        manifest_path = Path(settings.BASE_DIR) / "static" / "manifest.webmanifest"
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["start_url"], "/")
        self.assertEqual(payload["display"], "standalone")
        self.assertEqual(payload["theme_color"], "#09090b")
        self.assertGreaterEqual(len(payload.get("icons", [])), 2)
