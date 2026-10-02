#!/usr/bin/env python3
"""Write PJM's per-MODEL-zone hourly LMP archive (the zone-resolved C3a/C3b actual).

Output: ``data/raw/_validation-source/actual_lmp_zonal_PJM.parquet`` with columns
``year, hour, zone, rt, da`` — one dense 8760 series per PJM model zone per year,
on the same chronological standard-time calendar (EST, ``Etc/GMT+5``) as
``actual_lmp_hourly_PJM.parquet`` (``derive_actual_lmp._densify_std``).

Source: PJM DataMiner2 ``rt_hrl_lmps`` / ``da_hrl_lmps`` rows filtered to
``type = ZONE`` (the load-weighted transmission-zone price PJM publishes for
each of its 21 zones), staged by ``scripts/data/fetch_pjm_zonal_lmp_components.py``
under ``data/raw/pjm-zonal-lmp/`` (gitignored — DataMiner2 non-member
redistribution term, ``docs/data-licensing.md`` §4; the sha256 manifest is the
provenance record). Only this reduced per-model-zone derivative is committed.

Each model zone's series is the simple mean of its constituent transmission
zones' ``total_lmp`` — the same construction ``derive_actual_lmp`` uses for
NYISO (simple mean of constituent NYISO zones) and MISO (simple mean of a
multi-hub zone's hubs). The zone -> model-zone crosswalk is the canonical
``market_sim.data.eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS`` (keyed by EIA-930
subregion code), renamed to DataMiner2 pnode names by :data:`EIA930_TO_DATAMINER`.

Read by ``derive_actual_lmp._lw_fields`` through ``ZONAL_LW_SOURCES["PJM"]``
(owner ruling R-13, 2026-10-02: "adopt zonal load-weighted C3a for PJM", as
NYISO / MISO). Rule 13: the actual is a benchmark, never a model input.

Usage::

    python scripts/data/fetch_pjm_zonal_lmp_components.py --years 2019 ... 2025
    python scripts/data/derive_pjm_zonal_lmp.py --years 2019 2020 2021 2022 2023 2024 2025
    python scripts/data/derive_actual_lmp.py --lw-retrofit --isos PJM --years 2019 ... 2025
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

from market_sim.config import paths  # noqa: E402
from market_sim.data.eia930.zonal_shares import _PJM_LOAD_ZONE_GROUPS  # noqa: E402
from scripts.data import derive_actual_lmp as dal  # noqa: E402

SRC_DIR: Path = paths.RAW_DATA_DIR / "pjm-zonal-lmp"

#: EIA-930 PJM subregion code -> PJM DataMiner2 ZONE pnode name. Codes that
#: already match (AEP, DAY, DEOK, OVEC, ATSI, DUQ, EKPC, DOM, DPL, RECO) map to
#: themselves.
EIA930_TO_DATAMINER: dict[str, str] = {
    "CE": "COMED",
    "AP": "APS",
    "PL": "PPL",
    "PN": "PENELEC",
    "ME": "METED",
    "PS": "PSEG",
    "JC": "JCPL",
    "PE": "PECO",
    "AE": "AECO",
    "BC": "BGE",
    "PEP": "PEPCO",
}


def model_zone_to_pnodes() -> dict[str, tuple[str, ...]]:
    """Model zone -> its constituent DataMiner2 ZONE pnodes (canonical crosswalk)."""
    out: dict[str, list[str]] = {}
    for code, zone in _PJM_LOAD_ZONE_GROUPS.items():
        out.setdefault(zone, []).append(EIA930_TO_DATAMINER.get(code, code))
    return {z: tuple(sorted(v)) for z, v in out.items()}


def _read_feed(feed: str, year: int) -> pd.DataFrame | None:
    """Every staged month of ``feed`` for ``year`` (plus Jan of year+1 for the edge)."""
    files = sorted(SRC_DIR.glob(f"{feed}_{year:04d}_*.parquet"))
    nxt = SRC_DIR / f"{feed}_{year + 1:04d}_01.parquet"
    if nxt.exists():
        files.append(nxt)
    if not files:
        return None
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def zonal_frame(year: int) -> pd.DataFrame | None:
    """Long ``year, hour, zone, rt, da`` frame for one year, or ``None`` if unstaged."""
    crosswalk = model_zone_to_pnodes()
    dense: dict[str, dict[str, np.ndarray]] = {z: {} for z in crosswalk}
    any_feed = False
    for feed, kind in (("rt_hrl_lmps", "rt"), ("da_hrl_lmps", "da")):
        df = _read_feed(feed, year)
        if df is None:
            continue
        any_feed = True
        utc = pd.to_datetime(
            df["datetime_beginning_utc"], format="%m/%d/%Y %I:%M:%S %p", utc=True
        )
        df = df.assign(utc=utc)
        col = f"total_lmp_{kind}"
        for zone, pnodes in crosswalk.items():
            sub = df[df["pnode_name"].isin(pnodes)]
            ser = sub.groupby("utc")[col].mean()  # simple mean of constituents
            dense[zone][kind] = dal._densify_std(ser, year, dal._STD_TZ["PJM"])
    if not any_feed:
        return None
    n = dal._HOURS_PER_YEAR
    rows = [
        pd.DataFrame(
            {
                "year": np.int16(year),
                "hour": np.arange(n, dtype=np.int16),
                "zone": zone,
                "rt": d.get("rt", np.full(n, np.nan)).astype(np.float32),
                "da": d.get("da", np.full(n, np.nan)).astype(np.float32),
            }
        )
        for zone, d in dense.items()
    ]
    return pd.concat(rows, ignore_index=True)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, required=True)
    a = ap.parse_args()
    out = dal.HOURLY_OUT / dal.PJM_ZONAL_PARQUET
    parts = []
    for y in a.years:
        f = zonal_frame(y)
        if f is None:
            print(f"  {y}: no staged source — skipped")
            continue
        print(
            f"  {y}: {len(f)} rows, rt NaN {int(f.rt.isna().sum())}, "
            f"da NaN {int(f.da.isna().sum())}"
        )
        parts.append(f)
    df = pd.concat(parts, ignore_index=True).sort_values(
        ["year", "zone", "hour"], kind="stable"
    )
    df.to_parquet(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    main()
