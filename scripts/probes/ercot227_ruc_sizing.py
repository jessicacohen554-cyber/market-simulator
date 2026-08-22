"""ercot-227 F3 Phase-0: size the 2023 ONRUC (RUC-instructed) footprint.

The ercot97 Lane B sizing re-run ON THE 2023 DELIVERY MONTHS (Amendment 3):
the original 303-unit-hour IMMATERIAL verdict was measured on 2024/2025
slim tail-day subsets because the 2023 SCED corpus was absent; it is now on
disk (pubs 2023-03..2024-03), and 2023 is the year the IMM's
artificial-shortage record says RUC ran hot. Counts ONRUC unit-intervals by
class x month x hour-of-day with HSL/LSL/Base-Point levels, against the
keeper gas bridge's ~50,000-unit-hour committed state (the ercot97
materiality yardstick, and rule 19's incumbent).

Writes ``results/calibration/ercot227_ruc_sizing.json``. Solve-free.

Run:  python3 scripts/probes/ercot227_ruc_sizing.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_sced_offer_wall import (  # noqa: E402
    _delivery_year_rows,
    _sced_source_files,
)

YEAR = 2023
_UH = 5.0 / 60.0  # nominal SCED interval; the corpus snapshots ~15-min, so
# ALSO report interval-count-based hours from the observed cadence.
_BRIDGE_UNIT_HOURS = 50_000
COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "LSL",
    "Base Point",
]
RESTYPE_TO_CLASS = {
    "CLLIG": "COAL",
    "CCGT90": "CC_REGULAR",
    "CCLE90": "CC_REGULAR",
    "SCGT90": "CT_PEAKER",
    "SCLE90": "CT_PEAKER",
    "GSREH": "ST_GAS",
    "GSSUP": "ST_GAS",
    "GSNONR": "ST_GAS",
    "PWRSTR": "STORAGE",
}


def main() -> None:
    files = _sced_source_files(YEAR)
    parts = []
    n_int_all = 0
    for i, p in enumerate(files):
        try:
            df = pd.read_parquet(p, columns=COLS)
        except Exception:
            df = pd.read_parquet(p)
            df = df[[c for c in COLS if c in df.columns]]
        df = _delivery_year_rows(df, YEAR)
        if df.empty:
            continue
        n_int_all += df["SCED Time Stamp"].nunique()
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        ruc = df[stat == "ONRUC"].copy()
        if not ruc.empty:
            parts.append(ruc)
        if (i + 1) % 60 == 0:
            print(f"scanned {i + 1}/{len(files)} shards, "
                  f"{sum(len(x) for x in parts)} ONRUC rows so far")
    if not parts:
        out = {"probe": "ercot227_ruc_sizing", "year": YEAR,
               "onruc_rows": 0, "verdict": "ZERO ONRUC rows in delivery-2023"}
        Path(REPO / "results/calibration/ercot227_ruc_sizing.json").write_text(
            json.dumps(out, indent=1))
        print(json.dumps(out, indent=1))
        return
    ruc = pd.concat(parts, ignore_index=True)
    ts = pd.to_datetime(ruc["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    ruc["hod"] = ts.dt.hour
    ruc["month"] = ts.dt.month
    ruc["cls"] = ruc["Resource Type"].map(lambda t: RESTYPE_TO_CLASS.get(t, t))
    for c in ("HSL", "LSL", "Base Point"):
        ruc[c] = pd.to_numeric(ruc[c], errors="coerce")

    # Observed cadence: distinct stamps per (day) — snapshots/hour.
    per_day = ts.dt.normalize().value_counts()
    days = int(ts.dt.normalize().nunique())

    by_cls = (
        ruc.groupby("cls")
        .agg(rows=("HSL", "size"), mean_hsl=("HSL", "mean"),
             mean_lsl=("LSL", "mean"), mean_bp=("Base Point", "mean"),
             units=("Resource Name", "nunique"))
        .round(1)
    )
    print("\n=== delivery-2023 ONRUC by class ===")
    print(by_cls.to_string())
    by_month = ruc.groupby("month").size()
    by_hod = ruc.groupby("hod").size()
    # Distinct (unit, hour) pairs = unit-hours regardless of snapshot cadence.
    uh = ruc.assign(day=ts.dt.normalize(), hr=ts.dt.hour)
    unit_hours = int(uh.groupby(["Resource Name", "day", "hr"]).ngroups)
    print(f"\nONRUC rows {len(ruc)}, distinct unit-hours {unit_hours}, "
          f"days touched {days}")
    print(f"vs keeper gas bridge ~{_BRIDGE_UNIT_HOURS} unit-hours "
          f"-> ratio {unit_hours / _BRIDGE_UNIT_HOURS:.4f}")

    out = {
        "probe": "ercot227_ruc_sizing",
        "charter": "PRECOMMIT-ercot226 §5.11 Amendment 3, F3 (ercot97 Lane B "
        "re-run on delivery-2023 — new evidence)",
        "year": YEAR,
        "onruc_rows": int(len(ruc)),
        "onruc_unit_hours": unit_hours,
        "days_touched": days,
        "by_class": json.loads(by_cls.to_json(orient="index")),
        "by_month_rows": {str(k): int(v) for k, v in by_month.items()},
        "by_hod_rows": {str(k): int(v) for k, v in by_hod.items()},
        "bridge_unit_hours_yardstick": _BRIDGE_UNIT_HOURS,
        "ratio_vs_bridge": round(unit_hours / _BRIDGE_UNIT_HOURS, 4),
        "ercot97_prior": "303 unit-hours on 2024/2025 slim subsets (178x "
        "below the bridge) — IMMATERIAL, step 2 not triggered",
    }
    Path(REPO / "results/calibration/ercot227_ruc_sizing.json").write_text(
        json.dumps(out, indent=1))
    print("wrote results/calibration/ercot227_ruc_sizing.json")


if __name__ == "__main__":
    main()
