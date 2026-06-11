from __future__ import annotations

from types import SimpleNamespace

from apps.core.markdown_loader import load_site_context


def load_projects(featured_only: bool = False, limit: int | None = None) -> list[SimpleNamespace]:
    site = load_site_context()
    projects = site.opensource_projects + site.work_projects
    if featured_only:
        projects = [item for item in projects if item.category == "opensource"]
    if limit is not None:
        projects = projects[:limit]
    return [project_namespace(item) for item in projects]


def project_namespace(item) -> SimpleNamespace:
    stack_items = list(item.stack)
    return SimpleNamespace(
        title=item.title,
        slug=item.slug,
        headline=item.description,
        description=item.raw_text[:500],
        stack_items=stack_items,
        tech_stack=", ".join(stack_items),
        impact=item.category,
        source_url=item.repo,
        demo_url=item.demo,
        pk=None,
        display_order=item.order,
        is_featured=item.category == "opensource",
    )
