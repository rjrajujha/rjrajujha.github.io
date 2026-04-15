from django.test import TestCase
from django.urls import reverse


class ChatbotApiTests(TestCase):
    def test_chatbot_reply_api_returns_json(self):
        response = self.client.post(
            reverse("chatbot:api-chat"),
            data='{"message": "Tell me about your backend skills"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())
