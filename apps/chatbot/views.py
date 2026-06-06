import json

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone
from django.views import View

from .services import PortfolioChatService


class ChatbotReplyAPIView(View):
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if self._is_rate_limited(request):
            return JsonResponse(
                {"error": "Please wait a moment before sending another message."},
                status=429,
            )

        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid JSON payload."}, status=400)

        raw_message = str(payload.get("message", ""))
        if not raw_message.strip():
            return JsonResponse({"error": "Message is required."}, status=400)

        if len(raw_message) > 1000:
            return JsonResponse({"error": "Message is too long."}, status=400)

        history = payload.get("history", [])
        if not isinstance(history, list):
            history = []

        service = PortfolioChatService()
        reply = service.generate_reply(raw_message, history=history)

        response_payload = {"reply": reply}
        if settings.DEBUG:
            response_payload.update(
                {
                    "provider": service.active_provider,
                    "fallback": service.active_provider == "local",
                }
            )
        return JsonResponse(response_payload)

    def _is_rate_limited(self, request) -> bool:
        interval = max(int(settings.CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS), 1)
        cache_key = f"chatbot-rate-limit:{self._client_ip(request)}"
        now_ts = int(timezone.now().timestamp())
        last_ts = cache.get(cache_key)
        if last_ts and now_ts - int(last_ts) < interval:
            return True
        cache.set(cache_key, now_ts, timeout=interval * 2)
        return False

    @staticmethod
    def _client_ip(request) -> str:
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return (request.META.get("REMOTE_ADDR") or "unknown").strip()
