"""Export the per-plant tranche-config sheet from the live calibration config.

Writes one row per physical plant with its five tranche shares of nameplate
(must-run / committed / econ-low / econ-high / peaking, summing to 100) and the
five per-tranche heat-rate multipliers on the plant's base HR — the fully
resolved run10 baseline (offer_curve_by_group + the per-plant committed/peaking
dicts + CC duct-burner peak, all flattened to explicit per-plant numbers).

The numbers are read straight off the fleet that :func:`bins_to_fleet` builds,
so feeding the sheet back via ``--plant-tranche-config`` reproduces the run it
was exported from. Tweak any cell to reshape that plant's offer; rows you delete
fall back to the configured defaults.

Usage:
    python scripts/export_tranche_config.py [--out data/raw/reference/plant-tranche-config.csv]
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rc", str(REPO / "scripts" / "run_calibration.py")
)
rc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rc)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import REFERENCE_DIR  # noqa: E402
from market_sim.data.coal import COAL_PLANT_SUPPLY  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    BIN_GROUP_TO_FUEL,
    bins_to_fleet,
    load_campd_bins,
)

# Output column order: reference metadata first, then the editable tranche
# shares (% of nameplate) and per-tranche HR multipliers.
COLUMNS = [
    "Plant_Code",
    "Plant_Name",
    "Plant_Group",
    "Coal_Supply",
    "Config",
    "Turbine_Class",
    "ERCOT_Zone",
    "Nameplate_MW",
    "Base_HR_MMBtu_MWh",
    "Pct_Must_Run",
    "Pct_Committed",
    "Pct_Econ_Low",
    "Pct_Econ_High",
    "Pct_Peaking",
    "HR_Mult_Must_Run",
    "HR_Mult_Committed",
    "HR_Mult_Econ_Low",
    "HR_Mult_Econ_High",
    "HR_Mult_Peaking",
]

# LP unit-id suffix -> the export's (pct column, hr-mult column) pair. The
# single-econ "econ" suffix maps to econ-low; econ-high stays zero for those
# plants (the round-trip drops a zero-capacity tranche).
_SUFFIX_TO_BAND = {
    "mustrun": ("Pct_Must_Run", "HR_Mult_Must_Run"),
    "committed": ("Pct_Committed", "HR_Mult_Committed"),
    "econlo": ("Pct_Econ_Low", "HR_Mult_Econ_Low"),
    "econ": ("Pct_Econ_Low", "HR_Mult_Econ_Low"),
    "econhi": ("Pct_Econ_High", "HR_Mult_Econ_High"),
    "peak": ("Pct_Peaking", "HR_Mult_Peaking"),
}


def build_rows(year: int = 2023) -> pd.DataFrame:
    """Return the per-plant tranche-config frame for the live calibration config."""
    gas = rc._henry_hub_actual(rc._load_reference(), year)
    config = rc._calibration_config(year, "ERCOT", 8760, gas)
    bins = load_campd_bins(config.campd_bins_path)
    zones = [z.name for z in get_iso_config("ERCOT").zones]
    fleet, _ = bins_to_fleet(bins, zones, config)

    # Per-plant base HR and metadata from the bin sheet.
    meta = {int(r["Plant_Code"]): r for _, r in bins.iterrows()}
    # Group the built tranches by plant code.
    by_plant: dict[int, list] = {}
    for gen in fleet:
        by_plant.setdefault(int(gen.plant_code), []).append(gen)

    rows = []
    for code, gens in by_plant.items():
        b = meta.get(code)
        if b is None:
            continue
        base_hr = float(b["hr_weighted"])
        nameplate = float(b["capacity_mw"])
        if base_hr <= 0.0 or nameplate <= 0.0:
            continue
        group = str(b["Plant_Group"])
        row = {c: 0.0 for c in COLUMNS}
        row.update(
            {
                "Plant_Code": code,
                "Plant_Name": str(b.get("Plant_Name") or code),
                "Plant_Group": group,
                "Coal_Supply": COAL_PLANT_SUPPLY.get(code, ""),
                "Config": str(b.get("Config", "")),
                "Turbine_Class": str(b.get("Turbine_Class", "")),
                "ERCOT_Zone": str(b.get("ERCOT_Zone", "")),
                "Nameplate_MW": round(nameplate, 1),
                "Base_HR_MMBtu_MWh": round(base_hr, 3),
                # Default HR mults so an unused tranche still carries a sane value if
                # the user later gives it capacity.
                "HR_Mult_Must_Run": 1.0,
                "HR_Mult_Committed": 1.0,
                "HR_Mult_Econ_Low": 1.0,
                "HR_Mult_Econ_High": 1.0,
                "HR_Mult_Peaking": 1.0,
            }
        )
        for gen in gens:
            suffix = gen.unit_id.rsplit("_", 1)[-1]
            band = _SUFFIX_TO_BAND.get(suffix)
            if band is None:
                continue
            pct_col, hr_col = band
            row[pct_col] += gen.pmax_mw / nameplate * 100.0
            row[hr_col] = gen.heat_rate / base_hr
        # Non-coal host-steam must-run is removed before tranche creation, so it
        # is the share of nameplate not covered by the grid tranches.
        if BIN_GROUP_TO_FUEL[group] != "coal":
            grid = (
                row["Pct_Committed"]
                + row["Pct_Econ_Low"]
                + row["Pct_Econ_High"]
                + row["Pct_Peaking"]
            )
            row["Pct_Must_Run"] = max(0.0, 100.0 - grid)
        for c in (
            "Pct_Must_Run",
            "Pct_Committed",
            "Pct_Econ_Low",
            "Pct_Econ_High",
            "Pct_Peaking",
        ):
            row[c] = round(row[c], 3)
        for c in (
            "HR_Mult_Must_Run",
            "HR_Mult_Committed",
            "HR_Mult_Econ_Low",
            "HR_Mult_Econ_High",
            "HR_Mult_Peaking",
        ):
            row[c] = round(row[c], 4)
        rows.append(row)

    df = pd.DataFrame(rows, columns=COLUMNS)
    return df.sort_values(["Plant_Group", "Plant_Name"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    # Editable tranche-config sheet, a sibling of custom-bin-assignments.csv
    # under the single W1 data root (paths.REFERENCE_DIR = data/raw/reference);
    # the pre-W1 ``inputs/`` root was removed by the relocation.
    ap.add_argument("--out", default=str(REFERENCE_DIR / "plant-tranche-config.csv"))
    ap.add_argument(
        "--year",
        type=int,
        default=2023,
        help="Calibration year whose resolved config to export "
        "(default 2023; the offer curve is year-independent).",
    )
    args = ap.parse_args()
    df = build_rows(args.year)
    out = Path(args.out)
    df.to_csv(out, index=False)
    print(f"wrote {out}  ({len(df)} plants)")


if __name__ == "__main__":
    main()
