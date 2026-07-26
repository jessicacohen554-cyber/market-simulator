#!/usr/bin/env python3
"""Verify every Subresource-Integrity hash on the codebase-site against served bytes.

A wrong ``integrity`` attribute does not degrade — the browser **refuses to
execute the script entirely**, silently. The site has been bitten by this twice:
Wave 5C found six pages whose d3/gsap hashes were fabricated (a correct leading
run of base64 followed by an invented tail — the signature of a hash written
from memory rather than computed), and Wave 5D found a seventh where all three
of ``lp-core.html``'s KaTeX hashes were wrong, blocking its stylesheet, KaTeX
and auto-render outright.

Both were invisible: the pages still loaded, just without their charts (or, on
lp-core, carrying ~300 KB of blocked KaTeX it happens not to render math with).
That is the point — a fabricated hash is silent by construction, so whether it
costs a visible feature is luck, not design. This script makes it loud. It scans
every
``<script>``/``<link>`` tag in ``docs/codebase-site/*.html`` for an external URL
and reports:

* **FAIL** — a tag whose ``integrity`` does not match the bytes the CDN serves
  (the fabricated-hash defect; the resource is blocked in every browser);
* **NO-INTEGRITY** — an external tag with no ``integrity`` at all (unpinned: the
  CDN can change the bytes under us);
* **VERSION-SPLIT** — the same library pinned to two versions or two CDNs across
  pages (what produced the KaTeX 0.16.8/0.16.9 split).

Exit status is non-zero if any FAIL or VERSION-SPLIT is found, so this can gate
a site change locally. It needs the network, so it is **not** a CI job (and this
is a private repo — CLAUDE.md's GitHub-Actions rule); run it in-session after
touching any CDN tag.

The only correct way to obtain a hash is to compute it from the bytes, which is
what ``--emit`` does::

    python3 scripts/check_site_sri.py                 # audit the tree
    python3 scripts/check_site_sri.py --emit <url>    # print a correct SRI tag attribute

Never copy a hash from another page, from a CDN's docs, or from memory.

STDLIB-ONLY (``hashlib``/``urllib``/``re``), so it runs on a bare ``python3``.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

# scripts/check_site_sri.py -> <repo>/scripts -> <repo>
REPO = Path(__file__).resolve().parent.parent
SITE_DIR = REPO / "docs" / "codebase-site"

#: Whole opening tags that can carry a subresource reference.
TAG_RE = re.compile(r"<(?:script|link)\b[^>]*>", re.IGNORECASE)
#: The external URL a tag points at (``src`` for scripts, ``href`` for links).
URL_RE = re.compile(r'(?:src|href)="(https://[^"]+)"')
#: An SRI attribute: algorithm plus base64 digest.
INTEGRITY_RE = re.compile(r'integrity="(sha(?:256|384|512))-([^"]+)"')

#: Libraries whose version/source must be uniform across the site, matched
#: against the URL path. Value is the human name used in VERSION-SPLIT reports.
#: A library may legitimately load several *files* (gsap + ScrollTrigger; KaTeX
#: css + js + auto-render), so the split check keys on (CDN host, version) —
#: never on the URL, which would flag those as splits.
#: Keys are regexes because the two CDNs spell the same library differently:
#: cdnjs ``/ajax/libs/katex/0.16.9/`` vs jsdelivr ``/npm/katex@0.16.9/``. Matching
#: only the ``/katex/`` form is how a split hides.
TRACKED = {
    r"/d3[/@]": "d3",
    r"/gsap[/@]": "gsap",
    r"/katex[/@]": "KaTeX",
}

#: A version token in a CDN path: cdnjs ``/ajax/libs/<lib>/<version>/`` or
#: jsdelivr ``/npm/<pkg>@<version>/``.
VERSION_RE = re.compile(r"[/@](\d+\.\d+\.\d+)(?=[/@]|$)")


def sri(data: bytes, alg: str = "sha384") -> str:
    """Return the SRI attribute value (``<alg>-<base64 digest>``) for ``data``."""
    return f"{alg}-{base64.b64encode(getattr(hashlib, alg)(data).digest()).decode()}"


def fetch(url: str) -> bytes:
    """Download ``url`` and return its raw bytes."""
    with urllib.request.urlopen(url) as resp:  # noqa: S310 (https literals only)
        return resp.read()


def iter_tags(site_dir: Path):
    """Yield ``(page_name, url, algorithm_or_None, digest_or_None)`` per external tag."""
    for path in sorted(site_dir.glob("*.html")):
        text = path.read_text(encoding="utf-8")
        for tag in TAG_RE.findall(text):
            url_m = URL_RE.search(tag)
            if not url_m:
                continue
            integrity_m = INTEGRITY_RE.search(tag)
            if integrity_m:
                yield (
                    path.name,
                    url_m.group(1),
                    integrity_m.group(1),
                    integrity_m.group(2),
                )
            else:
                yield path.name, url_m.group(1), None, None


def tracked_build(url: str) -> tuple[str, str] | None:
    """Return ``(library, "<host> <version>")`` for ``url``, or None if untracked.

    The second element is the identity the site must keep uniform: the CDN host
    plus the pinned version. Two files of the same library at the same version
    from the same host share it, so only a genuine split is reported.
    """
    low = url.lower()
    for pattern, name in TRACKED.items():
        if re.search(pattern, low):
            host = url.split("/")[2]
            version_m = VERSION_RE.search(url)
            version = version_m.group(1) if version_m else "UNPINNED"
            return name, f"{host} @ {version}"
    return None


def audit(site_dir: Path) -> int:
    """Audit every external tag under ``site_dir``. Return a process exit status."""
    checked: dict[tuple[str, str, str], bool] = {}
    failures: list[str] = []
    unpinned: list[str] = []
    versions: dict[str, set[str]] = defaultdict(set)

    for page, url, alg, want in iter_tags(site_dir):
        tracked = tracked_build(url)
        if tracked:
            versions[tracked[0]].add(tracked[1])
        if alg is None:
            unpinned.append(f"{page}: {url}")
            print(f"NO-INTEGRITY  {page:28s} {url}")
            continue
        key = (url, alg, want)
        if key not in checked:
            got = sri(fetch(url), alg).split("-", 1)[1]
            checked[key] = got == want
            if not checked[key]:
                failures.append(
                    f"{page}: {url}\n    declared {alg}-{want}\n    actual   {alg}-{got}"
                )
        print(f"{'OK  ' if checked[key] else 'FAIL'}          {page:28s} {url}")

    splits = {name: builds for name, builds in versions.items() if len(builds) > 1}

    print()
    if failures:
        print(
            f"FABRICATED / STALE HASHES ({len(failures)}) — these resources are BLOCKED in every browser:"
        )
        for f in failures:
            print(f"  {f}")
    if splits:
        print(
            f"VERSION SPLITS ({len(splits)}) — one library, more than one build or CDN:"
        )
        for name, builds in sorted(splits.items()):
            print(f"  {name}: {', '.join(sorted(builds))}")
    if unpinned:
        print(f"UNPINNED ({len(unpinned)}) — external tag with no integrity attribute:")
        for u in unpinned:
            print(f"  {u}")

    print(
        f"\n{len(checked)} unique (url, hash) pairs checked · "
        f"{len(failures)} mismatched · {len(splits)} split · {len(unpinned)} unpinned"
    )
    return 1 if (failures or splits) else 0


def main() -> None:
    """CLI entry point: audit the site, or emit a correct SRI value for one URL."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--emit",
        metavar="URL",
        help="download URL and print its correct integrity value instead of auditing",
    )
    parser.add_argument(
        "--alg",
        default="sha384",
        choices=["sha256", "sha384", "sha512"],
        help="digest algorithm for --emit (default: sha384)",
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=SITE_DIR,
        help=f"directory of HTML pages to audit (default: {SITE_DIR})",
    )
    args = parser.parse_args()

    if args.emit:
        data = fetch(args.emit)
        print(
            f'integrity="{sri(data, args.alg)}" crossorigin="anonymous"  # {len(data)} bytes'
        )
        return

    sys.exit(audit(args.site_dir))


if __name__ == "__main__":
    main()
