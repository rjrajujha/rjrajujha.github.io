from django.conf import settings
from django.db import connections
from django.db.utils import DatabaseError
from django.http import JsonResponse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from .markdown_loader import load_site_context
from .page_context import build_site_page_context


class HomePageView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(build_site_page_context(self.request))
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
            "service": "rjrajujha-engineering-profile",
        }
        return JsonResponse(payload, status=200)


class OfflinePageView(TemplateView):
    template_name = "core/offline.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            build_site_page_context(
                self.request,
                page_title=f"Offline | {load_site_context().name}",
                page_description="You appear to be offline.",
            )
        )
        return context


class ServiceWorkerView(TemplateView):
    template_name = "pwa/service-worker.js"
    content_type = "application/javascript"

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, content_type=self.content_type, **response_kwargs)
        response["Service-Worker-Allowed"] = "/"
        response["Cache-Control"] = "no-cache"
        return response


class DebugRaise500View(View):
    """Gated test endpoint for production error-page verification only."""

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if not getattr(settings, "ENABLE_ERROR_TEST_ROUTES", False):
            from django.http import Http404

            raise Http404()
        raise RuntimeError("Test exception")
