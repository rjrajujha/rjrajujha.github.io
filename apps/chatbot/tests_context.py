from django.test import SimpleTestCase

from .context_memory import build_conversation_context, find_entity_in_text


class ConversationContextTests(SimpleTestCase):
    def test_find_entity_in_text_detects_syncwave(self):
        self.assertEqual(find_entity_in_text("Tell me about SyncWave"), "SyncWave")

    def test_follow_up_enriches_message_with_focus_entity(self):
        history = [
            {"role": "user", "content": "Tell me about spa-config-gen"},
            {"role": "assistant", "content": "spa-config-gen generates SPA routing configs."},
        ]
        context = build_conversation_context("What stack does it use?", history)
        self.assertEqual(context.focus_entity, "spa-config-gen")
        self.assertIn("spa-config-gen", context.enriched_message)
