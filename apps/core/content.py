"""Backward-compatible exports sourced from Markdown content."""

from __future__ import annotations

from apps.core.markdown_loader import (
    about_points,
    experience_items,
    profile_dict,
    project_catalog,
    skill_groups,
)

PROFILE = profile_dict()
SKILL_GROUPS = skill_groups()
EXPERIENCE_ITEMS = experience_items()
ABOUT_POINTS = about_points()
ALL_PROJECTS = project_catalog()
