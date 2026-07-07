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

print(f"\nERCOT endogenous storage AS-vs-energy split — {bundle.name}\n")
print(
    f"{'year':>4} | {'measured AS':>11} | {'modeled AS':>15} | "
    f"{'mod/meas':>8} | {'modeled energy':>14} | {'AS share (mod)':>14}"
)
print("-" * 84)
for year, g in df.groupby("year"):
    meas_as = g["measured_as_mw"].mean()  # mean MW
    mod_as = g["modeled_as_mw"].mean()
    mod_en = g["modeled_discharge_mw"].mean()
    mod_share = mod_as / (mod_as + mod_en) if (mod_as + mod_en) > 0 else 0.0
    ratio = mod_as / meas_as if meas_as > 0 else float("nan")
    print(
        f"{int(year):>4} | {meas_as:>8.0f} MW | {mod_as:>12.0f} MW | "
        f"{ratio:>7.2f}x | {mod_en:>11.0f} MW | {mod_share:>13.1%}"
    )
print(
    "\n(mean MW across 8760h. modeled AS: with ercot_storage_as_duration_gate ON "
    "(e.g. bundle 166) this is the EXACT storage AS decision variable "
    "(DispatchResult.storage_reserve_dispatch = sum_c RS[c,z]); with the gate OFF "
    "(storage pooled in the thermal headroom, e.g. bundle 164) it is the storage-FIRST "
    "min(storage room, zone reserve) UPPER bound. modeled energy = battery discharge. "
    "measured AS = 60-Day DAM battery award — the validation target, never a pin "
    "(CLAUDE.md #12). The LP CHOOSES the split; it is AS-dominated and rises with the "
    "fleet, as in reality. The gate-on 0.54-0.61x under-provision is a documented "
    "dispatch-choice residual (evening SOC depletion, G-37 / "
    "FINDING-ercot-storage-as-g37-2026-07.md), not retuned to the measured level.)"
)
