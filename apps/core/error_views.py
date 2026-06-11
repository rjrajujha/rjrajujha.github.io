from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import requires_csrf_token

from apps.core.markdown_loader import load_site_context
from apps.core.page_context import build_site_page_context


ERROR_CONFIG: dict[int, dict[str, str]] = {
    400: {
        "title": "Bad Request",
        "heading": "Bad request",
        "description": "The request could not be processed.",
        "hint": "Please refresh the page and try again.",
    },
    403: {
        "title": "Forbidden",
        "heading": "Access denied",
        "description": "You do not have permission to access this resource.",
        "hint": "",
    },
    404: {
        "title": "Not Found",
        "heading": "Page not found",
        "description": "The page you requested does not exist.",
        "hint": "You may have followed an outdated link or entered an incorrect URL.",
    },
    500: {
        "title": "Server Error",
        "heading": "Something went wrong",
        "description": "An unexpected error occurred.",
        "hint": "Please try again later.",
    },
}


def _render_error(request: HttpRequest, status_code: int, *, hint: str | None = None) -> HttpResponse:
    config = ERROR_CONFIG[status_code]
    site = load_site_context()
    context = build_site_page_context(
        request,
        page_title=f"{status_code} {config['title']} | {site.name}",
        page_description=config["description"],
    )
    context.update(
        {
            "error_code": status_code,
            "error_title": config["title"],
            "error_heading": config["heading"],
            "error_description": config["description"],
            "error_hint": hint if hint is not None else config["hint"],
        }
    )
    return render(request, "errors/error_page.html", context, status=status_code)


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 400)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 403)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 404)


def server_error(request: HttpRequest) -> HttpResponse:
    return _render_error(request, 500)


@requires_csrf_token
def csrf_failure(request: HttpRequest, reason: str = "") -> HttpResponse:  # noqa: ARG001
    return _render_error(
        request,
        403,
        hint="CSRF verification failed. Refresh the page and try again.",
    )
