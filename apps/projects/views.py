from django.http import Http404
from django.views.generic import DetailView, ListView

from .services import fallback_project_by_slug, load_projects


class ProjectListView(ListView):
    template_name = "projects/list.html"
    context_object_name = "projects"

    def get_queryset(self):
        return load_projects(featured_only=False)


class ProjectDetailView(DetailView):
    template_name = "projects/detail.html"
    context_object_name = "project"

    def get_object(self, queryset=None):
        project = fallback_project_by_slug(self.kwargs.get("slug", ""))
        if project:
            return project
        raise Http404("Project not found.")
