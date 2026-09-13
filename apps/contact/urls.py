from django.urls import path

from .views import ContactSubmitView, ContactVerifyOtpView

app_name = "contact"

urlpatterns = [
    path("submit/", ContactSubmitView.as_view(), name="submit"),
    path("verify-otp/", ContactVerifyOtpView.as_view(), name="verify-otp"),
]
