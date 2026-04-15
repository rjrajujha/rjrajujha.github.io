from django.urls import path

from .views import ContactSubmitView

app_name = "contact"

urlpatterns = [
    path("submit/", ContactSubmitView.as_view(), name="submit"),
]
