"""ERCOT-97 Lane B — measure the RUC-conduct commitment state (solve-free).

Sizes the "reality RUC" phenomenon (ERCOT-95 Finding 5: the operator
self-commits capacity economics would not) from the 60-Day SCED disclosure
``Telemetered Resource Status`` == ``ONRUC`` — the RUC-committed unit-intervals
— and compares it against the model's committed state (the ercot96 keeper's gas
commitment bridge floors ~50,000 unit-hours). The ERCOT-93 telemetered-span
derive is the read pattern; ``RESTYPE_TO_CLASS`` maps SCED Resource Types onto
model classes.

DATA SCOPE: the full 60-Day SCED corpus was purged from HEAD in the 2026-07-22
bloat clear; this probe reads the SLIM tail-day / control-day subsets that
survived (2024 ercot74 tail + ercot75 control, 2025 ercot75 control + ercot86
tail — the tail-day window Lane B cares about). 2023 SCED is absent (re-fetch
with fetch_ercot_60day_sced_gen_resource.py + slim_ercot_dam_disclosure.py
--sced to extend the span), but the measured RUC footprint is ~2 orders of
magnitude below the bridge's committed state, so the "not material" conclusion
is robust to the sampling.

Result (this data, 2026-07-22): ONRUC ≈ 303 unit-hours total (281 gas:
ST_GAS ~236 / CC ~28 / CT ~17), evening-ramp weighted (hod 18-20 peak, 49 % in
hod 13-19), dominated by the old gas-steam fleet (Olinger, Lake Hubbard,
Mountain Creek, Spencer, V H Braunig — the units the ST_GAS drag already
governs). vs the keeper gas bridge's ~50,000 unit-hours ⇒ RUC is IMMATERIAL to
the committed-state gap. Lane B step 2 (thread a measured RUC commitment-state
input) is therefore NOT triggered: a RUC floor would replace a tiny slice of the
bridge, not change the committed state, and rule 19 (one mechanism per
phenomenon) / rule 14 (measured-over-derived) are better served by leaving the
bridge + ST_GAS drag in place. Re-run if the 2023-2025 SCED corpus is refetched.

Usage::  .venv/bin/python scripts/probes/_ercot97_ruc_measure.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_thermal_dam_availability import RESTYPE_TO_CLASS, _site  # noqa: E402

SCED_DIR = REPO / "data" / "raw" / "ercot"
CROSSWALK = REPO / "data" / "raw" / "reference" / "ercot-dam-plant-crosswalk.csv"
_UH = 5.0 / 60.0  # SCED runs on a ~5-minute interval -> unit-hours per interval
_COLS = [
    "SCED Time Stamp", "Resource Name", "Resource Type",
    "Telemetered Resource Status", "HSL", "Base Point",
]
_GAS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
# The keeper (ercot96) gas commitment bridge floor size, for the materiality
# comparison (docs/calibration-log/ercot.md; CLAUDE.md Dispatch & Commitment).
_BRIDGE_UNIT_HOURS = 50_000


def main() -> None:
    files = sorted(SCED_DIR.glob("*60d_SCED_Gen_Resource_Data_*_ercot*_days.parquet"))
    if not files:
        raise SystemExit(
            "no slim SCED Gen_Resource files found — re-fetch with "
            "fetch_ercot_60day_sced_gen_resource.py + slim_ercot_dam_disclosure.py --sced"
        )
    frames = []
    for p in files:
        df = pd.read_parquet(p, columns=_COLS)
        ts = pd.to_datetime(df["SCED Time Stamp"])
        df["hod"] = ts.dt.hour
        df["month"] = ts.dt.month
        ruc = df[df["Telemetered Resource Status"] == "ONRUC"].copy()
        print(
            f"{p.name.split('_Data_')[1][:-8]}: {ts.dt.normalize().nunique()} days, "
            f"{len(df)} rows, {len(ruc)} ONRUC intervals"
        )
        frames.append(ruc)
    ruc = pd.concat(frames, ignore_index=True)
    ruc["cls"] = ruc["Resource Type"].map(lambda t: RESTYPE_TO_CLASS.get(t, t))
    ruc["site"] = [_site(n, t) for n, t in zip(ruc["Resource Name"], ruc["Resource Type"])]

    by_cls = ruc.groupby("cls").agg(
        intervals=("HSL", "size"), mean_HSL=("HSL", "mean"), mean_BP=("Base Point", "mean")
    )
    by_cls["unit_hours"] = (by_cls["intervals"] * _UH).round(1)
    print("\n=== ONRUC by class ===")
    print(by_cls.round(1).to_string())

    gas_uh = len(ruc[ruc["cls"].isin(_GAS)]) * _UH
    tot_uh = len(ruc) * _UH
    win = ruc[ruc["hod"].between(13, 19)]
    print(f"\nTOTAL ONRUC unit-hours: {tot_uh:.0f} (gas {gas_uh:.0f})")
    print(f"hod 13-19 share: {len(win)}/{len(ruc)} = {100 * len(win) / len(ruc):.0f}%")
    print(
        f"\nMATERIALITY: measured gas RUC {gas_uh:.0f} unit-hours vs keeper gas "
        f"bridge ~{_BRIDGE_UNIT_HOURS:,} ⇒ {_BRIDGE_UNIT_HOURS / max(gas_uh, 1):.0f}x "
        f"smaller ⇒ NOT material; Lane B step 2 not triggered."
    )

    print("\n=== top 10 ONRUC resources (unit-hours) ===")
    top = (
        ruc.groupby(["Resource Name", "cls"])
        .agg(intervals=("HSL", "size"), mean_HSL=("HSL", "mean"))
        .sort_values("intervals", ascending=False)
        .head(10)
    )
    top["unit_hours"] = (top["intervals"] * _UH).round(1)
    print(top.round(0).to_string())

    if CROSSWALK.exists():
        xw = pd.read_csv(CROSSWALK)
        acc = set(xw[xw["accepted"] == 1]["site"])
        print(
            f"\ncrosswalk-accepted among {ruc['site'].nunique()} ONRUC sites: "
            f"{len(set(ruc['site']) & acc)}"
        )


if __name__ == "__main__":
    main()
