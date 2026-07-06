#!/usr/bin/env python
"""Generate full-8760 fillable skeleton input templates (HP-01 §5).

Writes ready-to-fill CSVs for every accepted intake schema --
load-by-facility, hourly LMP (ADR 0011), and annual-average LMP (HP-01,
``data/templates/README.md`` §2b) -- covering a full ``HOURS_PER_YEAR``
calendar per requested ISO, so a user only has to overwrite the placeholder
values instead of hand-building the hour/iso plumbing. Distinct from the
small illustrative examples committed under ``data/templates/`` (a handful of
rows, for reading the schema at a glance): these skeletons are full-size and
gitignored under ``--out-dir`` (default ``data/templates/skeletons/``).

Every skeleton already satisfies its schema's intake validation as generated
(placeholder values are finite and non-negative, every ISO's calendar is
complete) -- a user can round-trip an unmodified skeleton through intake with
zero errors, then overwrite the placeholder values with real data.

Usage (run from inside ``scope2-lce-portfolio/``)::

    ../.venv/bin/python scripts/make_input_templates.py
    ../.venv/bin/python scripts/make_input_templates.py --isos ERCOT CAISO \\
        --out-dir data/templates/skeletons
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]  # scope2-lce-portfolio/
sys.path.insert(0, str(_ROOT / "src"))

from lce_portfolio.config import HOURS_PER_YEAR  # noqa: E402

#: The six real ISOs the tool ships resource/cap/gas-price tables for
#: (``SAMPLE`` is the synthetic demo ISO, not a real-data template target).
DEFAULT_ISOS: tuple[str, ...] = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

#: Placeholder values the user overwrites, chosen so every skeleton already
#: satisfies its schema's intake validation (finite, non-negative) before any
#: filling happens.
PLACEHOLDER_LOAD_MWH = 0.0
PLACEHOLDER_LMP = 0.0
PLACEHOLDER_ANNUAL_AVG_LMP = 0.0

#: Placeholder facility id for the load skeleton (one facility per ISO; the
#: user may split this into as many facility rows as they like -- intake sums
#: them, ADR 0010).
PLACEHOLDER_FACILITY = "facility_1"


def make_load_skeleton(isos: list[str]) -> pd.DataFrame:
    """Full ``HOURS_PER_YEAR`` x ``len(isos)`` load-by-facility skeleton.

    Columns ``(hour, iso, facility, load_mwh)``; every ISO carries the
    complete ``0..HOURS_PER_YEAR-1`` calendar (no Python loop over hours --
    :func:`numpy.tile`/:func:`numpy.repeat` build the columns).
    """
    hours = np.tile(np.arange(HOURS_PER_YEAR), len(isos))
    iso_col = np.repeat(isos, HOURS_PER_YEAR)
    return pd.DataFrame(
        {
            "hour": hours,
            "iso": iso_col,
            "facility": PLACEHOLDER_FACILITY,
            "load_mwh": PLACEHOLDER_LOAD_MWH,
        }
    )


def make_hourly_lmp_skeleton(isos: list[str]) -> pd.DataFrame:
    """Full ``HOURS_PER_YEAR`` x ``len(isos)`` hourly-LMP skeleton (ADR 0011).

    Columns ``(hour, iso, lmp)``, no Python loop over hours.
    """
    hours = np.tile(np.arange(HOURS_PER_YEAR), len(isos))
    iso_col = np.repeat(isos, HOURS_PER_YEAR)
    return pd.DataFrame({"hour": hours, "iso": iso_col, "lmp": PLACEHOLDER_LMP})


def make_annual_average_lmp_skeleton(isos: list[str]) -> pd.DataFrame:
    """One-row-per-ISO annual-average LMP skeleton (HP-01 §2b).

    Columns ``(iso, annual_avg_lmp)``, no ``hour`` column.
    """
    return pd.DataFrame(
        {"iso": list(isos), "annual_avg_lmp": PLACEHOLDER_ANNUAL_AVG_LMP}
    )


def main(argv: list[str] | None = None) -> int:
    """Parse args, write the three skeleton templates under ``--out-dir``."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="+",
        default=list(DEFAULT_ISOS),
        help=f"ISOs to generate rows for (default: {' '.join(DEFAULT_ISOS)})",
    )
    parser.add_argument(
        "--out-dir",
        default=str(_ROOT / "data" / "templates" / "skeletons"),
        help="output directory (default data/templates/skeletons/, gitignored)",
    )
    args = parser.parse_args(argv)

    isos = [str(i).strip().upper() for i in args.isos]
    if not isos:
        parser.error("--isos must name at least one ISO")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    skeletons = {
        "load_8760_by_facility_skeleton.csv": make_load_skeleton(isos),
        "lmp_8760_skeleton.csv": make_hourly_lmp_skeleton(isos),
        "lmp_annual_average_skeleton.csv": make_annual_average_lmp_skeleton(isos),
    }
    for filename, df in skeletons.items():
        path = out_dir / filename
        df.to_csv(path, index=False)
        print(f"wrote {path} ({len(df)} rows, {len(isos)} ISO(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
