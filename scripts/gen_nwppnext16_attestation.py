"""Emit the NWPP-NEXT-16 calibration attestation for an arm C / D / E span bundle.

NWPP-NEXT-16 (PRECOMMIT
``docs/handoffs/PRECOMMIT-nwppnext16-combined-captive-live-2019-2025-2026-10-01.md``) is keeper
#19's recipe (NWPP-NEXT-14) with the Bridger per-unit tranche fix swapped:
``campd_unit_fuel_split`` off and ``campd_per_unit_vintage_denominator`` on (rule 19: the
selector refuses both; the vintage denominator also repairs North Valmy). Arm D adds
``coal_captive_marginal_fuel_price``; arm E adds the live-capacity screened-coal WEFOR relief.

It reuses :mod:`gen_nwppnext13_attestation` (keeper #18's generator) and applies this lane's
delta, exactly as :mod:`gen_nwppnext14_attestation` does for keeper #19.
**ZERO NEW FREE PARAMETERS** (rules 21 / 24): EIA-860 vintage nameplate, EIA-923 Page-5
delivered prices and CAMPD outage windows; ``wefor_residual`` = 0.0 is the caiso-187 residual
construction already identified for NWPP, not a tuned value.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import scripts.gen_nwppnext13_attestation as prev  # noqa: E402
import scripts.gen_rnwpp_attestation as base  # noqa: E402

PIN = "33014efc27296bf78842c4a50f311fe191c82b07"
COAL_GROUPS = ["COAL_BIT", "COAL_LIGNITE", "COAL_PRB", "COAL_WC"]

#: Boolean keys each arm arms (all must read True in every year's run_config).
ARM_KEYS = {
    "c": ("eia923_cc_family_heat_rates", "campd_per_unit_vintage_denominator"),
    "d": (
        "eia923_cc_family_heat_rates",
        "campd_per_unit_vintage_denominator",
        "coal_captive_marginal_fuel_price",
    ),
    "e": (
        "eia923_cc_family_heat_rates",
        "campd_per_unit_vintage_denominator",
        "unit_outage_dispatched_bin_denominator",
        "unit_outage_dispatched_bin_live_denominator",
        "wefor_residual_short_screened_coal",
    ),
}

_SOURCES = {
    "eia923_cc_family_heat_rates": (
        "EIA-923 CC-family heat rate (data/raw/_processed-legacy/"
        "eia923_cc_family_heat_rates_NWPP.csv): Clark 2322's CC rows take the plant's own "
        "EIA-923 electric fuel / net generation. Rule 14. Unchanged from keeper #19."
    ),
    "campd_per_unit_vintage_denominator": (
        "Per-unit tranche companion on each year's EIA-860 vintage nameplate (data/raw/"
        "_processed-legacy/thermal_tranches-perunit-vintage-NWPP.csv, sha 6fe20358): repairs "
        "Jim Bridger's coal row and North Valmy 8224's must-run (212.45 -> 127.89 MW). "
        "Replaces campd_unit_fuel_split (rule 19). Rule 14."
    ),
    "coal_captive_marginal_fuel_price": (
        "EIA-923 Page-5 coal receipts: at a mixed-source coal plant the econ/peak tranches "
        "take the plant-month non-captive delivered price (PHASE0-nwppnext15-captive-mine). "
        "Owner card 'Build, no threshold'. Rule 13 forward-regenerable."
    ),
    "unit_outage_dispatched_bin_denominator": (
        "CAMPD unit-outage share divided by the dispatched LP bin's capacity (miso-266)."
    ),
    "unit_outage_dispatched_bin_live_denominator": (
        "Sub-gate: the dispatched-bin denominator counts only cohorts live in the solve "
        "year (stamped EIA-860 exit month). Centralia 1,340 -> 670 MW, Colstrip 2,094 -> "
        "1,480 MW in 2021/22/25 (nwppnext15/live_denominator_census.json)."
    ),
    "wefor_residual_short_screened_coal": (
        "Screened coal's sub-5-day stops are measured by unit_outage_short_windows, so the "
        "statistical WEFOR is capped at wefor_residual on the screened share (miso-273)."
    ),
}


def build(bundle: Path, arm: str) -> dict:
    """Return the NWPP-NEXT-16 attestation for ``arm`` built on the NEXT-13 generator."""
    keys = ARM_KEYS[arm]
    base._ARMED = tuple(k for k in base._ARMED if k != "campd_unit_fuel_split")
    for key in keys:
        if key not in base._ARMED:
            base._ARMED = (*base._ARMED, key)
        base._SOURCES[key] = _SOURCES[key]
    att = prev.build(bundle)
    years = json.loads((bundle / "meta.json").read_text())["years"]
    sw = att.setdefault("switches", {})
    sw["campd_unit_fuel_split"] = {
        "value": False,
        "where": "ScenarioConfig.campd_unit_fuel_split, pinned through replay_keeper --set",
        "identification": "measured-physical",
        "source": "Disarmed: replaced by campd_per_unit_vintage_denominator (rule 19).",
    }
    if arm == "e":
        for y in years:
            sc = json.loads((bundle / f"run_config_{y}.json").read_text())[
                "scenario_config"
            ]
            groups = sorted(sc.get("wefor_residual_groups") or [])
            if sc.get("wefor_residual") != 0.0 or groups != COAL_GROUPS:
                raise SystemExit(
                    f"{y}: wefor_residual={sc.get('wefor_residual')!r}, groups={groups} "
                    "-- not the arm-E recipe"
                )
        sw["wefor_residual"] = {
            "value": 0.0,
            "where": "ScenarioConfig.wefor_residual, pinned through replay_keeper --set",
            "identification": "measured-physical",
            "source": (
                "caiso-187 residual max(0, W - X) on NWPP's own fleet "
                "(FINDING-nwppnext13 s1.3): the measured windows carry the forced outages."
            ),
        }
        sw["wefor_residual_groups"] = {
            "value": COAL_GROUPS,
            "where": "ScenarioConfig.wefor_residual_groups",
            "identification": "measured-physical",
            "source": "Scopes the relief to screened coal only (FINDING-nwppnext13 s1.3.3).",
        }
    att["lane"] = f"NWPP-NEXT-16-{arm.upper()}"
    att["governance"]["notes"] = (
        "Keeper #19 recipe with the Bridger per-unit fix swapped to the vintage denominator "
        f"(arm {arm.upper()}; owner cards 2026-10-01). Offer-curve multipliers unchanged; "
        "nothing swept, nothing selected on a gate."
    )
    disc = att["disclosures"]
    disc["years"] = (
        f"Solved {years}, one isolated shard per year (rule 36), pinned {PIN[:8]}, on the "
        "requirements.txt library pins (keeper #19 solved off-pin: library drift is LIVE and "
        "unmeasured in any C-vs-#19 difference)."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        f"Config keys moved against keeper #19: campd_unit_fuel_split -> False, "
        f"{', '.join(k for k in keys if k != 'eia923_cc_family_heat_rates')} -> True"
        + (
            ", wefor_residual -> 0.0, wefor_residual_groups -> coal"
            if arm == "e"
            else ""
        )
        + "; plus highspy 1.15.1 -> 1.14.0 / pandas / pyarrow / pydantic to the pins."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--arm", required=True, choices=sorted(ARM_KEYS))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle, args.arm)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
