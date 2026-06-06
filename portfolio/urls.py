from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve

handler400 = "apps.core.error_views.bad_request"
handler403 = "apps.core.error_views.permission_denied"
handler404 = "apps.core.error_views.page_not_found"
handler500 = "apps.core.error_views.server_error"

urlpatterns = [
    path("", include("apps.core.urls")),
    path("projects/", include("apps.projects.urls")),
    path("contact/", include("apps.contact.urls")),
    path("chatbot/", include("apps.chatbot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif not settings.IS_PRODUCTION:
    static_source_root = settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else settings.STATIC_ROOT
    urlpatterns += [
        re_path(r"^static/(?P<path>.*)$", serve, {"document_root": static_source_root}),
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
