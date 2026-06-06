import os

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .resume_access import try_resume_access_reply
from .services import PortfolioChatService


@override_settings(SECURE_SSL_REDIRECT=False, DEBUG=False)
class ChatbotApiTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_chatbot_reply_api_returns_json(self):
        response = self.client.post(
            reverse("chatbot:api-chat"),
            data='{"message": "Tell me about your backend skills"}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("reply", response.json())
        self.assertNotIn("provider", response.json())
        self.assertNotIn("fallback", response.json())

    def test_chatbot_profile_links_response_contains_required_urls(self):
        service = PortfolioChatService()
        reply = service.generate_reply("Share github and linkedin profile links and hiring summary")

        self.assertIn("https://github.com/rjrajujha", reply)
        self.assertIn("https://linkedin.com/in/rjrajujha", reply)
        self.assertFalse(reply.endswith("..."))
        self.assertIn(reply[-1], {".", "!", "?"})

    def test_chatbot_skills_reply_includes_expected_stack_items(self):
        service = PortfolioChatService()
        reply = service.generate_reply("What is Raju's backend and full-stack skill set?")

        self.assertIn("Python", reply)
        self.assertIn("Django", reply)
        self.assertIn("Java", reply)
        self.assertIn("Spring Boot", reply)
        self.assertIn("React", reply)
        self.assertIn("Next.js", reply)

    def test_chatbot_architecture_and_ai_reply_is_complete(self):
        service = PortfolioChatService()
        reply = service.generate_reply("How does Raju approach backend architecture and AI integrations?")

        self.assertIn("API", reply)
        self.assertIn("automation", reply.lower())
        self.assertIn("AI", reply)
        self.assertFalse(reply.endswith("..."))

    def test_chatbot_reply_hides_internal_mode_labels(self):
        service = PortfolioChatService()
        reply = service.generate_reply("Give a local knowledge mode summary with profile links.")

        self.assertNotIn("local knowledge mode", reply.lower())
        self.assertIn("https://github.com/rjrajujha", reply)
        self.assertIn("https://linkedin.com/in/rjrajujha", reply)

    def test_natural_language_owner_and_projects_queries(self):
        service = PortfolioChatService()
        owner_reply = service.generate_reply("tell me about owner")
        self.assertIn("Raju", owner_reply)
        projects_reply = service.generate_reply("what projects have you built")
        self.assertTrue(
            "SyncWave" in projects_reply
            or "spa-config-gen" in projects_reply
            or "project" in projects_reply.lower()
        )

    def test_follow_up_question_uses_conversation_context_for_syncwave(self):
        service = PortfolioChatService()
        history = [
            {"role": "user", "content": "Tell me about SyncWave"},
            {
                "role": "assistant",
                "content": "SyncWave is a local-first synchronized audio app with Flutter and FastAPI.",
            },
        ]
        reply = service.generate_reply("What technologies does it use?", history=history)
        self.assertIn("SyncWave", reply)
        self.assertTrue(
            any(term in reply for term in ("Flutter", "FastAPI", "Dart", "WebSocket")),
            msg=reply,
        )

    @override_settings(CHATBOT_MIN_SUBMIT_INTERVAL_SECONDS=60)
    def test_chatbot_rate_limit_blocks_rapid_repeat_request(self):
        payload = '{"message": "Tell me about backend architecture strengths."}'
        first = self.client.post(reverse("chatbot:api-chat"), data=payload, content_type="application/json")
        second = self.client.post(reverse("chatbot:api-chat"), data=payload, content_type="application/json")

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)


class ResumeSecretStrictTests(TestCase):
    expected_link = "http://rajujha.dev/resume/?id=latest&key=7596f075702dbdb745d7dccbaf4d5a79259"

    def setUp(self):
        self._env = os.environ.copy()
        os.environ["RESUME_SECRET_KEY"] = "RESUME-LINK"
        os.environ["RESUME_URL"] = "http://rajujha.dev/resume/?id=latest"
        os.environ["RESUME_ACCESS_KEY"] = "7596f075702dbdb745d7dccbaf4d5a79259"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_exact_secret_returns_resume_url(self):
        reply = try_resume_access_reply("RESUME-LINK")
        self.assertIsNotNone(reply)
        self.assertIn(self.expected_link, reply)

        service = PortfolioChatService()
        service_reply = service.generate_reply("RESUME-LINK")
        self.assertIn(self.expected_link, service_reply)

    def test_variations_do_not_return_resume_url(self):
        failures = (
            "resume-link",
            "Resume-Link",
            "My RESUME-LINK",
            "RESUME-LINK please",
            "Show RESUME-LINK",
            "Give RESUME-LINK",
            "RESUME-LINK of owner",
            "RESUME-LINK?",
            " RESUME-LINK",
            "RESUME-LINK ",
        )
        for phrase in failures:
            with self.subTest(phrase=phrase):
                self.assertIsNone(try_resume_access_reply(phrase))
                reply = PortfolioChatService().generate_reply(phrase)
                self.assertNotIn(self.expected_link, reply)
