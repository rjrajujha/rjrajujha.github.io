from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_renders_featured_projects(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SyncWave")
        self.assertContains(response, "spa-config-gen")

    def test_health_check_reports_database_disabled(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["database"], "disabled")
        self.assertEqual(payload["status"], "ok")
