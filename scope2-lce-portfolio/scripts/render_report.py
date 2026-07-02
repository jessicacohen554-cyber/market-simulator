#!/usr/bin/env python
"""Regenerate ``report.html`` from a committed run folder (ADR 0014 §6).

Usage::

    ../.venv/bin/python scripts/render_report.py results/<run_id>/

Reads ``<run-dir>/report.json`` — the versioned report payload (ADR 0014 §3)
— and re-renders ``<run-dir>/report.html`` **without re-solving**, e.g. after
a template improvement in ``lce_portfolio.report``. The renderer refuses any
``payload_version`` it does not know, so a payload written by a future schema
can never be silently mis-rendered. Rendering is a pure function of the
payload: the same ``report.json`` always regenerates byte-identical HTML.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]  # scope2-lce-portfolio/
sys.path.insert(0, str(_ROOT / "src"))

from lce_portfolio.report import render_report  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Parse the run-dir argument, re-render its HTML, report what was written."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run_dir",
        help="run folder containing report.json (e.g. results/<run_id>/)",
    )
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    payload_path = run_dir / "report.json"
    if not payload_path.exists():
        print(f"error: no report.json in {run_dir}", file=sys.stderr)
        return 1

    try:
        payload = json.loads(payload_path.read_text())
        html = render_report(payload)  # refuses unknown payload_version (§3)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    out_path = run_dir / "report.html"
    out_path.write_text(html)
    print(f"re-rendered {out_path} ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
