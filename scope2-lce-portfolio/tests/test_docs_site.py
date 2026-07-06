"""Open-file sanity for the HP-04 handoff docs site (`docs/site/`).

Mirrors ``test_report.py::test_report_html_has_no_external_references``: the
site must render correctly opened via ``file://`` from a pulled-out copy of
the folder, so no page may link, fetch, or @import anything external (no
CDN, no font fetch, no absolute URL) — self-contained is the whole point of
putting it inside ``scope2-lce-portfolio/`` in the first place.
"""

import re
from pathlib import Path

import pytest

SITE_DIR = Path(__file__).parent.parent / "docs" / "site"
SITE_HTML_FILES = sorted(SITE_DIR.glob("*.html"))

_HREF_SRC_RE = re.compile(r'(?:href|src)="([^"]+)"')


@pytest.mark.parametrize("html_path", SITE_HTML_FILES, ids=lambda p: p.name)
def test_site_page_has_no_external_references(html_path: Path) -> None:
    """No CDN, no external font fetch, no absolute URL in any site page."""
    html = html_path.read_text()
    for needle in ("http://", "https://", "@import", "//fonts."):
        assert needle not in html, f"external reference {needle!r} in {html_path.name}"


def test_site_has_expected_pages() -> None:
    """The four documented pages (+ shared stylesheet) exist."""
    names = {p.name for p in SITE_HTML_FILES}
    assert names == {"index.html", "mechanics.html", "inputs.html", "decisions.html"}
    assert (SITE_DIR / "site.css").is_file()


@pytest.mark.parametrize("html_path", SITE_HTML_FILES, ids=lambda p: p.name)
def test_site_page_local_links_resolve(html_path: Path) -> None:
    """Every relative href/src (css, other pages, doc/ADR links) points at a
    file that actually exists on disk — a broken relative link would only
    surface by manually clicking through the pulled-out site."""
    html = html_path.read_text()
    for target in _HREF_SRC_RE.findall(html):
        if target.startswith(("mailto:", "#")):
            continue
        path_part = target.split("#", 1)[0]
        resolved = (html_path.parent / path_part).resolve()
        assert resolved.is_file(), f"{html_path.name} links to missing file: {target!r}"


@pytest.mark.parametrize("html_path", SITE_HTML_FILES, ids=lambda p: p.name)
def test_site_page_has_no_script_tags(html_path: Path) -> None:
    """Content-first, hand-rolled SVG only: no JS frameworks or inline
    scripts on the docs site (unlike the ADR 0014 report, which needs JS for
    its interactive heatmap/SOC view)."""
    html = html_path.read_text()
    assert "<script" not in html.lower()
