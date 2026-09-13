from django.test import SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(SECURE_SSL_REDIRECT=False)
class ProjectViewsTests(SimpleTestCase):
    def test_project_list_redirects_to_home_anchor(self):
        response = self.client.get(reverse("projects:list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/#opensource")

    def test_project_detail_redirects_to_opensource_anchor(self):
        response = self.client.get(reverse("projects:detail", kwargs={"slug": "syncwave"}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/#opensource#syncwave")

    def test_project_detail_unknown_slug_redirects_to_opensource(self):
        response = self.client.get(reverse("projects:detail", kwargs={"slug": "missing"}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/#opensource")
