import json

from django.conf import settings
from django.http import JsonResponse
from django.views import View

from .models import ChatbotLog
from .services import PortfolioChatService


class ChatbotReplyAPIView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        message = str(payload.get("message", "")).strip()
        if not message:
            return JsonResponse({"error": "Message is required."}, status=400)

        if len(message) > 1000:
            return JsonResponse({"error": "Message is too long."}, status=400)

        service = PortfolioChatService()
        reply = service.generate_reply(message)

        if settings.CHATBOT_STORE_LOGS:
            ChatbotLog.objects.create(
                provider=service.provider,
                user_message=message,
                assistant_response=reply,
            )

        return JsonResponse({"reply": reply, "provider": service.provider})
