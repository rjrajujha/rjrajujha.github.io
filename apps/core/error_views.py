from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


ERROR_CONFIG: dict[int, dict[str, str]] = {
    400: {
        "title": "Bad Request",
        "heading": "Request could not be processed",
        "description": "The request appears malformed or incomplete. Please retry from a valid page.",
        "hint": "If this keeps happening, refresh the page and submit again.",
    },
    403: {
        "title": "Forbidden",
        "heading": "Access denied",
        "description": "You do not have permission to access this resource.",
        "hint": "Check your account permissions or return to the homepage.",
    },
    404: {
        "title": "Not Found",
        "heading": "Page not found",
        "description": "The page you requested does not exist or may have been moved.",
        "hint": "Use the navigation links or return to the main portfolio page.",
    },
    500: {
        "title": "Server Error",
        "heading": "Something went wrong on our side",
        "description": "An unexpected server error occurred while processing your request.",
        "hint": "Please try again in a moment. If the issue continues, use the contact section.",
    },
}


def _render_error(request: HttpRequest, status_code: int) -> HttpResponse:
    config = ERROR_CONFIG[status_code]
    return render(
        request,
        "errors/error_page.html",
        {
            "error_code": status_code,
            "error_title": config["title"],
            "error_heading": config["heading"],
            "error_description": config["description"],
            "error_hint": config["hint"],
        },
        status=status_code,
    )


def bad_request(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 400)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 403)


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:  # noqa: ARG001
    return _render_error(request, 404)


def server_error(request: HttpRequest) -> HttpResponse:
    return _render_error(request, 500)
