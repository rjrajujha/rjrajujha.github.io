from django.test import SimpleTestCase

from apps.core.markdown_loader import (
    _convert_mermaid_blocks,
    _extract_headings,
    _plain_text,
    invalidate_content_cache,
    load_site_context,
)


class MarkdownLoaderTests(SimpleTestCase):
    def setUp(self):
        invalidate_content_cache()

    def test_plain_text_strips_html_entities_and_pilcrow(self):
        raw = "<h2 id=\"x\">Devout Growth &middot; Engineer<a href=\"#x\">&para;</a></h2>"
        self.assertEqual(_plain_text(raw), "Devout Growth · Engineer")

    def test_heading_extraction_omits_permalink_artifacts(self):
        html = '<h2 id="backend">Backend &amp; systems<a class="heading-anchor" href="#backend">&para;</a></h2>'
        headings = _extract_headings(html)
        self.assertEqual(headings[0]["title"], "Backend & systems")

    def test_search_index_contains_plain_text_only(self):
        context = load_site_context()
        for entry in context.search_index:
            self.assertNotIn("&para;", entry.get("title", ""))
            self.assertNotIn("&para;", entry.get("subtitle", ""))
            self.assertNotIn("&para;", entry.get("text", ""))
            self.assertNotIn("<", entry.get("title", ""))
            self.assertNotIn("¶", entry.get("title", ""))

    def test_mermaid_blocks_convert_to_diagram_container(self):
        source = "```mermaid\ngraph TD\nA --> B\n```"
        converted = _convert_mermaid_blocks(source)
        self.assertIn('class="mermaid"', converted)
        self.assertIn("graph TD", converted)

    def test_tables_are_wrapped_for_horizontal_scroll(self):
        from apps.core.markdown_loader import _render_markdown

        html, _ = _render_markdown("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn('class="md-table-scroll"', html)

    def test_external_links_open_in_new_tab(self):
        from apps.core.markdown_loader import _render_markdown

        html, _ = _render_markdown("[Example](https://example.com)")
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="noopener noreferrer"', html)
