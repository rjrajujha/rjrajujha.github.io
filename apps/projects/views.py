from django.shortcuts import redirect
from django.views import View

from apps.core.markdown_loader import load_site_context


class ProjectListView(View):
    def get(self, request, *args, **kwargs):
        return redirect("/#projects")


class ProjectDetailView(View):
    def get(self, request, slug="", *args, **kwargs):
        target = (slug or "").strip().lower()
        site = load_site_context()
        for project in site.opensource_projects + site.work_projects:
            if project.slug == target:
                section = "opensource" if project.category == "opensource" else "projects"
                return redirect(f"/#{section}#{project.slug}")
        return redirect("/#projects")
