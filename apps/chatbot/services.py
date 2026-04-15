from __future__ import annotations

import json
import logging
from urllib import error, request

from django.conf import settings

from apps.core.content import EXPERIENCE_ITEMS, PROFILE, SKILL_GROUPS
from apps.projects.models import Project

logger = logging.getLogger(__name__)


class PortfolioChatService:
    def __init__(self) -> None:
        self.provider = settings.CHATBOT_PROVIDER
        self.timeout = settings.CHATBOT_TIMEOUT_SECONDS

    def generate_reply(self, user_message: str) -> str:
        clean_message = user_message.strip()
        if not clean_message:
            return "Ask a question about my experience, projects, or technical strengths and I will help."

        prompt = self._system_prompt()
        if self.provider == "openai":
            ai_reply = self._openai_reply(prompt, clean_message)
            if ai_reply:
                return ai_reply
        elif self.provider == "ollama":
            ai_reply = self._ollama_reply(prompt, clean_message)
            if ai_reply:
                return ai_reply

        return self._fallback_reply(clean_message)

    def _system_prompt(self) -> str:
        skills_flat = ", ".join(
            skill for category in SKILL_GROUPS for skill in category["items"]
        )
        experiences = "\n".join(
            f"- {item['role']} at {item['company']} ({item['period']}): {item['summary']}"
            for item in EXPERIENCE_ITEMS
        )
        projects = "\n".join(self._project_lines())

        return (
            "You are a concise and helpful portfolio assistant for software engineer Raju Jha. "
            "Answer with confidence, keep responses practical, and anchor details in real portfolio data.\n\n"
            f"Profile: {PROFILE['headline']}\n"
            f"Location: {PROFILE['location']}\n"
            f"Skills: {skills_flat}\n\n"
            f"Experience:\n{experiences}\n\n"
            f"Projects:\n{projects}\n\n"
            "If a question is outside portfolio scope, politely say so and invite a project-specific question."
        )

    def _project_lines(self) -> list[str]:
        try:
            projects = list(Project.objects.all()[:8])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load projects for chatbot context: %s", exc)
            projects = []
        if not projects:
            return [
                "- Influencer Marketing Platform: full-stack campaign lifecycle platform with API-driven analytics.",
                "- WhatsApp Automation Server: automation workflows, scheduling, and real-time messaging updates.",
                "- Custom DNS Deployment: secure DNS with DoH/DoT and operational monitoring.",
            ]

        return [
            f"- {project.title}: {project.headline}. Stack: {project.tech_stack}."
            for project in projects
        ]

    def _openai_reply(self, system_prompt: str, user_message: str) -> str | None:
        if not settings.OPENAI_API_KEY:
            logger.warning("CHATBOT_PROVIDER is openai but OPENAI_API_KEY is not configured")
            return None

        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
        }
        req = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except (error.URLError, error.HTTPError, KeyError, IndexError, ValueError) as exc:
            logger.exception("OpenAI chatbot request failed: %s", exc)
            return None

    def _ollama_reply(self, system_prompt: str, user_message: str) -> str | None:
        endpoint = f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
        payload = {
            "model": settings.OLLAMA_MODEL,
            "prompt": f"{system_prompt}\n\nUser: {user_message}\nAssistant:",
            "stream": False,
        }
        req = request.Request(
            url=endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
            return data.get("response", "").strip() or None
        except (error.URLError, error.HTTPError, ValueError) as exc:
            logger.exception("Ollama chatbot request failed: %s", exc)
            return None

    def _fallback_reply(self, user_message: str) -> str:
        lowered = user_message.lower()

        if any(keyword in lowered for keyword in ["skill", "stack", "technology", "tech"]):
            top_skills = ", ".join(SKILL_GROUPS[0]["items"] + SKILL_GROUPS[2]["items"][:3])
            return (
                f"Raju's strongest backend stack includes {top_skills}. "
                "He also works with AI tooling and production DevOps workflows."
            )

        if any(keyword in lowered for keyword in ["experience", "work", "company", "career"]):
            current = EXPERIENCE_ITEMS[0]
            return (
                f"He is currently {current['role']} at {current['company']} ({current['period']}). "
                "His focus is shipping scalable product features and improving API performance."
            )

        if any(keyword in lowered for keyword in ["project", "portfolio", "built"]):
            return (
                "Highlighted work includes an Influencer Marketing Platform, a WhatsApp Automation Server, "
                "and a secure Custom DNS deployment."
            )

        if any(keyword in lowered for keyword in ["contact", "hire", "reach"]):
            return (
                "You can reach Raju through the contact form on this site or via LinkedIn and email listed in the hero section."
            )

        return (
            "I can help with details about Raju's projects, engineering experience, architecture approach, and technical strengths. "
            "Ask a specific question and I will answer directly."
        )
