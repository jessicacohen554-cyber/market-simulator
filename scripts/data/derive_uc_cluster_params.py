"""Derive the ``uc-params`` clean datatype (lane UC-1, frozen derive, rule 23).

The measured per-plant commitment physics the MILP unit-commitment stage reads
(``ScenarioConfig.unit_commitment_milp``): unit count, HSL/LSL and minimum
stable fraction, minimum run / down durations and the plant no-load heat
input, per (plant, CAMPD unit-type family) cluster, pooled 2023-2025 from the
EPA CAMPD unit-level extracts (``data/raw/campd-unit-level``). Schema:
``data/dictionary/schema/uc-params.schema.yaml``; design:
``docs/records/governance/uc-milp-2026-10/DESIGN-uc-milp-engine-2026-10-03.md``
section 1.2-1.3.

Per-ISO scoping lives in ``scripts/lib/uc_params/<iso>.py`` (each registers an
:class:`~scripts.lib.uc_params.IsoSpec` naming its CAMPD state footprint); this
script is a thin dispatcher over that registry, so adding an ISO never touches
it. The vintage span is a *column*, so each ISO writes one partition
``data/clean/uc-params/<ISO>/uc-params.parquet`` (``year=None``) through the
frozen :func:`scripts.lib.clean_io.write_clean` seam. Reads only ``data/raw``;
idempotent; re-run only when the CAMPD source updates (the commit cites the
data change).

Usage:
    PYTHONPATH=. .venv/bin/python scripts/data/derive_uc_cluster_params.py --isos NEISO
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import uc_params as up
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Derive and write every requested ISO's ``uc-params`` partition.

    Args:
        raw_root: Root of the raw tree (defaults to ``paths.RAW_DIR``); tests
            point it at a fixture directory.
        isos: Subset of ISOs to derive (default: every registered ISO). An ISO
            whose footprint has no extract yields an empty frame and is skipped.

    Returns:
        The list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = up.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    written: list[Path] = []
    for iso in wanted:
        if iso not in registry:
            raise SystemExit(
                f"{iso}: no uc-params spec registered (scripts/lib/uc_params/)"
            )
        t0 = time.perf_counter()
        frame = up.derive_iso(iso, raw_root)
        if frame.empty:
            print(f"  {iso}: no CAMPD extract in the footprint — skipped")
            continue
        out = clean_io.write_clean(
            frame,
            up.DATATYPE,
            iso=iso,
            source=(
                f"{_rel(raw_root / 'campd-unit-level')} pooled "
                f"{up.POOLED_VINTAGES[0]}-{up.POOLED_VINTAGES[-1]} via "
                "scripts/data/derive_uc_cluster_params.py"
            ),
            extra_provenance={"pooled_vintages": list(up.POOLED_VINTAGES)},
        )
        clean_io.validate_clean(out)
        n_plants = int((frame["plant_code"] > 0).sum())
        n_fit = int(frame.loc[frame["plant_code"] > 0, "noload_mmbtu_h"].notna().sum())
        print(
            f"  {iso}: {n_plants} clusters ({n_fit} with a no-load fit), "
            f"{len(frame) - n_plants} class-fallback rows, "
            f"{time.perf_counter() - t0:.1f}s -> {_rel(out)}"
        )
        written.append(out)
    return written


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
