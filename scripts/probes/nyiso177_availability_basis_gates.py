"""nyiso-177: discharge PREREG gates G3 and G3' from artifact bytes only.

G3 (as originally worded) asks whether the merit-order guard REPAIRS the
availability envelope; G3' (the §6.3 amendment) asks the question the brief
actually posed -- whether a candidate companion HOLDS the envelope at the
keeper's so the representation repair becomes a clean single delta. Both are
scored here over four legs, with NO SOLVE and no LP output of any kind.

Run: PYTHONPATH=.:src python scripts/probes/nyiso177_availability_basis_gates.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from market_sim.data import outages

YEARS = (2023, 2024, 2025)
ISO = "NYISO"
OUT = Path("results/calibration/_nyiso177_availability_basis_gates.json")

# Candidate unit-outage companions, all derived at HEAD over 2019-2026 with the
# SAME per-unit crosswalk. `None` = the resolver's own default for the leg.
# `override` records whether repair 1 (the rule-19 _FLEET_GROUP_OVERRIDE
# de-stack) is DISARMED on that leg. G3' was specified in the PREREG §6.3
# amendment against the code as it stood BEFORE repair 1 landed, so each
# candidate is scored BOTH ways: `*_ovr` is the configuration the gate was
# written for, and the bare name is the configuration a solve would actually
# run. Reporting both is what keeps the gate honest across the repair.
CANDIDATES = {
    "keeper_incumbent": (None, False),
    "arm_unguarded": (None, True),
    "merit_guard": ("data/raw/campd-unit-outages-perunitmerit-NYISO.csv", True),
    "no_fullstop_override": ("data/raw/campd-unit-outages-perunitnofs-NYISO.csv", True),
    "merit_guard_ovr": ("data/raw/campd-unit-outages-perunitmerit-NYISO.csv", True),
    "arm_unguarded_ovr": (None, True),
    "no_fullstop_override_ovr": (
        "data/raw/campd-unit-outages-perunitnofs-NYISO.csv",
        True,
    ),
}
# Legs whose name ends in _ovr keep the per-plant override ARMED on the
# per-unit path (i.e. repair 1 NOT applied).


def _avail(path: str | None, per_unit: bool, keep_override: bool = False) -> dict:
    """Return {year: {bin: (hours,) availability array}} for one candidate.

    ``keep_override`` re-arms the per-plant ``_FLEET_GROUP_OVERRIDE`` on the
    per-unit path, reproducing the code state the G3' bar was written against.
    """
    orig = outages.unit_outage_csv_for_iso
    orig_target = outages._generic_unit_outage_target
    if keep_override:
        def _target(facility_id, unit_id, group, per_unit_crosswalk=False):
            return orig_target(facility_id, unit_id, group, per_unit_crosswalk=False)

        outages._generic_unit_outage_target = _target

    def resolver(
        iso,
        mixed_gas_routing=False,
        per_unit_crosswalk=False,
        merit_order_guard=False,
    ):
        if path and per_unit_crosswalk and (iso or "").upper() == ISO:
            return Path(path)
        return orig(iso, mixed_gas_routing, per_unit_crosswalk, merit_order_guard)

    outages.unit_outage_csv_for_iso = resolver
    outages.unit_outage_derate_factors.cache_clear()
    try:
        return {
            y: outages.unit_outage_derate_factors(y, iso=ISO, per_unit_crosswalk=per_unit)
            for y in YEARS
        }
    finally:
        outages.unit_outage_csv_for_iso = orig
        outages._generic_unit_outage_target = orig_target
        outages.unit_outage_derate_factors.cache_clear()


def main() -> None:
    cap = outages._iso_plant_capacity(ISO, False, False)
    legs = {
        name: _avail(path, per_unit, keep_override=name.endswith("_ovr"))
        for name, (path, per_unit) in CANDIDATES.items()
    }

    def booked(leg: str, year: int, group: str) -> float:
        num = den = 0.0
        for (code, grp), mw in cap.items():
            if grp != group:
                continue
            den += mw
            arr = legs[leg][year].get((code, grp))
            num += mw * (1.0 - (float(np.mean(arr)) if arr is not None else 1.0))
        return num / den if den else 0.0

    def l1_from_keeper(leg: str) -> float:
        """Nameplate-weighted L1 distance of the mean-availability vector."""
        num = den = 0.0
        for year in YEARS:
            for key, mw in cap.items():
                a = legs["keeper_incumbent"][year].get(key)
                b = legs[leg][year].get(key)
                av = float(np.mean(a)) if a is not None else 1.0
                bv = float(np.mean(b)) if b is not None else 1.0
                den += mw
                num += mw * abs(bv - av)
        return num / den if den else 0.0

    def ravenswood_identical(leg: str) -> dict[int, bool]:
        out = {}
        for year in YEARS:
            a = legs["keeper_incumbent"][year].get((2500, "ST_GAS"))
            b = legs[leg][year].get((2500, "ST_GAS"))
            out[year] = bool(
                a is not None and b is not None and np.array_equal(a, b)
            )
        return out

    rec: dict = {"years": list(YEARS), "legs": {}}
    for leg in CANDIDATES:
        rec["legs"][leg] = {
            "booked_share": {
                g: {y: booked(leg, y, g) for y in YEARS}
                for g in ("ST_GAS", "CC_REGULAR", "CC_CHP", "ST_CHP")
            },
            "rav_2500_ST_GAS_mean_availability": {
                y: (
                    float(np.mean(legs[leg][y][(2500, "ST_GAS")]))
                    if (2500, "ST_GAS") in legs[leg][y]
                    else 1.0
                )
                for y in YEARS
            },
            "l1_distance_from_keeper": l1_from_keeper(leg),
            "rav_2500_ST_GAS_array_equal_to_keeper": ravenswood_identical(leg),
        }

    # ---- G3 AS ORIGINALLY WORDED (both legs, reported at full strength) ----
    g = rec["legs"]["merit_guard"]
    ctl = rec["legs"]["keeper_incumbent"]["rav_2500_ST_GAS_mean_availability"]
    arm = rec["legs"]["arm_unguarded"]["rav_2500_ST_GAS_mean_availability"]
    strictly_between = all(
        min(ctl[y], arm[y]) < g["rav_2500_ST_GAS_mean_availability"][y] < max(ctl[y], arm[y])
        for y in YEARS
    )
    under_threshold = all(g["booked_share"]["ST_GAS"][y] < 0.40 for y in YEARS)
    rec["G3_as_worded"] = {
        "leg_a_strictly_between": strictly_between,
        "leg_b_booked_share_below_0.40": under_threshold,
        "keeper_own_booked_share": rec["legs"]["keeper_incumbent"]["booked_share"][
            "ST_GAS"
        ],
        "verdict": "PASS" if (strictly_between and under_threshold) else "FAIL",
        "note": (
            "leg (b)'s threshold measures a PRE-EXISTING keeper property "
            "(the keeper's own booked_share is 0.50-0.56), so no guarded "
            "construction could pass it — a defect in the gate's construction, "
            "disclosed in the PREREG §6.1 amendment. The over-booking object "
            "stays OPEN and unrepaired."
        ),
    }

    # ---- G3' (PREREG §6.3): does a candidate HOLD the keeper's envelope? ----
    rec["G3prime"] = {
        "bar": {"l1_max": 0.01, "rav_array_equal": True},
        "candidates": {
            leg: {
                "l1": rec["legs"][leg]["l1_distance_from_keeper"],
                "array_equal": rec["legs"][leg][
                    "rav_2500_ST_GAS_array_equal_to_keeper"
                ],
                "qualifies": (
                    rec["legs"][leg]["l1_distance_from_keeper"] <= 0.01
                    and all(
                        rec["legs"][leg]["rav_2500_ST_GAS_array_equal_to_keeper"].values()
                    )
                ),
            }
            for leg in (
                "arm_unguarded",
                "merit_guard",
                "no_fullstop_override",
                "arm_unguarded_ovr",
                "merit_guard_ovr",
                "no_fullstop_override_ovr",
            )
        },
    }
    rec["G3prime"]["qualifying"] = [
        k for k, v in rec["G3prime"]["candidates"].items() if v["qualifies"]
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({
        "G3_as_worded": rec["G3_as_worded"]["verdict"],
        "G3prime_qualifying": rec["G3prime"]["qualifying"],
        "l1": {k: round(v["l1"], 4) for k, v in rec["G3prime"]["candidates"].items()},
    }, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
