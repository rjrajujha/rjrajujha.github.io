from django.shortcuts import redirect
from django.views import View

from apps.core.markdown_loader import load_site_context


def _section_for_category(category: str) -> str:
    if category == "infrastructure":
        return "infrastructure"
    return "opensource"


class ProjectListView(View):
    def get(self, request, *args, **kwargs):
        return redirect("/#opensource")


class ProjectDetailView(View):
    def get(self, request, slug="", *args, **kwargs):
        target = (slug or "").strip().lower()
        site = load_site_context()
        for project in site.opensource_projects + site.infrastructure_projects:
            if project.slug == target:
                section = _section_for_category(project.category)
                return redirect(f"/#{section}#{project.slug}")
        return redirect("/#opensource")
