from django.urls import path

from .views import HealthCheckView, HomePageView, OfflinePageView, ServiceWorkerView

app_name = "core"

urlpatterns = [
    path("health", HealthCheckView.as_view(), name="health"),
    path("offline/", OfflinePageView.as_view(), name="offline"),
    path("service-worker.js", ServiceWorkerView.as_view(), name="service-worker"),
    path("", HomePageView.as_view(), name="home"),
]
