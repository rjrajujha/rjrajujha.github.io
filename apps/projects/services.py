from __future__ import annotations

from types import SimpleNamespace

from apps.core.content import FALLBACK_FEATURED_PROJECTS, OPEN_SOURCE_PROJECTS


def load_projects(featured_only: bool = False, limit: int | None = None) -> list[SimpleNamespace]:
    projects = list(OPEN_SOURCE_PROJECTS) + list(FALLBACK_FEATURED_PROJECTS)
    if featured_only:
        projects = [item for item in projects if item.get("is_featured", True)]
    projects = sorted(projects, key=lambda item: item.get("display_order", 99))
    if limit is not None:
        projects = projects[:limit]
    return [project_namespace(item) for item in projects]


def project_namespace(item: dict) -> SimpleNamespace:
    stack_items = item.get("stack_items") or []
    if isinstance(stack_items, str):
        stack_items = [part.strip() for part in stack_items.split(",") if part.strip()]
    return SimpleNamespace(
        title=item["title"],
        slug=item.get("slug", ""),
        headline=item["headline"],
        description=item["description"],
        stack_items=stack_items,
        tech_stack=", ".join(stack_items),
        impact=item.get("impact", ""),
        source_url=item.get("source_url", ""),
        demo_url=item.get("demo_url", ""),
        pk=None,
        display_order=item.get("display_order", 0),
        is_featured=item.get("is_featured", True),
    )


def fallback_projects(limit: int | None = None) -> list[SimpleNamespace]:
    return load_projects(featured_only=False, limit=limit)


def fallback_project_by_slug(slug: str) -> SimpleNamespace | None:
    target = (slug or "").strip().lower()
    if not target:
        return None
    for project in load_projects():
        if (project.slug or "").strip().lower() == target:
            return project
    return None
