from django.test import TestCase
from django.urls import reverse


class ProjectViewsTests(TestCase):
    def test_project_list_renders_open_source_projects(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SyncWave")
        self.assertContains(response, "spa-config-gen")

    def test_project_detail_resolves_syncwave_slug(self):
        response = self.client.get(reverse("projects:detail", kwargs={"slug": "syncwave"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SyncWave")
