"""Build MISO's actual-LMP reference block from the hourly validation source.

The other multi-zone ISOs (PJM/CAISO/NYISO/NEISO) derive their
``data/raw/_validation-source/actual_lmp.json`` block straight from raw market
price exports in ``scripts/derive_actual_lmp.py``. MISO's raw hub exports are
not staged in the repo; instead the measured hourly system series is already
committed as ``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet``
(columns ``year``, ``hour``, ``rt``, ``da`` on the model's fixed non-leap
8760-hour local calendar — the same sidecar shape the other ISOs' builders
emit). This script reduces that committed parquet to the JSON block the
backcast scorer reads, mirroring the ``_pjm`` record schema exactly:

    "MISO": {"2023": {"da": ..., "rt": ...,
                      "da_mon": [...12...], "rt_mon": [...12...],
                      "da_pct": {min, p1, ..., p99, max},
                      "rt_pct": {...},
                      "src": "..."}, ...}

The block is the SCORING target derived from measured market data — never
pinned to or derived from model output. It is merged into ``actual_lmp.json``
in place; every other ISO's block is left byte-identical (the file round-trips
through ``json.dumps(..., indent=2)``).

Hub -> model-zone mapping: MISO publishes several hub prices (Indiana,
Michigan, Minnesota, Arkansas, Louisiana, Texas). The committed parquet
carries only a single system/representative RT+DA series, so this produces the
system (hub-level) block only — the same top-level fields PJM carries, with no
``zones`` sub-dict. The six model zones (MISO-West / MISO-Plains /
MISO-Illinois / MISO-Indiana / MISO-East / MISO-South) therefore share the
system price for scoring; a zonal block is the scope decision D6 upload
(per-hub RT/DA LMPs) and can be added when the per-hub series are staged
into the parquet.

Usage:
    python scripts/build_miso_lmp_reference.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

# Reuse the exact helpers/constants the other ISO builders use so the MISO
# record is schema-identical (same percentile levels, monthly reducer, calendar
# and output path) rather than a parallel re-implementation that could drift.
from derive_actual_lmp import (  # noqa: E402
    OUT,
    _HOURS_PER_YEAR,
    _MONTH_START_HOUR,
    _by_month,
    _pct,
)
from market_sim.config import paths  # noqa: E402  (resolves the data root)

DEFAULT_YEARS = (2023, 2024, 2025)
HOURLY_PARQUET = paths.CALIBRATION_DIR / "actual_lmp_hourly_MISO.parquet"
MISO_SRC = (
    "MISO RT/DA LMP, system hub-average hourly series (actual_lmp_hourly_MISO.parquet)"
)


def _month_of_hour() -> np.ndarray:
    """Month label (1-12) for each fixed non-leap hour-of-year (0..8759).

    The dense parquet calendar is the same Feb-29-dropped clock used by
    ``derive_actual_lmp._hour_index``; ``_MONTH_START_HOUR`` gives each month's
    starting hour, so a searchsorted over those bounds recovers the month for
    every hour. Lets the monthly reducer reuse ``_by_month`` unchanged.
    """
    bounds = np.asarray(_MONTH_START_HOUR[1:])  # starts of Feb..Dec
    return np.searchsorted(bounds, np.arange(_HOURS_PER_YEAR), side="right") + 1


def _record(g: pd.DataFrame, months: np.ndarray) -> dict:
    """Build one year's ``{da, rt, da_mon, rt_mon, da_pct, rt_pct, src}`` record.

    ``g`` is the year's dense hourly frame (``hour`` 0..8759, ``rt``/``da``
    columns, NaN where the local calendar has no value); ``months`` the matching
    per-hour month labels. Means/percentiles ignore NaN, exactly as the other
    ISO builders do.
    """
    g = g.sort_values("hour")
    rt = g["rt"].to_numpy(float)
    da = g["da"].to_numpy(float)
    return {
        "da": round(float(np.nanmean(da)), 2),
        "rt": round(float(np.nanmean(rt)), 2),
        "da_mon": _by_month(da, months),
        "rt_mon": _by_month(rt, months),
        "da_pct": _pct(da),
        "rt_pct": _pct(rt),
        "src": MISO_SRC,
    }


def build(years) -> dict:
    """Return ``{str(year): record}`` for MISO over ``years`` present in the parquet."""
    df = pd.read_parquet(HOURLY_PARQUET)
    months = _month_of_hour()
    out: dict[str, dict] = {}
    for year in years:
        g = df[df["year"] == int(year)]
        if g.empty:
            continue
        rec = _record(g, months)
        out[str(int(year))] = rec
        print(f"  MISO {year}: da ${rec['da']} rt ${rec['rt']}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    block = build(args.years)
    if not block:
        raise SystemExit(f"no MISO years built from {HOURLY_PARQUET}")
    # Merge in place: load the committed reference, replace only the MISO block,
    # and re-dump with the same indent so every other ISO stays byte-identical.
    merged: dict[str, dict] = {}
    if OUT.exists():
        merged = json.loads(OUT.read_text())
    merged.setdefault("MISO", {}).update(block)
    OUT.write_text(json.dumps(merged, indent=2) + "\n")
    print(f"wrote {OUT} (MISO: {len(block)} years)")


if __name__ == "__main__":
    main()
