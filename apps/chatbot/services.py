from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Protocol
from urllib import error, request

from django.conf import settings

from apps.core.content import (
    ABOUT_POINTS,
    ALL_PROJECTS,
    EXPERIENCE_ITEMS,
    PROFILE,
    SKILL_GROUPS,
)
from apps.chatbot.context_memory import build_conversation_context, get_project_by_title
from apps.chatbot.nlp import detect_intents, tokenize
from apps.chatbot.resume_access import try_resume_access_reply

logger = logging.getLogger(__name__)

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
INTERNAL_MODE_RE = re.compile(
    r"(?:^|\s)(?:local knowledge mode|provider:\s*\w+|fallback:\s*\w+)(?:\s|$)",
    re.I,
)
GITHUB_PROFILE_URL = "https://github.com/rjrajujha"
LINKEDIN_PROFILE_URL = "https://linkedin.com/in/rjrajujha"
LOCAL_PROFILE_SUMMARY = (
    "Raju Jha is a backend-heavy full-stack software engineer focused on Python and Django systems, "
    "production APIs, automation workflows, and practical AI integrations."
)
LOCAL_STACK_SUMMARY = (
    "Core technologies include Python, Django, FastAPI, Java, Spring Boot, React, Next.js, "
    "REST/GraphQL APIs, SQL/NoSQL databases, and cloud-oriented delivery workflows."
)


@dataclass(frozen=True)
class ContextChunk:
    key: str
    title: str
    text: str
    tags: tuple[str, ...]


class Provider(Protocol):
    name: str

    def generate(self, system_prompt: str, user_message: str) -> str | None:
        pass


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, timeout: int) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(self, system_prompt: str, user_message: str) -> str | None:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 420,
        }
        req = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            logger.warning("OpenAI provider request failed; falling back to local response.")
            return None

        try:
            reply = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError):
            return None
        return reply or None


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: int) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def generate(self, system_prompt: str, user_message: str) -> str | None:
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 420},
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        req = request.Request(
            url=url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=self.timeout) as response:  # noqa: S310
                data = json.loads(response.read().decode("utf-8"))
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            logger.warning("Gemini provider request failed; falling back to local response.")
            return None

        try:
            parts = data["candidates"][0]["content"]["parts"]
            reply = " ".join(
                str(part.get("text", "")).strip() for part in parts if isinstance(part, dict)
            ).strip()
        except (KeyError, IndexError, TypeError):
            return None
        return reply or None


