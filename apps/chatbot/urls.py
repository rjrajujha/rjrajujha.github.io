from django.urls import path

from .views import ChatbotReplyAPIView

app_name = "chatbot"

urlpatterns = [
    path("api/chat/", ChatbotReplyAPIView.as_view(), name="api-chat"),
]
