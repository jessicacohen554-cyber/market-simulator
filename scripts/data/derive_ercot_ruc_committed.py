"""Derive ERCOT hourly RUC-instructed committed MW by class (ONRUC, LSL).

Writes ``data/raw/ercot-AS/ercot_<year>_ruc_committed_hourly.parquet`` —
columns ``hour`` + ``<class>_lsl_mw`` for class in {CC_REGULAR, ST_GAS,
CT_PEAKER, COAL}: the sum of LSL over units whose ``Telemetered Resource
Status`` snapshot is ``ONRUC`` in that CST hour (hourly mean of snapshot
sums, zero where uncovered — the plan-fallback contract).

ercot-227 F3 (PRECOMMIT-ercot226 §5.11 Amendment 3, owner waiver W-3's
"measured RUC / out-of-market commitment MW"): the RUC INSTRUCTION STATE is
an operator input of the outage-window class (rule 13's admissible example
family) — the instruction and the physical LSL, never realized output (the
D-9 quarantined ``ct_deployment_overlay`` shape) and never a per-unit
model crosswalk (class grain; Q-B stays closed). Source: the NP3-965 60-Day
SCED Gen Resource Data corpus through the committed shard selection
(``derive_ercot_sced_offer_wall``). Clock: CPT→Etc/GMT+6 non-leap 8760
(the derive_ercot_as_responsibility discipline). Sizing record:
``results/calibration/ercot227_ruc_sizing.json`` (2,031 unit-hours,
ST_GAS-dominated). Rule 23: re-derive only on corpus change.

Run:  python3 scripts/data/derive_ercot_ruc_committed.py --year 2023
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

_HERE = Path(__file__).resolve().parent
REPO = _HERE.parents[1]
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(REPO / "src"))

from derive_ercot_dam_cleared_share import _MONTH_START_HOUR  # noqa: E402
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _delivery_year_rows,
    _sced_source_files,
)

_STD_TZ = "Etc/GMT+6"
CLASSES = ("CC_REGULAR", "ST_GAS", "CT_PEAKER", "COAL")
RESTYPE_TO_CLASS = {
    "CLLIG": "COAL",
    "CCGT90": "CC_REGULAR",
    "CCLE90": "CC_REGULAR",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSSUP": "ST_GAS",
    "GSNONR": "ST_GAS",
}
COLS = ["SCED Time Stamp", "Resource Type", "Telemetered Resource Status", "LSL"]
OUT_DIR = REPO / "data" / "raw" / "ercot-AS"


def derive_year(year: int) -> None:
    files = _sced_source_files(year)
    parts = []
    for i, p in enumerate(files):
        df = pd.read_parquet(p, columns=COLS)
        df = _delivery_year_rows(df, year)
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        # Interval coverage marker rows (one per stamp) + the ONRUC rows.
        stamps = df[["SCED Time Stamp"]].drop_duplicates().assign(cls="_cov", lsl=0.0)
        ruc = df[stat == "ONRUC"].copy()
        if not ruc.empty:
            ruc["cls"] = ruc["Resource Type"].map(RESTYPE_TO_CLASS)
            ruc = ruc.dropna(subset=["cls"])
            ruc["lsl"] = pd.to_numeric(ruc["LSL"], errors="coerce").fillna(0.0)
            g = (
                ruc.groupby(["SCED Time Stamp", "cls"], sort=False)["lsl"]
                .sum()
                .reset_index()
            )
            parts.append(
                pd.concat(
                    [g, stamps.rename(columns={"SCED Time Stamp": "SCED Time Stamp"})],
                    ignore_index=True,
                )
            )
        else:
            parts.append(stamps)
        if (i + 1) % 80 == 0:
            print(f"[{year}] scanned {i + 1}/{len(files)}")
    long = pd.concat(parts, ignore_index=True).drop_duplicates(
        subset=["SCED Time Stamp", "cls"], keep="first"
    )
    t = pd.to_datetime(
        long["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    cst = t.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo, dy, hh = cst.dt.month.to_numpy(), cst.dt.day.to_numpy(), cst.dt.hour.to_numpy()
    ok = t.notna().to_numpy() & ~((mo == 2) & (dy == 29))
    hoy = np.full(len(long), -1, dtype=int)
    hoy[ok] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    long = long.loc[ok].assign(hoy=hoy[ok])
    n_int = long[long["cls"] == "_cov"].groupby("hoy")["SCED Time Stamp"].nunique()
    grid = pd.DataFrame({"hour": np.arange(8760, dtype=np.int32)})
    for cls in CLASSES:
        s = long[long["cls"] == cls].groupby("hoy")["lsl"].sum()
        hourly = (s / n_int.reindex(s.index)).reindex(grid["hour"]).fillna(0.0)
        grid[f"{cls}_lsl_mw"] = hourly.to_numpy(float)
        print(
            f"[{year}] {cls}: mean {grid[f'{cls}_lsl_mw'].mean():.1f} MW, "
            f"max {grid[f'{cls}_lsl_mw'].max():.0f}, "
            f"hours>0 {(grid[f'{cls}_lsl_mw'] > 0).sum()}"
        )
    meta = {
        b"source": b"ERCOT NP3-965 60-Day SCED (ONRUC status, LSL)",
        b"description": b"RUC-instructed committed LSL MW by class, hourly "
        b"mean of snapshot sums; zero where uncovered",
        b"units": b"MW",
        b"year": str(year).encode(),
        b"clock": b"CPT->Etc/GMT+6, non-leap 8760",
        b"charter": b"PRECOMMIT-ercot226 section 5.11 Amendment 3 (F3)",
    }
    out = OUT_DIR / f"ercot_{year}_ruc_committed_hourly.parquet"
    pq.write_table(
        pa.Table.from_pandas(grid, preserve_index=False).replace_schema_metadata(meta),
        out,
    )
    print(f"[{year}] wrote {out.name}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--year", type=int, nargs="+", default=[2023])
    args = ap.parse_args()
    for y in args.year:
        derive_year(y)


if __name__ == "__main__":
    main()
