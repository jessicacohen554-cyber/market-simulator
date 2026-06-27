"""Print the measured-vs-modeled ERCOT battery AS-vs-energy split (G5 validation).

Reads a bundle's ``storage_as.parquet`` (written by run_calibration_full when
``ercot_storage_as_endogenous`` is on) and reports, per year, the LP's CHOSEN
battery split — modeled upward-AS MWh (storage-first attribution of the cleared
co-opt reserve) and modeled discharge (energy) MWh — against the **measured**
60-Day DAM battery AS award. The measured award is the backcast realization the
chosen split is validated against, never pinned to it (CLAUDE.md #12).

Usage: python scripts/probes/storage_as_split.py [BUNDLE_DIR]
       (default results/calibration/164)
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results/calibration/164"
path = bundle / "storage_as.parquet"
if not path.exists():
    raise SystemExit(f"no storage_as.parquet in {bundle} (run with the G5 flag on)")

df = pd.read_parquet(path)
# Use the final pass per (year): P2 if present else P1.
order = {"P0": 0, "P1": 1, "P2": 2}
df["_o"] = df["pass"].astype(str).map(order).fillna(0)
df = df.sort_values("_o").groupby(["year", "hour"], as_index=False).last()

GWH = 1e3  # MWh -> GWh
print(f"\nERCOT endogenous storage AS-vs-energy split — {bundle.name}\n")
print(
    f"{'year':>4} | {'measured AS':>11} | {'modeled AS':>10} | "
    f"{'modeled energy':>14} | {'AS share (mod)':>14} | {'AS share (meas)':>15}"
)
print("-" * 92)
for year, g in df.groupby("year"):
    meas_as = g["measured_as_mw"].mean()  # mean MW
    mod_as = g["modeled_as_mw"].mean()
    mod_en = g["modeled_discharge_mw"].mean()
    mod_share = mod_as / (mod_as + mod_en) if (mod_as + mod_en) > 0 else 0.0
    # Measured energy proxy: not in this frame; report AS share vs modeled energy
    # denominator is not apples-to-apples, so report measured AS MW for the level
    # check and the modeled AS/energy split as the model's own choice.
    meas_share = meas_as / (meas_as + mod_en) if (meas_as + mod_en) > 0 else 0.0
    print(
        f"{int(year):>4} | {meas_as:>8.0f} MW | {mod_as:>7.0f} MW | "
        f"{mod_en:>11.0f} MW | {mod_share:>13.1%} | {meas_share:>14.1%}"
    )
print(
    "\n(mean MW across 8760h; modeled AS = storage-first attribution of cleared "
    "co-opt reserve, modeled energy = battery discharge. Measured AS = 60-Day DAM "
    "battery award — the validation target, not a pin.)"
)
