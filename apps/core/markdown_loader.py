"""Load, render, and index Markdown content from content/."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import markdown
import yaml
from django.conf import settings

BASE_DIR = Path(settings.BASE_DIR)
CONTENT_DIR = BASE_DIR / "content"
PROJECTS_DIR = CONTENT_DIR / "projects"

CALLOUT_RE = re.compile(
    r"^>\s*\[!(NOTE|TIP|WARNING|IMPORTANT|CAUTION)\]\s*\n((?:>.*\n?)*)",
    re.MULTILINE,
)
HEADING_RE = re.compile(r"<h([1-6])\s+id=\"([^\"]+)\"[^>]*>(.*?)</h\1>", re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
MERMAID_FENCE_RE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)
RENDER_ARTIFACT_RE = re.compile(r"[¶\u00b6\u200b\u00ad]")
WHITESPACE_RE = re.compile(r"\s+")
EXTERNAL_LINK_RE = re.compile(
    r'<a href="(https?://[^"]+)"([^>]*)>',
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RenderedSection:
    id: str
    label: str
    title: str
    description: str
    html: str
    headings: tuple[dict[str, str], ...] = ()
    raw_text: str = ""


@dataclass(frozen=True)
class RenderedProject:
    title: str
    slug: str
    category: str
    order: int
    description: str
    repo: str
    demo: str
    stack: tuple[str, ...]
    html: str
    headings: tuple[dict[str, str], ...] = ()
    raw_text: str = ""


@dataclass
class SiteContext:
    name: str
    title: str
    location: str
    domain: str
    domain_url: str
    social_links: list[dict[str, str]]
    navigation: list[dict[str, str]]
    seo: dict[str, str]
    sections: list[RenderedSection] = field(default_factory=list)
    opensource_projects: list[RenderedProject] = field(default_factory=list)
    work_projects: list[RenderedProject] = field(default_factory=list)
    search_index: list[dict[str, str]] = field(default_factory=list)
    resume_url: str = ""


def _markdown_extensions() -> list[str]:
    return [
        "markdown.extensions.fenced_code",
        "markdown.extensions.codehilite",
        "markdown.extensions.tables",
        "markdown.extensions.nl2br",
        "markdown.extensions.sane_lists",
        "markdown.extensions.attr_list",
        "markdown.extensions.toc",
    ]


def _markdown_extension_configs() -> dict[str, dict[str, Any]]:
    return {
        "markdown.extensions.toc": {
            "permalink": True,
            "permalink_class": "heading-anchor",
            "permalink_title": "Link to this section",
            "slugify": _slugify,
            "toc_depth": 3,
        },
        "markdown.extensions.codehilite": {
            "css_class": "highlight",
            "guess_lang": True,
            "noclasses": False,
        },
    }


def _slugify(value: str, separator: str = "-") -> str:
    value = value.strip().lower()
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s_-]+", separator, value)
    return value.strip(separator)


def _render_inline_markdown(body: str) -> str:
    md = markdown.Markdown(extensions=["markdown.extensions.nl2br", "markdown.extensions.sane_lists"])
    return md.convert(body)


def _convert_mermaid_blocks(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        diagram = match.group(1).strip()
        return f'<pre class="mermaid">{diagram}</pre>'

    return MERMAID_FENCE_RE.sub(replace, text)


def _convert_callouts(text: str) -> str:
    callout_classes = {
        "NOTE": "callout-note",
        "TIP": "callout-tip",
        "WARNING": "callout-warning",
        "IMPORTANT": "callout-important",
        "CAUTION": "callout-caution",
    }

    def replace(match: re.Match[str]) -> str:
        kind = match.group(1)
        body = match.group(2)
        lines = []
        for line in body.splitlines():
            cleaned = re.sub(r"^>\s?", "", line).strip()
            if cleaned:
                lines.append(cleaned)
        inner = _render_inline_markdown("\n".join(lines))
        css_class = callout_classes.get(kind, "callout-note")
        return (
            f'<div class="callout {css_class}">'
            f'<span class="callout-title">{kind.title()}</span>{inner}</div>'
        )

    return CALLOUT_RE.sub(replace, text)


def _parse_frontmatter(source: str) -> tuple[dict[str, Any], str]:
    if not source.startswith("---"):
        return {}, source

    parts = source.split("---", 2)
    if len(parts) < 3:
        return {}, source

    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body


def _apply_external_link_attrs(html: str) -> str:
    def repl(match: re.Match[str]) -> str:
        href = match.group(1)
        attrs = match.group(2)
        if "target=" in attrs:
            return match.group(0)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer"{attrs}>'

    return EXTERNAL_LINK_RE.sub(repl, html)


def _wrap_tables(html: str) -> str:
    if "<table>" not in html:
        return html
    return html.replace("<table>", '<div class="md-table-scroll"><table>').replace(
        "</table>", "</table></div>"
    )


def _render_markdown(body: str) -> tuple[str, markdown.Markdown]:
    body = _convert_mermaid_blocks(body)
    body = _convert_callouts(body)
    md = markdown.Markdown(
        extensions=_markdown_extensions(),
        extension_configs=_markdown_extension_configs(),
    )
    html = _apply_external_link_attrs(_wrap_tables(md.convert(body)))
    return html, md


def _plain_text(value: str) -> str:
    text = TAG_RE.sub(" ", value or "")
    text = html.unescape(text)
    text = RENDER_ARTIFACT_RE.sub("", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def _extract_headings(html: str) -> tuple[dict[str, str], ...]:
    headings: list[dict[str, str]] = []
    for match in HEADING_RE.finditer(html):
        level, anchor_id, raw_title = match.groups()
        title = _plain_text(raw_title)
        if title:
            headings.append({"level": level, "id": anchor_id, "title": title})
    return tuple(headings)


def _strip_html(html: str) -> str:
    return _plain_text(html)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _load_project(path: Path) -> RenderedProject:
    source = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(source)
    html, _ = _render_markdown(body)
    headings = _extract_headings(html)
    stack = meta.get("stack") or []
    if isinstance(stack, str):
        stack = [item.strip() for item in stack.split(",") if item.strip()]

    return RenderedProject(
        title=str(meta.get("title", path.stem)),
        slug=str(meta.get("slug", path.stem)),
        category=str(meta.get("category", "work")),
        order=int(meta.get("order", 99)),
        description=str(meta.get("description", "")),
        repo=str(meta.get("repo", "")),
        demo=str(meta.get("demo", "")),
        stack=tuple(stack),
        html=html,
        headings=headings,
        raw_text=_strip_html(html),
    )


def _load_section(section_id: str, label: str, filename: str) -> RenderedSection:
    path = CONTENT_DIR / filename
    source = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(source)
    html, _ = _render_markdown(body)
    headings = _extract_headings(html)

    return RenderedSection(
        id=section_id,
        label=label,
        title=str(meta.get("title", label)),
        description=str(meta.get("description", "")),
        html=html,
        headings=headings,
        raw_text=_strip_html(html),
    )


def _build_search_index(
    sections: list[RenderedSection],
    projects: list[RenderedProject],
    site: dict[str, Any],
) -> list[dict[str, str]]:
    index: list[dict[str, str]] = []

    def index_text(*parts: str) -> str:
        return _plain_text(" ".join(part for part in parts if part))

    for nav in site.get("navigation", []):
        nav_id = nav.get("id", "")
        if nav_id == "contact":
            url = "#open-contact"
        else:
            url = f"/#{nav_id}"
        label = _plain_text(str(nav.get("label", "")))
        index.append(
            {
                "type": "section",
                "title": label,
                "subtitle": "Section" if nav_id != "contact" else "Open contact form",
                "url": url,
                "text": label,
            }
        )

    for section in sections:
        for heading in section.headings:
            if section.id == "contact":
                heading_url = "#open-contact"
            else:
                heading_url = f"/#{section.id}#{heading['id']}"
            title = _plain_text(heading["title"])
            section_title = _plain_text(section.title)
            index.append(
                {
                    "type": "heading",
                    "title": title,
                    "subtitle": section_title,
                    "url": heading_url,
                    "text": index_text(section_title, title),
                }
            )

    for project in projects:
        anchor = "opensource" if project.category == "opensource" else "projects"
        title = _plain_text(project.title)
        description = _plain_text(project.description)
        index.append(
            {
                "type": "project",
                "title": title,
                "subtitle": description,
                "url": f"/#{anchor}#{project.slug}",
                "text": index_text(title, description, " ".join(project.stack), project.raw_text),
            }
        )
        for heading in project.headings:
            heading_title = _plain_text(heading["title"])
            index.append(
                {
                    "type": "heading",
                    "title": heading_title,
                    "subtitle": title,
                    "url": f"/#{anchor}#{project.slug}#{heading['id']}",
                    "text": index_text(title, heading_title),
                }
            )

    for link in site.get("social_links", []):
        index.append(
            {
                "type": "link",
                "title": link.get("label", ""),
                "subtitle": "External link",
                "url": link.get("url", ""),
                "text": link.get("label", ""),
            }
        )

    return index


@lru_cache(maxsize=1)
def load_site_context() -> SiteContext:
    site = _load_yaml(CONTENT_DIR / "site.yaml")
    navigation = site.get("navigation", [])

    sections = [
        _load_section(item["id"], item["label"], item["file"])
        for item in navigation
        if item.get("id") and item.get("file")
    ]

    projects = sorted(
        (_load_project(path) for path in PROJECTS_DIR.glob("*.md")),
        key=lambda item: item.order,
    )
    opensource = [project for project in projects if project.category == "opensource"]
    work = [project for project in projects if project.category == "work"]

    resume_url = getattr(settings, "RESUME_URL", "") or ""

    search_index = _build_search_index(sections, projects, site)

    return SiteContext(
        name=str(site.get("name", "Raju Jha")),
        title=str(site.get("title", "Software Engineer")),
        location=str(site.get("location", "")),
        domain=str(site.get("domain", "")),
        domain_url=str(site.get("domain_url", "")),
        social_links=list(site.get("social_links", [])),
        navigation=[{"id": item["id"], "label": item["label"]} for item in navigation],
        seo=dict(site.get("seo", {})),
        sections=sections,
        opensource_projects=opensource,
        work_projects=work,
        search_index=search_index,
        resume_url=resume_url,
    )


def invalidate_content_cache() -> None:
    load_site_context.cache_clear()


def project_catalog() -> list[dict[str, Any]]:
    """Flat project dicts for chatbot and legacy consumers."""
    context = load_site_context()
    catalog: list[dict[str, Any]] = []
    for project in context.opensource_projects + context.work_projects:
        catalog.append(
            {
                "title": project.title,
                "slug": project.slug,
                "headline": project.description,
                "description": project.raw_text[:500],
                "stack_items": list(project.stack),
                "source_url": project.repo,
                "demo_url": project.demo,
                "is_featured": project.category == "opensource",
                "display_order": project.order,
            }
        )
    return catalog


def profile_dict() -> dict[str, Any]:
    context = load_site_context()
    return {
        "name": context.name,
        "headline": context.seo.get("description", context.title),
        "subheadline": context.title,
        "location": context.location,
        "domain": context.domain,
        "domain_url": context.domain_url,
        "social_links": context.social_links,
    }


def skill_groups() -> list[dict[str, Any]]:
    path = CONTENT_DIR / "skills.md"
    if not path.exists():
        return []
    meta, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    groups = meta.get("groups") or []
    return [{"title": g.get("title", ""), "items": list(g.get("items", []))} for g in groups]


def about_points() -> list[str]:
    path = CONTENT_DIR / "about.md"
    if not path.exists():
        return []
    meta, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    return [str(point) for point in meta.get("summary_points", [])]


def experience_items() -> list[dict[str, Any]]:
    path = CONTENT_DIR / "experience.md"
    if not path.exists():
        return []
    meta, _ = _parse_frontmatter(path.read_text(encoding="utf-8"))
    roles = meta.get("roles") or []
    return [
        {
            "company": role.get("company", ""),
            "role": role.get("role", ""),
            "period": role.get("period", ""),
            "summary": role.get("summary", ""),
            "highlights": list(role.get("highlights", [])),
        }
        for role in roles
    ]
