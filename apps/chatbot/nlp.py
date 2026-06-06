"""Offline-first NLP helpers: intents, synonyms, fuzzy matching, resume secret detection."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass

TOKEN_RE = re.compile(r"[a-z0-9]+")

INTENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "identity": (
        "who are you",
        "who is",
        "about raju",
        "about owner",
        "tell me about",
        "introduce",
        "summary",
        "background",
        "profile",
        "bio",
        "owner",
        "who built",
        "about you",
    ),
    "skills": (
        "skill",
        "stack",
        "technology",
        "technologies",
        "backend",
        "frontend",
        "django",
        "python",
        "java",
        "spring",
        "react",
        "next",
        "tailwind",
        "fastapi",
        "what do you know",
    ),
    "projects": (
        "project",
        "portfolio",
        "built",
        "work",
        "case study",
        "example",
        "github repo",
        "syncwave",
        "spa-config",
        "modal-fix",
        "open source",
        "repository",
    ),
    "experience": ("experience", "career", "history", "company", "role", "internshala", "devout", "job"),
    "hiring": ("hire", "hiring", "fit", "candidate", "consulting", "consultant", "freelance", "contract"),
    "contact": (
        "contact",
        "reach",
        "connect",
        "message",
        "talk",
        "email",
        "details",
        "contact details",
        "get in touch",
    ),
    "architecture": (
        "architecture",
        "system design",
        "api",
        "scalable",
        "performance",
        "automation",
        "integration",
    ),
    "ai": ("ai", "llm", "openai", "gemini", "prompt", "chatbot", "automation", "machine learning"),
    "links": ("github", "linkedin", "profile link", "links", "url", "social"),
    "resume": (
        "resume",
        "cv",
        "curriculum",
        "share resume",
        "download resume",
        "resume link",
    ),
}

SYNONYM_MAP: dict[str, tuple[str, ...]] = {
    "owner": ("raju", "developer", "engineer", "author"),
    "technologies": ("technology", "stack", "skills", "tech"),
    "proj": ("project", "projects"),
    "gh": ("github",),
    "li": ("linkedin",),
    "contact": ("reach", "connect", "email"),
    "resume": ("cv", "curriculum vitae"),
    "syncwave": ("audio", "realtime", "streaming"),
    "backend": ("api", "server", "django", "fastapi"),
}

@dataclass(frozen=True)
class IntentMatch:
    intents: frozenset[str]
    expanded_message: str


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def expand_synonyms(message: str) -> str:
    tokens = tokenize(message)
    extra: list[str] = []
    for token in tokens:
        for canonical, aliases in SYNONYM_MAP.items():
            if token == canonical or token in aliases:
                extra.append(canonical)
                extra.extend(aliases)
    if not extra:
        return message
    return f"{message} {' '.join(extra)}"


def fuzzy_contains(haystack: str, needle: str, threshold: float = 0.82) -> bool:
    if not needle:
        return False
    hay = haystack.lower()
    if needle.lower() in hay:
        return True
    for window in _sliding_windows(hay, max(len(needle) + 4, len(needle))):
        ratio = difflib.SequenceMatcher(None, needle.lower(), window).ratio()
        if ratio >= threshold:
            return True
    return False


def _sliding_windows(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    return [text[index : index + size] for index in range(0, len(text) - size + 1, max(1, size // 2))]


def detect_intents(message: str) -> IntentMatch:
    expanded = expand_synonyms(message)
    lowered = expanded.lower()
    intents: set[str] = set()

    for intent, keywords in INTENT_KEYWORDS.items():
        for keyword in keywords:
            if " " in keyword:
                if keyword in lowered:
                    intents.add(intent)
                    break
            elif fuzzy_contains(lowered, keyword, threshold=0.88 if len(keyword) > 5 else 0.9):
                intents.add(intent)
                break

    if not intents:
        query_terms = set(tokenize(lowered))
        for intent, keywords in INTENT_KEYWORDS.items():
            for keyword in keywords:
                keyword_terms = set(tokenize(keyword))
                if keyword_terms and keyword_terms.issubset(query_terms):
                    intents.add(intent)

    return IntentMatch(intents=frozenset(intents), expanded_message=expanded)


