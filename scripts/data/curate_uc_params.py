"""Curate the ``uc-params`` clean datatype (the orchestrator's entry point).

``scripts/regenerate_clean.py`` and ``scripts/lib/clean_profiles.py`` resolve a
datatype's curate script by name (``curate_<datatype>.py``); the derivation
itself lives in :mod:`scripts.data.derive_uc_cluster_params` (the frozen
derive named by the UC-1 charter, rule 23). This module is that derive under
the orchestrator's name: the same ``curate(raw_root=None, isos=None)`` and the
same ``--isos`` / ``--raw-root`` flags, nothing else.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/data/curate_uc_params.py --isos NEISO
"""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.data.derive_uc_cluster_params import curate

__all__ = ["curate", "main"]


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--isos`` subset (default every registered ISO)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="*", default=None, help="ISO subset (default: all)")
    ap.add_argument(
        "--raw-root", default=None, help="Raw tree root (default: data/raw)"
    )
    args = ap.parse_args(argv)
    written = curate(
        raw_root=Path(args.raw_root) if args.raw_root else None, isos=args.isos
    )
    print(f"wrote {len(written)} partition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
