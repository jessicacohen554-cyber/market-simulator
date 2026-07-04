"""Curate the ``winter-fuel-inventory`` clean datatype.

Lands the forward-derivable capacity/logistics quantities that size a
winter-season (Nov-Mar) oil-burn energy budget for the fuel-constrained fleet
(component A of ``docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md``),
onto the single tidy schema in
``data/dictionary/schema/winter-fuel-inventory.schema.yaml`` and writes each ISO
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Two sources feed one schema (see
``scripts/lib/winter_fuel_inventory/__init__.py``): the committed EIA-860 tables
(per-plant oil-limb MW + petroleum firing rate, derived programmatically) and a
hand-curated ISO-NE study/program CSV (fleet/system/program figures with
citations). Per-ISO parsing lives in
``scripts/lib/winter_fuel_inventory/<iso>.py`` (each registers an
:class:`~scripts.lib.winter_fuel_inventory.IsoSpec`); this script is a thin
dispatcher over the registry, so adding an ISO never touches it. The vintage /
season / study year is a *column*, so each ISO writes one partition
``data/clean/winter-fuel-inventory/<ISO>/…parquet`` (``year=None``). Reads only
``data/raw``; idempotent. Run
``python scripts/curate_winter_fuel_inventory.py [--isos ISONE ...]``.

ADMISSIBILITY GUARD (CLAUDE.md #11/#13): this datatype carries physical/market
INPUTS only (tank capacity, start fill, delivery rate, firing rate, oil-limb
MW). Measured burn/delivery *outcomes* (F923 petroleum receipts) are
inadmissible as budget drivers and must never be intaken here — see
``docs/multi-iso/neiso-winter-fuel-data-audit.md``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import winter_fuel_inventory as wfi
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
    """Curate and write every requested ISO's winter-fuel-inventory partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory. Both the EIA-860 tables (``<raw_root>/eia-860``)
        and the study CSV (``<raw_root>/winter-fuel-inventory/<iso>``) resolve
        beneath it.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO with
        no EIA-860 rows and no study CSV yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = wfi.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = wfi.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no EIA-860 rows and no study CSV under {_rel(raw_root)}"
            )
            continue
        source = (
            f"{_rel(wfi.eia860_dir(raw_root))} + {_rel(wfi.raw_dir_for(iso, raw_root))}"
        )
        path = clean_io.write_clean(df, wfi.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        n_plant = int((df["entity_type"] == "plant").sum())
        n_other = len(df) - n_plant
        print(
            f"wrote {path}  ({len(df)} rows: {n_plant} EIA-860 plant, {n_other} study)"
        )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: every registered ISO)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
