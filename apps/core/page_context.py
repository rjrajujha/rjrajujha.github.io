"""Shared template context for full-shell pages."""

from __future__ import annotations

import json

from django.http import HttpRequest

from apps.core.markdown_loader import about_intro, experience_items, load_site_context, skill_groups


def build_site_page_context(request: HttpRequest, **overrides) -> dict:
    site = load_site_context()
    seo = site.seo
    base = site.domain_url.rstrip("/")
    canonical = f"{base}{request.path}" if request.path != "/" else f"{base}/"

    context = {
        "site": site,
        "page_title": seo.get("title", f"{site.name} · {site.title}"),
        "page_description": seo.get("description", ""),
        "canonical_url": canonical,
        "og_type": seo.get("og_type", "website"),
        "twitter_card": seo.get("twitter_card", "summary_large_image"),
        "search_index_json": json.dumps(site.search_index),
        "site_config_json": json.dumps(
            {
                "name": site.name,
                "social": site.social_links,
            }
        ),
        "structured_data_json": json.dumps(
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": site.name,
                "jobTitle": site.title,
                "url": f"{base}/",
                "sameAs": [link["url"] for link in site.social_links if link.get("url")],
                "description": seo.get("description", ""),
            }
        ),
        "about_intro": about_intro(),
        "experience_items": experience_items(),
        "skill_groups": skill_groups(),
    }
    context.update(overrides)
    return context
