#!/usr/bin/env python3
"""Write NYISO's per-MODEL-zone hourly LBMP archive (the zone-resolved C3a/C3b actual).

Output: ``data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet`` with
columns ``year, hour, zone, rt, da`` — one dense 8760/8784 series per model zone
per year, on the same chronological standard-time calendar as
``actual_lmp_hourly_NYISO.parquet`` (``derive_actual_lmp._densify_std``).

Each model zone's series is ``derive_actual_lmp.nyiso_zone_hourly`` — the simple
mean of its constituent NYISO internal zones (``NYISO_ZONE_MAP``), RT = the RTD
5-minute prices averaged to the hour (interval-ending, adjudicated P-4A clock),
DA = the DAM hourly product. The source is NYISO's public MIS archive, staged by
``scripts/data/fetch_nyiso_zonal_lmp.py`` (gitignored). No new construction: the
same frame already feeds ``actual_lmp.json``'s ``zones`` sub-dict and its hub.

Read by ``derive_actual_lmp._lw_fields`` through ``ZONAL_LW_SOURCES["NYISO"]``
(owner ruling 2026-10-01, NYISO-NEXT-22, "Adopt for NYISO now"). Rule 13: the
actual is a benchmark, never a model input.

Usage::

    python scripts/data/fetch_nyiso_zonal_lmp.py --start 201801 --end 202512 --kind both
    python scripts/data/derive_nyiso_zonal_lmp.py --years 2018 2019 2020 2021 2022 2023 2024 2025
    python scripts/data/derive_actual_lmp.py --lw-retrofit --isos NYISO --years 2018 ... 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.data import derive_actual_lmp as dal  # noqa: E402


def zonal_frame(year: int) -> pd.DataFrame | None:
    """Long ``year, hour, zone, rt, da`` frame for one year, or ``None`` if unstaged."""
    frames = {k: dal.nyiso_zone_hourly(year, k) for k in ("rt", "da")}
    if frames["rt"] is None and frames["da"] is None:
        return None
    std = dal._STD_TZ["NYISO"]
    rows = []
    for zone in dal.NYISO_ZONE_MAP:
        dense = {}
        for kind, fr in frames.items():
            if fr is None or zone not in fr.columns:
                dense[kind] = None
            else:
                dense[kind] = dal._densify_std(fr[zone], year, std)
        n = len(next(d for d in dense.values() if d is not None))
        rows.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(n, dtype=np.int16),
                    "zone": zone,
                    "rt": (
                        dense["rt"] if dense["rt"] is not None else np.full(n, np.nan)
                    ).astype(np.float32),
                    "da": (
                        dense["da"] if dense["da"] is not None else np.full(n, np.nan)
                    ).astype(np.float32),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, required=True)
    a = ap.parse_args()
    out = dal.HOURLY_OUT / dal.NYISO_ZONAL_PARQUET
    parts = []
    for y in a.years:
        f = zonal_frame(y)
        if f is None:
            print(f"  {y}: no staged source — skipped")
            continue
        print(
            f"  {y}: {len(f)} rows, rt NaN {int(f.rt.isna().sum())}, da NaN {int(f.da.isna().sum())}"
        )
        parts.append(f)
    df = pd.concat(parts, ignore_index=True).sort_values(
        ["year", "zone", "hour"], kind="stable"
    )
    df.to_parquet(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