class ContextRetriever:
    def __init__(self, projects: list[SimpleNamespace], max_context_chars: int) -> None:
        self.projects = projects
        self.max_context_chars = max_context_chars
        self._chunks = self._build_chunks()

    def _build_chunks(self) -> list[ContextChunk]:
        chunks: list[ContextChunk] = [
            ContextChunk(
                key="profile",
                title="Profile",
                text=(
                    f"{PROFILE['name']} - {PROFILE['headline']} Location: {PROFILE['location']}. "
                    f"{LOCAL_PROFILE_SUMMARY} {LOCAL_STACK_SUMMARY} "
                    f"GitHub: {GITHUB_PROFILE_URL}. LinkedIn: {LINKEDIN_PROFILE_URL}."
                ),
                tags=("identity", "skills", "hiring", "links", "contact"),
            ),
            ContextChunk(
                key="about-focus",
                title="Engineering Focus",
                text=" ".join(ABOUT_POINTS),
                tags=("identity", "architecture", "ai"),
            ),
            ContextChunk(
                key="delivery-hiring-fit",
                title="Hiring Fit",
                text=(
                    "Raju is a strong fit for backend-heavy full-stack roles and consulting work that require "
                    "API architecture, reliability, performance optimization, automation systems, and pragmatic AI integration."
                ),
                tags=("hiring", "architecture", "skills"),
            ),
            ContextChunk(
                key="profiles",
                title="Public Profiles",
                text=f"GitHub: {GITHUB_PROFILE_URL}. LinkedIn: {LINKEDIN_PROFILE_URL}.",
                tags=("links", "contact", "hiring"),
            ),
        ]

        for group in SKILL_GROUPS:
            title_lower = group["title"].lower()
            tags: list[str] = ["skills"]
            if "backend" in title_lower or "api" in title_lower:
                tags.append("architecture")
            if "ai" in title_lower:
                tags.append("ai")
            chunks.append(
                ContextChunk(
                    key=f"skills-{group['title'].lower()}",
                    title=f"Skills - {group['title']}",
                    text=f"{group['title']}: {', '.join(group['items'])}.",
                    tags=tuple(tags),
                )
            )

        for item in EXPERIENCE_ITEMS:
            highlights = " ".join(item["highlights"])
            chunks.append(
                ContextChunk(
                    key=f"experience-{item['company'].lower()}",
                    title=f"Experience - {item['role']} at {item['company']}",
                    text=(
                        f"{item['role']} at {item['company']} ({item['period']}). "
                        f"{item['summary']} Highlights: {highlights}"
                    ),
                    tags=("experience", "projects", "architecture"),
                )
            )

        for index, project in enumerate(self.projects[:20], start=1):
            stack = project.stack_items if hasattr(project, "stack_items") else []
            stack_text = ", ".join(stack) if stack else getattr(project, "tech_stack", "")
            source = getattr(project, "source_url", "") or ""
            chunks.append(
                ContextChunk(
                    key=f"project-{getattr(project, 'slug', index)}",
                    title=f"Project - {project.title}",
                    text=(
                        f"{project.title}. {project.headline} "
                        f"Description: {project.description} "
                        f"Tech stack: {stack_text}. "
                        f"Impact: {getattr(project, 'impact', '')}. "
                        f"Source: {source}."
                    ),
                    tags=("projects", "skills", "architecture", "ai"),
                )
            )

        return chunks

    def retrieve(self, query: str, intents: set[str] | None = None, top_k: int = 7) -> list[ContextChunk]:
        intents = intents or set()
        query_terms = tokenize(query)
        if not query_terms:
            return self._chunks[:3]

        doc_freq: Counter[str] = Counter()
        chunk_terms: dict[str, list[str]] = {}
        for chunk in self._chunks:
            terms = tokenize(f"{chunk.title} {chunk.text}")
            chunk_terms[chunk.key] = terms
            doc_freq.update(set(terms))

        total_docs = len(self._chunks) or 1
        scored: list[tuple[float, ContextChunk]] = []
        for chunk in self._chunks:
            terms = chunk_terms.get(chunk.key, [])
            if not terms:
                continue
            tf = Counter(terms)
            avg_len = max(len(terms), 1)
            score = 0.0
            for term in query_terms:
                if term not in tf:
                    continue
                idf = math.log((total_docs + 1) / (1 + doc_freq.get(term, 0))) + 1
                normalized_tf = tf[term] / (tf[term] + 0.8 + (0.2 * avg_len / 50))
                score += normalized_tf * idf

            if query.lower() in chunk.text.lower():
                score += 1.2
            if intents and set(chunk.tags).intersection(intents):
                score += 1.0 + (0.35 * len(set(chunk.tags).intersection(intents)))
            if score > 0:
                scored.append((score, chunk))

        if not scored:
            return self._chunks[:3]

        scored.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def context_block(self, query: str, intents: set[str]) -> str:
        selected = self.retrieve(query=query, intents=intents, top_k=8)
        lines: list[str] = []
        current_len = 0

        for chunk in selected:
            line = f"{chunk.title}: {chunk.text}"
            next_len = current_len + len(line) + 1
            if next_len > self.max_context_chars:
                break
            lines.append(line)
            current_len = next_len

        if not lines:
            lines.append(self._chunks[0].text)
        return "\n".join(f"- {line}" for line in lines)


