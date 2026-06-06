from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from apps.projects.services import load_projects

from .content import (
    ABOUT_POINTS,
    EXPERIENCE_ITEMS,
    PROFILE,
    SKILL_GROUPS,
)


class HomePageView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "profile": PROFILE,
                "about_points": ABOUT_POINTS,
                "skill_groups": SKILL_GROUPS,
                "experience_items": EXPERIENCE_ITEMS,
                "featured_projects": load_projects(featured_only=True, limit=6),
            }
        )
        return context


class HealthCheckView(View):
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        database = "disabled"
        status = "ok"

        if getattr(settings, "USE_DATABASE", False) and settings.DATABASES:
            database = "ok"
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
            except DatabaseError:
                database = "unavailable"
                status = "degraded"

        payload = {
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "database": database,
            "service": "rjrajujha-portfolio",
        }
        return JsonResponse(payload, status=200)


class OfflinePageView(TemplateView):
    template_name = "core/offline.html"


class ServiceWorkerView(TemplateView):
    template_name = "pwa/service-worker.js"
    content_type = "application/javascript"

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, content_type=self.content_type, **response_kwargs)
        response["Service-Worker-Allowed"] = "/"
        response["Cache-Control"] = "no-cache"
        return response
