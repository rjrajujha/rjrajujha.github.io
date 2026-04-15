from django.test import TestCase

from .models import Project


class ProjectModelTests(TestCase):
    def test_stack_items_splits_comma_values(self):
        project = Project(
            title="Demo",
            slug="demo",
            headline="Demo headline",
            description="Description",
            tech_stack="Python, Django, TailwindCSS",
        )

        self.assertEqual(project.stack_items, ["Python", "Django", "TailwindCSS"])
