"""caiso-146 side-check: how much of each ISO's measured CT heat rate is set by
physically-impossible METER HOURS rather than by the machine.

Context. ``derive_campd_ct_heat_rates.py`` guards its output with a physical
band ``[6.0, 25.0]`` MMBtu/MWh applied to the **plant aggregate** — the script's
own docstring calls it "a DATA-INTEGRITY guard on the meter, not a tuning knob"
and says a value below 6.0 means "a mis-tagged combined cycle" or "a broken
heat-input channel". CAISO's Delano Energy Center (58122) shows the gap that
grain leaves: its loaded-hour heat rates run p05 = 0.81 / p25 = 3.20 against a
median of 7.89, so a minority of hours with under-reported ``heatInput`` drag
the plant aggregate to 6.507 — *below* any real simple-cycle machine, yet just
**above** the 6.0 floor, so the guard passes it.

This probe measures — read-only, changing nothing — how many units in EACH ISO's
CT population carry such hours, and what the plant rate would be if the same
declared physical floor were applied per HOUR before aggregating. It exists to
size the blast radius of an hour-grain screen across the three ISOs that already
hold COMMITTED artifacts and keepers built on them (NYISO nyiso-89, PJM pjm-137,
MISO miso-99), so the question can be handed on with a number attached instead
of a guess. It deliberately does not modify the shared derive: a change there
would move three committed keepers' inputs, which is not a CAISO session's to
make (rules 24 [R-FROZEN-DERIVE] / 25 [R-ISO-SCOPE]).

Usage::

    PYTHONPATH=.:src .venv/bin/python \
        scripts/probes/_caiso146_hourly_hr_integrity.py --iso CAISO NYISO PJM MISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

YEARS = (2023, 2024, 2025)
TARGET_CLASS = "CT_PEAKER"
CT_UNIT_TYPE = "combustion turbine"
UNIT_DIR = RAW_DIR / "campd-unit-level"

#: The derive's own declared physical floor, re-used unchanged at hour grain.
HR_FLOOR = 6.0
_LOADED_FRAC, _CAP_PCTILE, _MIN_LOADED_HOURS = 0.80, 95.0, 50


def class_codes(iso: str) -> set[int]:
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    return {
        int(g.plant_code)
        for g in fleet
        if g.plant_group == TARGET_CLASS and int(g.plant_code or 0)
    }


def audit(iso: str) -> pd.DataFrame:
    codes = class_codes(iso)
    frames = []
    for state in campd.states_for_iso(iso):
        for year in YEARS:
            path = UNIT_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=["facilityId", "facilityName", "unitId", "unitType",
                         "grossLoad", "heatInput"],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(codes)]
            df = df[df["unitType"].astype(str).str.strip().str.casefold() == CT_UNIT_TYPE]
            if not df.empty:
                frames.append(df)
    if not frames:
        return pd.DataFrame()
    p = pd.concat(frames, ignore_index=True).dropna(subset=["grossLoad", "heatInput"])
    p = p[(p["grossLoad"] > 0.0) & (p["heatInput"] > 0.0)]

    rows = []
    for (code, unit), g in p.groupby(["facilityId", "unitId"], sort=True):
        cap = float(np.percentile(g["grossLoad"], _CAP_PCTILE))
        ld = g[g["grossLoad"] >= _LOADED_FRAC * cap]
        if len(ld) < _MIN_LOADED_HOURS:
            continue
        hr_h = (ld["heatInput"] / ld["grossLoad"]).to_numpy(float)
        bad = hr_h < HR_FLOOR
        keep = ld[~bad]
        rows.append({
            "plant_code": int(code),
            "plant_name": str(g["facilityName"].iloc[0]),
            "unit_id": str(unit),
            "loaded_h": int(len(ld)),
            "bad_h": int(bad.sum()),
            "bad_pct": round(100.0 * bad.mean(), 2),
            "gross_mwh": float(ld["grossLoad"].sum()),
            "hr_as_is": float(ld["heatInput"].sum() / ld["grossLoad"].sum()),
            "hr_screened": (
                float(keep["heatInput"].sum() / keep["grossLoad"].sum())
                if len(keep) else float("nan")
            ),
        })
    d = pd.DataFrame(rows)
    if d.empty:
        return d
    d["delta"] = d["hr_screened"] - d["hr_as_is"]
    d["iso"] = iso
    return d


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=["CAISO", "NYISO", "PJM", "MISO"])
    args = ap.parse_args()

    for iso in args.iso:
        d = audit(iso)
        print("=" * 78)
        if d.empty:
            print(f"{iso}: no qualifying CT units")
            continue
        art_path = PROCESSED_DIR / f"campd_ct_heat_rates_{iso}.csv"
        committed = art_path.exists()
        gross = d["gross_mwh"].sum()
        print(f"{iso} — {len(d)} qualifying CT units, committed artifact: {committed}")
        print(f"  units with ANY sub-{HR_FLOOR} loaded hour: "
              f"{(d['bad_h'] > 0).sum()} / {len(d)}")
        print(f"  loaded hours below the floor: {int(d['bad_h'].sum()):,} / "
              f"{int(d['loaded_h'].sum()):,} ({100 * d['bad_h'].sum() / d['loaded_h'].sum():.2f} %)")
        print(f"  energy-weighted unit HR  as-is {np.average(d['hr_as_is'], weights=d['gross_mwh']):.4f}"
              f"  screened {np.average(d['hr_screened'], weights=d['gross_mwh']):.4f}"
              f"  (delta {np.average(d['delta'], weights=d['gross_mwh']):+.4f})")
        moved = d[d["delta"].abs() > 0.25].sort_values("delta", ascending=False)
        print(f"  units moving > 0.25 MMBtu/MWh under an hour-grain floor: {len(moved)}"
              f"  ({100 * moved['gross_mwh'].sum() / gross:.2f} % of class CT energy)")
        if len(moved):
            print(moved[["plant_code", "plant_name", "unit_id", "loaded_h", "bad_h",
                         "bad_pct", "hr_as_is", "hr_screened", "delta"]]
                  .to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
