"""caiso-197 (lane 5) — the per-plant PS citation record, G-AGG reconciliation
and G-ZONE/G-ENGAGE (fleet-build) checks. **NO LP. No price series.**

`GATESPEC-caiso195-ps-physical-2026-08-11.md` §7 record: per-plant values,
document citations, the G-AGG reconciliation arithmetic. This probe:

1. re-derives every `constants.CAISO_PS_PLANT_PARAMS` value from its cited
   primitives (motor hp × 745.7 W/hp; reservoir AF × MW / design-flow AF/h)
   and asserts the committed constant matches to its rounding;
2. measures **G-AGG** on the SHIPPED loader: the armed per-plant split's
   Σ power_cap must equal the off-state aggregate's Σ power_cap exactly
   (zero MW added — the aggregate's own EIA-860 rows re-attributed);
3. records **G-ZONE**: each plant's `build_zone_lookup` geography (the
   model's own convention — no zone chosen by this lane);
4. records the **G-ENGAGE fleet half**: the armed loader emits the six
   per-plant units with their cited bounds (a build, never a solve — the
   LP half is measured on the A/B bundles).

Usage::

    python scripts/probes/_caiso197_ps_citations.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

OUT = REPO / "results" / "calibration" / "_caiso197_ps_citations.json"

HP_TO_MW = 745.6999e-6  # 1 hp = 745.6999 W (fixed physics constant)
CFS_TO_AF_H = 3600.0 / 43560.0  # 1 cfs for one hour = 0.0826446 AF

# Cited primitives, quoted from the committed corpora (each row names its
# document). The derived values below must reproduce constants.
_PRIMITIVES = {
    6100: {
        "plant": "Helms (PG&E, FERC P-2735)",
        "source": "data/raw/reference/pge-helms-ps-plant-2008 (PG&E, NW Wind "
        "Integration Forum 2008-10-17, p.4-5)",
        "pump_mw_quoted": 930.0,  # "930 MW total in pump mode" — direct quote
        "gen_mw_quoted": 1212.0,
        "design_flow_cfs": 9000.0,
        "reservoir": "Courtright Lake (upper)",
        "reservoir_af_gross": 123000.0,
    },
    437: {
        "plant": "Edward C Hyatt (DWR)",
        "source": "data/raw/reference/dwr-b132-22-swp-plants (DWR Bulletin "
        "132-22 Ch.1: pumping table p.9; Table 1-4 p.10; Table 1-1 p.7)",
        "pump_motor_hp": 519000.0,
        "gen_mw_quoted": 645.0,
        "design_flow_cfs": 16950.0,
        "reservoir": "Thermalito Forebay 11,800 + Afterbay 57,000 (pump-back "
        "cycle store; USBR EWA EIS §16.2.5.2.6 names the afterbay)",
        "reservoir_af_gross": 68800.0,
    },
    438: {
        "plant": "Robie Thermalito (DWR)",
        "source": "data/raw/reference/dwr-b132-22-swp-plants",
        "pump_motor_hp": 120000.0,
        "gen_mw_quoted": 114.0,
        "design_flow_cfs": 17400.0,
        "reservoir": "Thermalito Afterbay",
        "reservoir_af_gross": 57000.0,
    },
    448: {
        "plant": "W R Gianelli (DWR/USBR joint)",
        "source": "data/raw/reference/dwr-b132-22-swp-plants",
        "pump_motor_hp": 504000.0,
        "gen_mw_quoted": 424.0,
        "design_flow_cfs": 16960.0,
        "reservoir": "San Luis Reservoir (gross; DWR share 1,062,183 AF "
        "recorded — gross used per GATESPEC §4.1 more-capability)",
        "reservoir_af_gross": 2027800.0,
    },
    446: {
        "plant": "O'Neill (USBR)",
        "source": "USBR EWA Draft EIS/EIR (July 2003) Ch.16 §16.2.7.1.1 "
        "(Reclamation 2001): 6 units, 6,000-hp motors, 700 cfs and "
        "4,200 kW each; forebay volume from DWR B132-22 Table 1-1",
        "pump_motor_hp": 36000.0,
        "gen_mw_quoted": 25.2,
        "design_flow_cfs": 4200.0,
        "reservoir": "O'Neill Forebay (gross; DWR share 29,500 AF recorded)",
        "reservoir_af_gross": 56400.0,
    },
    104: {
        "plant": "J S Eastwood (SCE, FERC P-67)",
        "source": "USBR Upper San Joaquin Storage Investigation, Hydropower "
        "Technical Appendix (June 2005) p.2-16: 199.8 MW, 1,338 ft head, "
        "pumped-storage function; NO public pump-mode rating or Balsam "
        "Meadow forebay volume found",
        "pump_mw_quoted": None,
        "gen_mw_quoted": 199.8,
        "design_flow_cfs": None,
        "reservoir": "Balsam Meadow forebay (volume uncited)",
        "reservoir_af_gross": None,
    },
}


def _derive(spec: dict) -> dict:
    """Derived pump/energy values from the cited primitives."""
    if spec.get("pump_mw_quoted") is not None:
        pump = spec["pump_mw_quoted"]
        pump_basis = "direct public quote"
    elif spec.get("pump_motor_hp") is not None:
        pump = round(spec["pump_motor_hp"] * HP_TO_MW, 1)
        pump_basis = f"{spec['pump_motor_hp']:,.0f} hp x 745.6999 W/hp"
    else:
        pump = None
        pump_basis = "UNCITED — unrestrained default (charge cap = power cap)"
    if spec.get("reservoir_af_gross") and spec.get("design_flow_cfs"):
        af_h = spec["design_flow_cfs"] * CFS_TO_AF_H
        mwh_af = spec["gen_mw_quoted"] / af_h
        energy = round(spec["reservoir_af_gross"] * mwh_af)
        energy_basis = (
            f"{spec['reservoir_af_gross']:,.0f} AF x {spec['gen_mw_quoted']} MW"
            f" / ({spec['design_flow_cfs']:,.0f} cfs = {af_h:,.2f} AF/h)"
        )
    else:
        energy = None
        energy_basis = (
            "UNCITED — incumbent default (PUMPED_STORAGE_DURATION_HOURS x "
            "EIA-860 nameplate)"
        )
    return {
        "pump_mw": pump,
        "pump_basis": pump_basis,
        "energy_mwh": energy,
        "energy_basis": energy_basis,
    }


def main() -> None:
    """Verify constants against citations; measure G-AGG/G-ZONE/G-ENGAGE."""
    from market_sim.config.constants import CAISO_PS_PLANT_PARAMS
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.zone_assignment import build_zone_lookup
    from market_sim.model.storage import load_eia860_pumped_storage

    rows = {}
    mismatches = []
    for code, prim in _PRIMITIVES.items():
        derived = _derive(prim)
        const = CAISO_PS_PLANT_PARAMS[code]
        ok_pump = (
            derived["pump_mw"] is None
            and const["pump_mw"] is None
            or (
                derived["pump_mw"] is not None
                and const["pump_mw"] is not None
                and abs(derived["pump_mw"] - float(const["pump_mw"])) < 0.51
            )
        )
        ok_energy = (
            derived["energy_mwh"] is None
            and const["energy_mwh"] is None
            or (
                derived["energy_mwh"] is not None
                and const["energy_mwh"] is not None
                and abs(derived["energy_mwh"] - float(const["energy_mwh"])) < 1.0
            )
        )
        if not (ok_pump and ok_energy):
            mismatches.append(code)
        rows[str(code)] = {**prim, **derived, "constants_entry": const,
                           "matches_constants": bool(ok_pump and ok_energy)}

    zl = build_zone_lookup("CAISO")
    zones = {str(c): zl.get(c) for c in _PRIMITIVES}

    off = load_eia860_pumped_storage("CAISO", 2023, ScenarioConfig(iso="CAISO"))
    on = load_eia860_pumped_storage(
        "CAISO", 2023, ScenarioConfig(iso="CAISO", caiso_ps_plant_params=True)
    )
    g_agg = {
        "off_units": [(u.unit_id, u.power_cap_mw) for u in off],
        "armed_units": [
            {
                "unit_id": u.unit_id,
                "zone": u.zone,
                "power_cap_mw": u.power_cap_mw,
                "energy_cap_mwh": u.energy_cap_mwh,
                "charge_power_cap_mw": u.charge_power_cap_mw,
            }
            for u in on
        ],
        "off_total_mw": round(sum(u.power_cap_mw for u in off), 6),
        "armed_total_mw": round(sum(u.power_cap_mw for u in on), 6),
    }
    g_agg["zero_mw_added"] = g_agg["off_total_mw"] == g_agg["armed_total_mw"]

    out = {
        "iso": "CAISO",
        "gatespec": "GATESPEC-caiso195-ps-physical-2026-08-11.md",
        "constants_table": "config/constants.py::CAISO_PS_PLANT_PARAMS",
        "citations": rows,
        "constants_match_citations": not mismatches,
        "mismatched_codes": mismatches,
        "g_zone_build_zone_lookup": zones,
        "g_agg": g_agg,
        "g_engage_fleet_half": {
            "armed_unit_count": len(on),
            "expected": 6,
            "pass": len(on) == 6,
        },
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "citations"}, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    if mismatches or not g_agg["zero_mw_added"] or len(on) != 6:
        sys.exit(2)


if __name__ == "__main__":
    main()
