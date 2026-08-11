"""caiso-194 engagement probe: does `hydro_ror_split` actually reach the fleet?

Object-level proof, NO LP. caiso-188 G-CTRL proved the CAISO keeper solved with
this mechanism INERT (exact reproduction from an environment with no
``hydro-plant-modes`` partition). caiso-188 §7 item 5 is binding: never treat
"run_config records the flag as armed" as evidence the mechanism ran — check the
gate, the call site, and the DATA.

This probe checks the DATA end directly by building the real CAISO hydro fleet
twice, ``ror_split`` off and on, and comparing the per-unit RoR stamp
(``hydro_ror_flat_monthly_mw``, set to ``budget[g, m] / hours[m]`` clipped to
nameplate). An off/on difference proves the classifier was read and applied; an
identical pair proves the mechanism is inert at this head.

Deliberately NOT done here: any comparison of hydro output against measured
hydro or pumped-storage generation. The caiso-141 wall (GATESPEC §2) forbids it.
Every number below is model-side fleet construction only.

Usage:
  PYTHONPATH=.:src uv run python scripts/probes/_caiso194_engagement.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results" / "calibration" / "_caiso194_engagement.json"
YEARS = (2023, 2024, 2025)


def probe_year(year: int, zones: list[str]) -> dict:
    """Build the CAISO hydro fleet off/on and report the RoR stamping delta."""
    from market_sim.data.hydro import build_hydro_fleet

    off_units, off_energy = build_hydro_fleet("CAISO", year, zones, ror_split=False)
    on_units, on_energy = build_hydro_fleet("CAISO", year, zones, ror_split=True)

    off_stamped = [u for u in off_units if u.hydro_ror_flat_monthly_mw is not None]
    on_stamped = [u for u in on_units if u.hydro_ror_flat_monthly_mw is not None]

    # The monthly energy budget must be untouched by the split: the mechanism
    # redistributes WHEN the water runs, never HOW MUCH (rule 13 forward story).
    budget_identical = bool(np.array_equal(off_energy, on_energy))

    stamped_mw = float(sum(u.pmax_mw for u in on_stamped))
    fleet_mw = float(sum(u.pmax_mw for u in on_units))

    return {
        "year": year,
        "units_built": len(on_units),
        "units_stamped_off": len(off_stamped),
        "units_stamped_on": len(on_stamped),
        "stamped_pmax_mw": round(stamped_mw, 3),
        "fleet_pmax_mw": round(fleet_mw, 3),
        "stamped_pmax_share_pct": round(100.0 * stamped_mw / fleet_mw, 4)
        if fleet_mw
        else 0.0,
        "monthly_budget_identical_off_vs_on": budget_identical,
        "engaged": len(on_stamped) > 0 and len(off_stamped) == 0,
    }


def main() -> int:
    """CLI entry point."""
    from market_sim.config.iso_configs import get_iso_config

    zones = [z.name for z in get_iso_config("CAISO").zones]
    rows = [probe_year(y, zones) for y in YEARS]
    rec = {
        "note": (
            "Object-level engagement evidence for hydro_ror_split at CAISO. No LP, "
            "no scoring, no comparison against measured hydro/PS output "
            "(caiso-141 wall, GATESPEC-caiso194 section 2)."
        ),
        "zones": zones,
        "years": rows,
        "engaged_all_years": all(r["engaged"] for r in rows),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")

    for r in rows:
        print(
            f"{r['year']}  units={r['units_built']:4d}  stamped off/on="
            f"{r['units_stamped_off']}/{r['units_stamped_on']:<4d} "
            f"({r['stamped_pmax_mw']:.1f} MW = {r['stamped_pmax_share_pct']:.2f} % of fleet)  "
            f"budget identical={r['monthly_budget_identical_off_vs_on']}  "
            f"ENGAGED={r['engaged']}"
        )
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