class PortfolioChatService:
    def __init__(self) -> None:
        self.timeout = settings.CHATBOT_TIMEOUT_SECONDS
        self.active_provider = "local"
        self.provider = self._resolve_provider()
        self.retriever = ContextRetriever(
            projects=self._load_projects(),
            max_context_chars=settings.CHATBOT_MAX_CONTEXT_CHARS,
        )

    def generate_reply(self, user_message: str, history: list[dict] | None = None) -> str:
        resume_reply = try_resume_access_reply(user_message)
        if resume_reply is not None:
            return self._finalize_reply(resume_reply)

        clean_message = user_message.strip()
        if not clean_message:
            return "Ask a question about projects, engineering strengths, or hiring fit, and I will help."

        conversation = build_conversation_context(clean_message, history)
        intent_match = detect_intents(conversation.enriched_message)
        intents = set(intent_match.intents)
        retrieval_query = intent_match.expanded_message

        system_prompt = self._system_prompt(
            retrieval_query,
            intents,
            focus_entity=conversation.focus_entity,
        )
        if self.provider:
            ai_reply = self.provider.generate(system_prompt=system_prompt, user_message=clean_message)
            if ai_reply:
                self.active_provider = self.provider.name
                return self._finalize_reply(ai_reply)

        self.active_provider = "local"
        return self._finalize_reply(
            self._fallback_reply(
                clean_message,
                intents,
                focus_entity=conversation.focus_entity,
            )
        )

    def _resolve_provider(self) -> Provider | None:
        preferred = (settings.CHATBOT_PROVIDER or "local").strip().lower()
        if preferred in {"local", ""}:
            return None

        if preferred == "openai":
            if not settings.OPENAI_API_KEY:
                logger.warning("CHATBOT_PROVIDER=openai but OPENAI_API_KEY is not configured.")
                return None
            return OpenAIProvider(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                timeout=self.timeout,
            )

        if preferred == "gemini":
            if not settings.GEMINI_API_KEY:
                logger.warning("CHATBOT_PROVIDER=gemini but GEMINI_API_KEY is not configured.")
                return None
            return GeminiProvider(
                api_key=settings.GEMINI_API_KEY,
                model=settings.GEMINI_MODEL,
                timeout=self.timeout,
            )

        if preferred == "auto":
            if settings.OPENAI_API_KEY:
                return OpenAIProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.OPENAI_MODEL,
                    timeout=self.timeout,
                )
            if settings.GEMINI_API_KEY:
                return GeminiProvider(
                    api_key=settings.GEMINI_API_KEY,
                    model=settings.GEMINI_MODEL,
                    timeout=self.timeout,
                )

        logger.warning("Unknown CHATBOT_PROVIDER=%s; using local NLP only.", preferred)
        return None

    def _load_projects(self) -> list[SimpleNamespace]:
        from apps.projects.services import load_projects

        return load_projects(featured_only=False, limit=24)

    def _system_prompt(self, query: str, intents: set[str], focus_entity: str | None = None) -> str:
        context_block = self.retriever.context_block(query, intents=intents)
        focus_line = f"Conversation focus: {focus_entity}.\n" if focus_entity else ""
        return (
            "You are Ask Raju, a portfolio assistant for software engineer Raju Jha.\n"
            "Use only the provided context. If unknown, say so politely and redirect to portfolio topics.\n"
            "Respond with complete sentences and complete URLs, never truncated links.\n"
            "Keep answers practical, clear, and useful for recruiters, founders, or engineering peers.\n"
            "Always include profile links when the user asks about profile, contact, hiring, GitHub, or LinkedIn.\n"
            "If asked about stack, explicitly mention Python/Django, Java/Spring Boot, and React/Next.js when relevant.\n"
            "Never reveal resume secret keys; only share resume URLs when the user provides the exact secret phrase.\n"
            f"{focus_line}\n"
            "Reference links:\n"
            f"- GitHub: {GITHUB_PROFILE_URL}\n"
            f"- LinkedIn: {LINKEDIN_PROFILE_URL}\n\n"
            f"Retrieved context:\n{context_block}"
        )

    def _fallback_reply(
        self,
        user_message: str,
        intents: set[str],
        focus_entity: str | None = None,
    ) -> str:
        selected_chunks = self.retriever.retrieve(user_message, intents=intents, top_k=6)
        response_sections: list[str] = []

        focus_detail = self._project_detail_paragraph(focus_entity)
        if focus_detail:
            response_sections.append(focus_detail)

        if "identity" in intents:
            response_sections.append(self._owner_background())

        if "skills" in intents:
            response_sections.append(self._skills_overview())

        if "projects" in intents and not focus_detail:
            response_sections.append(
                "Featured engineering work includes "
                f"{self._project_highlights(limit=4)}. "
                "Open-source highlights include SyncWave (real-time audio sync), spa-config-gen (SPA deployment CLI), "
                "and react-native-modal-fix (maintained React Native modal library)."
            )

        if "experience" in intents:
            response_sections.append(self._experience_summary())
            response_sections.append(
                "Across roles he has delivered campaign platforms, API integrations, automation services, and production reliability improvements."
            )

        if "architecture" in intents:
            response_sections.append(
                "Architecture focus is backend reliability and API design: clear service boundaries, pragmatic data models, "
                "performance tuning, queue-safe automation, and integration patterns that remain maintainable as products scale."
            )

        if "ai" in intents:
            response_sections.append(
                "AI work is practical and product-oriented, including prompt design, LLM-assisted workflows, local model experimentation, "
                "and integrations that support delivery goals rather than demo-only prototypes."
            )

        if "hiring" in intents:
            response_sections.append(
                "Raju is a strong fit for backend-heavy full-stack roles or consulting engagements that need ownership from "
                "architecture through production execution, especially where APIs, automation, and pragmatic AI adoption matter."
            )

        if "contact" in intents or "resume" in intents:
            response_sections.append(
                f"Location: {PROFILE['location']}. "
                "The best way to reach him is the portfolio contact form or LinkedIn, both monitored for hiring and consulting inquiries."
            )

        if not response_sections:
            response_sections.append(
                "Based on the portfolio context, "
                f"{self._summarize_selected_chunks(selected_chunks)}"
            )

        if {"links", "contact", "hiring", "identity"}.intersection(intents):
            response_sections.append(
                f"Profiles: GitHub {GITHUB_PROFILE_URL} · LinkedIn {LINKEDIN_PROFILE_URL}."
            )

        return " ".join(self._dedupe_sections(response_sections))

    def _owner_background(self) -> str:
        about = " ".join(ABOUT_POINTS[:3])
        return (
            f"{LOCAL_PROFILE_SUMMARY} {about} "
            f"{self._experience_summary()} "
            "He is open to backend-heavy full-stack roles and consulting where API quality, automation, and execution speed are priorities."
        )

    def _skills_overview(self) -> str:
        groups = []
        for group in SKILL_GROUPS:
            sample = ", ".join(group["items"][:5])
            groups.append(f"{group['title']}: {sample}")
        return (
            "Raju's stack spans backend APIs, frontend delivery, infrastructure, and applied AI. "
            + " ".join(groups[:3])
            + ". He is strongest where Python/Django or Java/Spring services power React/Next.js product experiences."
        )

    def _project_detail_paragraph(self, title: str | None) -> str | None:
        project = get_project_by_title(title)
        if not project:
            return None
        stack = ", ".join(project.get("stack_items", []))
        source = project.get("source_url", "")
        source_text = f" Repository: {source}." if source else ""
        return (
            f"{project['title']} — {project['headline']} "
            f"{project['description']} "
            f"Technologies: {stack}. Impact: {project.get('impact', 'engineering delivery')}.{source_text}"
        )

    @staticmethod
    def _dedupe_sections(sections: list[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for section in sections:
            normalized = " ".join(section.split()).strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(section.strip())
        return deduped

    def _summarize_selected_chunks(self, chunks: list[ContextChunk]) -> str:
        snippets: list[str] = []
        for chunk in chunks[:3]:
            sentences = SENTENCE_RE.split(chunk.text)
            if not sentences:
                continue
            first = sentences[0].strip()
            if first:
                snippets.append(first)
        if snippets:
            return " ".join(snippets[:2])
        return (
            f"{LOCAL_PROFILE_SUMMARY} Project examples include {self._project_highlights(limit=2)}."
        )

    def _experience_summary(self) -> str:
        if not EXPERIENCE_ITEMS:
            return "Experience details are available in the portfolio sections."
        latest = EXPERIENCE_ITEMS[0]
        summary = str(latest["summary"]).strip().rstrip(".")
        if summary:
            summary = summary[0].lower() + summary[1:]
        else:
            summary = "production backend and full-stack delivery"
        return (
            f"He is currently {latest['role']} at {latest['company']} ({latest['period']}), "
            f"where he focuses on {summary}."
        )

    def _project_highlights(self, limit: int = 2) -> str:
        highlights: list[str] = []
        for project in self.retriever.projects[:limit]:
            title = (project.title or "").strip()
            headline = (project.headline or "").strip()
            if title and headline:
                highlights.append(f"{title} ({headline})")
            elif title:
                highlights.append(title)

        if highlights:
            return "; ".join(highlights)

        for project in ALL_PROJECTS[:limit]:
            highlights.append(f"{project['title']} ({project['headline']})")
        return "; ".join(highlights) if highlights else "backend API platforms and open-source engineering tools"

    @staticmethod
    def _finalize_reply(text: str) -> str:
        cleaned = INTERNAL_MODE_RE.sub(" ", str(text).strip())
        normalized = " ".join(cleaned.split())
        if not normalized:
            return "I could not generate a useful response right now."
        if normalized[-1] not in {".", "!", "?"}:
            normalized += "."
        return normalized
