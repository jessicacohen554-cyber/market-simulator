"""Curate the ``load-forecast-error`` clean datatype (the orchestrator's entry point).

``scripts/regenerate_clean.py`` and ``scripts/lib/clean_profiles.py`` resolve a
datatype's curate script by name (``curate_<datatype>.py``); the derivation
itself lives in :mod:`scripts.data.derive_load_forecast_error` (the frozen
derive named by lane UC-1-FIX-7, rule 23). This module is that derive under
the orchestrator's name: the same ``curate`` and the same ``--isos`` flag.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/data/curate_load_forecast_error.py --isos SPP
"""

from __future__ import annotations

import argparse

from scripts.data.derive_load_forecast_error import curate

__all__ = ["curate", "main"]


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--isos`` subset (default every registered ISO)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="*", default=None, help="ISO subset (default: all)")
    ap.add_argument(
        "--last-year",
        type=int,
        default=None,
        help="Last year scanned (default: this year)",
    )
    args = ap.parse_args(argv)
    written = curate(isos=args.isos, last_year=args.last_year)
    print(f"wrote {len(written)} partition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
