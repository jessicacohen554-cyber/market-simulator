"""neiso-99 probe: how much CC/CHP availability the mis-routed oil peakers remove.

Quantifies, on the DESIGNATED KEEPER's own scenario settings, the hourly
availability multiplier the ``campd-unit-outages-NEISO.csv`` overlay applies to
each affected ``(plant_code, plant_group)`` bin WITH the mis-routed liquid-fuel
combustion-turbine rows and WITHOUT them. Read-only: no CSV is rewritten, no LP
is constructed.

The mis-routed population is the one measured by
``neiso99_routing_blast_radius.py``: a CAMPD unit whose own ``unitType`` is a
combustion turbine and whose own ``primaryFuelInfo`` is a LIQUID (Diesel Oil /
Other Oil), written into a sibling GAS bin by ``_resolve_unit_group``'s
``fac_group`` short-circuit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _load_unit_outage_events,
    _unit_outage_factors_from_events,
)

# (facility_id, unit_id) of the mis-routed liquid-fuel CTs in NEISO, measured by
# the blast-radius probe against CAMPD unitType + primaryFuelInfo.
MISROUTED = {
    (568, "BHB4"),
    (1588, "MJ-1"),
    (1595, "S6"),
    (6081, "004"),
    (6081, "005"),
}
YEARS = (2023, 2024, 2025)
# The keeper (2026-08-17-neiso-97-dstrepair) arms cc_steam_part_reclass.
CC_STEAM_PART_RECLASS = True


def summarize(arr: np.ndarray) -> dict:
    """Return the availability multiplier's shape statistics for one bin-year."""
    return {
        "min": round(float(arr.min()), 6),
        "mean": round(float(arr.mean()), 6),
        "hours_derated": int((arr < 0.999999).sum()),
        "mwh_equiv_frac_of_year": round(float((1.0 - arr).sum() / len(arr)), 6),
    }


def main() -> None:
    """Measure the mis-routed rows' derate on every bin they touch."""
    csv_path = RAW_DATA_DIR / "campd-unit-outages-NEISO.csv"
    df = _load_unit_outage_events(csv_path, "NEISO")
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    keep = ~pd.Series(
        [
            (int(f), str(u)) in MISROUTED
            for f, u in zip(df["facility_id"], df["unit_id"])
        ],
        index=df.index,
    )
    print(
        f"rows >= {UNIT_OUTAGE_MIN_DAYS}d: {len(df)}; mis-routed {int((~keep).sum())}"
    )

    result: dict[str, dict] = {"years": {}}
    for y in YEARS:
        with_ = _unit_outage_factors_from_events(
            df, y, 8760, "", "NEISO", CC_STEAM_PART_RECLASS, False
        )
        without = _unit_outage_factors_from_events(
            df[keep], y, 8760, "", "NEISO", CC_STEAM_PART_RECLASS, False
        )
        rows = {}
        for tgt in sorted(set(with_) | set(without), key=str):
            a = with_.get(tgt, np.ones(8760))
            b = without.get(tgt, np.ones(8760))
            if np.array_equal(a, b):
                continue
            rows[f"{tgt[0]}:{tgt[1]}"] = {
                "with_misrouted": summarize(a),
                "without_misrouted": summarize(b),
                "max_abs_delta": round(float(np.abs(a - b).max()), 6),
                "hours_changed": int((a != b).sum()),
            }
        result["years"][str(y)] = rows
        print(f"\n=== {y}: {len(rows)} bin(s) change")
        for k, v in rows.items():
            w, o = v["with_misrouted"], v["without_misrouted"]
            print(
                f"  {k:22s} derated h {w['hours_derated']:5d} -> {o['hours_derated']:5d}"
                f" | min avail {w['min']:.4f} -> {o['min']:.4f}"
                f" | lost-capacity-year frac {w['mwh_equiv_frac_of_year']:.4f}"
                f" -> {o['mwh_equiv_frac_of_year']:.4f}"
                f" | max|d| {v['max_abs_delta']:.4f} over {v['hours_changed']} h"
            )

    out = ROOT / "results" / "calibration" / "_neiso99_routing_derate_magnitude.json"
    out.write_text(json.dumps(result, indent=1, sort_keys=True))
    print("\nwrote", out)


if __name__ == "__main__":
    main()
