"""Lightweight in-request conversation context (no database)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from apps.core.content import ALL_PROJECTS

FOLLOW_UP_RE = re.compile(
    r"\b(it|its|it's|this|that|they|them|the project|the platform|the library|the tool|the app)\b",
    re.I,
)
TECH_FOLLOW_UP_RE = re.compile(
    r"\b(technologies?|tech stack|stack|built with|written in|language|framework)\b",
    re.I,
)


@dataclass(frozen=True)
class ConversationContext:
    focus_entity: str | None
    enriched_message: str


def _project_catalog() -> list[dict]:
    catalog: list[dict] = []
    for project in ALL_PROJECTS:
        aliases = {project["title"].lower(), project.get("slug", "").lower()}
        title_lower = project["title"].lower()
        if " " in title_lower:
            aliases.add(title_lower.replace(" ", ""))
        catalog.append(
            {
                "title": project["title"],
                "aliases": tuple(alias for alias in aliases if alias),
                "data": project,
            }
        )
    return catalog


def _normalize_history(history: list[dict] | None) -> list[dict]:
    if not history:
        return []
    normalized: list[dict] = []
    for entry in history[-10:]:
        if not isinstance(entry, dict):
            continue
        role = str(entry.get("role", "")).strip().lower()
        content = str(entry.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            normalized.append({"role": role, "content": content})
    return normalized


def find_entity_in_text(text: str) -> str | None:
    lowered = text.lower()
    for project in _project_catalog():
        for alias in project["aliases"]:
            if len(alias) < 3:
                continue
            if alias in lowered:
                return project["title"]
    return None


def extract_focus_entity(history: list[dict]) -> str | None:
    for entry in reversed(history):
        entity = find_entity_in_text(entry["content"])
        if entity:
            return entity
    return None


def needs_context_resolution(message: str) -> bool:
    return bool(FOLLOW_UP_RE.search(message) or TECH_FOLLOW_UP_RE.search(message))


def build_conversation_context(message: str, history: list[dict] | None) -> ConversationContext:
    normalized_history = _normalize_history(history)
    explicit = find_entity_in_text(message)
    if explicit:
        return ConversationContext(
            focus_entity=explicit,
            enriched_message=message,
        )

    focus = extract_focus_entity(normalized_history)
    if focus and needs_context_resolution(message):
        return ConversationContext(
            focus_entity=focus,
            enriched_message=f"{message} (referring to {focus})",
        )

    return ConversationContext(focus_entity=focus, enriched_message=message)


def get_project_by_title(title: str | None) -> dict | None:
    if not title:
        return None
    target = title.strip().lower()
    for project in ALL_PROJECTS:
        if project["title"].lower() == target:
            return project
    return None
