#!/usr/bin/env python3
"""AUDIT-FOLLOWUP row O4 — re-measure the CC availability envelope at HEAD.

Audit row O4 grounds the ACTIVE holdout spend freeze on the neiso-63 finding
that the CAMPD unit-outage detector books sustained economic layup as mechanical
outage, at 23-46 % of the CC capacity-year against a real EFOR+planned norm of
~10-15 %. The merit-order guard was ADOPTED 2026-07-26 (charter section 8) and
every ISO's extract re-derived guard-on, so the row's premise has to be
RE-MEASURED at HEAD rather than carried from the register's July snapshot: the
question is whether adopting the guard moved the envelope into the norm band.

WHAT THIS MEASURES, from committed artifacts only, NO LP SOLVE:

  kept_outage_share   the CC_REGULAR capacity-weighted outage fraction of the
                      capacity-year in the extract THE LP ACTUALLY READS
                      (data/raw/campd-unit-outages[-<ISO>].csv) -- i.e. the
                      post-guard envelope every current keeper inherits.
  layup_removed_share the same fraction over the guard's layup companion
                      (campd-unit-outages-layup[-<ISO>].csv), which holds the
                      windows the guard RECLASSIFIED out of the envelope.
  pre_guard_total     their sum -- the envelope as it stood before the guard,
                      the construction the neiso-63 23-46 % range measured.

Denominator is the union of both files' CC_REGULAR units, so a unit whose every
window was reclassified still counts in the fleet capacity and the two shares
are directly comparable. Windows are clipped to the calendar year, so a window
spanning a year boundary contributes to each year only its own overlap.

Reads: data/raw/campd-unit-outages*.csv (ERCOT is the unsuffixed pair).
Writes: results/calibration/_audit_followup_o4_cc_envelope.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"
OUT = REPO / "results" / "calibration" / "_audit_followup_o4_cc_envelope.json"

# ERCOT is the original unsuffixed pair; the other five carry an -<ISO> suffix.
EXTRACTS: dict[str, tuple[str, str]] = {
    "ERCOT": ("campd-unit-outages.csv", "campd-unit-outages-layup.csv"),
    **{
        iso: (f"campd-unit-outages-{iso}.csv", f"campd-unit-outages-layup-{iso}.csv")
        for iso in ("CAISO", "PJM", "MISO", "NYISO", "NEISO")
    },
}
YEARS = (2023, 2024, 2025)
CC_CLASS = "CC_REGULAR"
# The real EFOR + planned-outage norm the neiso-63 finding scored against
# (results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md).
NORM_BAND = (0.10, 0.15)


def overlap_days(df: pd.DataFrame, year: int) -> pd.Series:
    """Days of each outage window falling inside ``year``.

    Windows are clipped to [Jan 1, Jan 1 next year) and floored at zero, so a
    multi-year window contributes only its own overlap to each year.
    """
    start = pd.to_datetime(df["outage_start"]).clip(lower=pd.Timestamp(f"{year}-01-01"))
    end = pd.to_datetime(df["outage_end"]).clip(upper=pd.Timestamp(f"{year + 1}-01-01"))
    return ((end - start).dt.total_seconds() / 86400.0).clip(lower=0)


def measure_iso(kept_path: Path, layup_path: Path) -> dict:
    """CC_REGULAR envelope shares for one ISO, kept vs guard-reclassified."""
    kept = pd.read_csv(kept_path)
    layup = pd.read_csv(layup_path) if layup_path.exists() else kept.iloc[0:0]
    both = pd.concat(
        [kept.assign(_src="kept"), layup.assign(_src="layup")], ignore_index=True
    )
    cc = both[both["plant_group"] == CC_CLASS].copy()
    units = cc.drop_duplicates(subset=["facility_id", "unit_id"])
    fleet_mw = float(units["unit_capacity_mw"].sum())

    row: dict = {"cc_units": int(len(units)), "cc_capacity_mw": round(fleet_mw, 1)}
    for year in YEARS:
        cc["_days"] = overlap_days(cc, year)
        mw_days = cc.groupby("_src").apply(
            lambda g: float((g["unit_capacity_mw"] * g["_days"]).sum()),
            include_groups=False,
        )
        denom = fleet_mw * 365.0
        k = float(mw_days.get("kept", 0.0)) / denom
        lay = float(mw_days.get("layup", 0.0)) / denom
        row[str(year)] = {
            "kept_outage_share": round(k, 4),
            "layup_removed_share": round(lay, 4),
            "pre_guard_total": round(k + lay, 4),
            "kept_above_norm_pp": round((k - NORM_BAND[1]) * 100, 2),
        }
    return row


def main() -> int:
    """Measure every ISO and write the JSON record."""
    result: dict = {
        "probe": "audit-followup/o4-cc-envelope",
        "audit_row": "O4",
        "no_lp_solve": True,
        "norm_band": list(NORM_BAND),
        "years": list(YEARS),
        "class": CC_CLASS,
        "isos": {},
    }
    for iso, (kept_name, layup_name) in EXTRACTS.items():
        kept_path = RAW / kept_name
        if not kept_path.exists():
            print(f"{iso}: SKIPPED (no {kept_name} — hydrate the ISO's profile)")
            continue
        result["isos"][iso] = measure_iso(kept_path, RAW / layup_name)

    kept_all = [
        y["kept_outage_share"]
        for iso in result["isos"].values()
        for k, y in iso.items()
        if k.isdigit()
    ]
    pre_all = [
        y["pre_guard_total"]
        for iso in result["isos"].values()
        for k, y in iso.items()
        if k.isdigit()
    ]
    if kept_all:
        result["summary"] = {
            "kept_share_range": [round(min(kept_all), 4), round(max(kept_all), 4)],
            "pre_guard_range": [round(min(pre_all), 4), round(max(pre_all), 4)],
            "n_iso_years": len(kept_all),
            "n_iso_years_above_norm": sum(1 for v in kept_all if v > NORM_BAND[1]),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    if "summary" in result:
        s = result["summary"]
        print(
            f"  kept CC outage share {s['kept_share_range'][0]:.1%}"
            f"-{s['kept_share_range'][1]:.1%} "
            f"(pre-guard {s['pre_guard_range'][0]:.1%}-{s['pre_guard_range'][1]:.1%}); "
            f"{s['n_iso_years_above_norm']}/{s['n_iso_years']} ISO-years above the "
            f"{NORM_BAND[1]:.0%} norm ceiling"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
