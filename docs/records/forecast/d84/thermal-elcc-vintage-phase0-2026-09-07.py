"""capx D84 — phase 0 for the PJM THERMAL ELCC delivery-year vintage axis (ZERO LP).

Charter phase 0, steps (a)-(d). Measures the BUILT mechanism's accredited
thermal MW by fuel class, per delivery year, under both vintages, and applies
the chartered STOP gate: if the predicted per-class accredited-MW move is ZERO
in every delivery year in the window, the lane is INERT and ends here.

**What makes this a phase 0 rather than arithmetic on paper.** It calls the
SHIPPED CODE PATH — ``thermal_accreditation_fraction`` /
``resolve_thermal_accreditation_basis`` / ``thermal_accreditation_vintage_armed``
— under a control config and an armed one, so what is gated is the mechanism as
it will actually run in the screen, not a hand model of it.

**Zero LP, and no fleet rebuild either.** Thermal accreditation is
``pmax x fraction`` with the fraction uniform inside a fuel class, so the
delta over any fleet is exactly ``sum_fuel nameplate_fuel x delta_rating_fuel``
and the committed ledgers' own ``fleet_by_fuel_before`` supplies the nameplate.
That identity is asserted here (``identity_check``) rather than assumed, by
reconstructing the incumbent thermal subtotal from the same ledger and
differencing it against the vintaged one two independent ways.

**The reference bundle is NOT at HEAD posture** and this instrument says so
rather than hiding it: ``pjm-2021-2025-realized-t1h-d78-sectorgate`` carries key
``bb6a60239d69508b`` while HEAD's bare ``pjm-t1h`` resolves ``f736025631d0d27e``
(owner rulings Q55/Q56/Q58 landed after it). Its fleet is therefore an ANCHOR
for the magnitude, not the number the screen will reproduce; the identity above
is what the screen is graded on, evaluated on the CONTROL's own entering fleet.

Rule 13: every published figure is an observable compared against, never an
input. Rule 21: nothing here is fitted to a residual. Rule 29: this gate may
KILL an arm; it can never promote one, and it is never read against the target
residual.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity import (  # noqa: E402
    resolve_thermal_accreditation_basis,
    thermal_accreditation_fraction,
    thermal_accreditation_vintage_armed,
)

REF = REPO / (
    "results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate/PJM/bb6a60239d69508b"
)

# Delivery year <- the model year whose screen prices it (the planning-year
# label resolve_delivery_year builds: model year Y -> "Y/Y+1").
DY_TO_MODEL_YEAR = {f"{y}/{y + 1}": y for y in range(2021, 2026)}

# A representative EFORd purely for the UCAP-fallback legs of the printout; it
# cancels out of every delta this instrument reports, because a UCAP year is
# identical between arms by construction.
EFORD = 0.07


def _ledger(year: int) -> dict:
    return json.loads((REF / f"evolution_{year}.json").read_text())


def _config(armed: bool) -> ScenarioConfig:
    """The two phase-0 postures. They differ in EXACTLY ONE field."""
    return ScenarioConfig(
        mode="forecast",
        iso="PJM",
        hindcast=True,
        renewable_elcc_curves=True,
        pjm_accreditation_design_vintage=True,
        pjm_demand_response_supply=True,
        pjm_thermal_accreditation_vintage=armed,
    )


def main() -> dict:
    control, armed = _config(False), _config(True)

    out: dict = {
        "lane": "capx D84 phase 0 (zero LP)",
        "reference_bundle": str(REF.relative_to(REPO)),
        "reference_bundle_caveat": (
            "key bb6a60239d69508b; HEAD's bare pjm-t1h resolves "
            "f736025631d0d27e (Q55/Q56/Q58 landed after it). The fleet below "
            "is a MAGNITUDE ANCHOR, not the number the screen reproduces — the "
            "graded prediction is the IDENTITY, evaluated on the control's own "
            "entering fleet."
        ),
        "gate": (
            "STOP GATE (charter phase 0): if the predicted per-class "
            "accredited-MW move is ZERO in every delivery year in the window, "
            "the lane is INERT and ends here with that measurement as its "
            "result. Rule 29: it may kill the arm, never promote one, and it "
            "is never read against the target residual."
        ),
        "gate_armed_check": {
            "control": thermal_accreditation_vintage_armed(control, "PJM"),
            "arm": thermal_accreditation_vintage_armed(armed, "PJM"),
        },
        "reform_delivery_year": THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO[
            "PJM"
        ],
        "incumbent_table_vintage": "2026/2027 BRA (official/final)",
        "registry_delivery_years": sorted(
            THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"]
        ),
        "years": {},
    }

    window_total = 0.0
    for dy, model_year in DY_TO_MODEL_YEAR.items():
        led = _ledger(model_year)
        fleet = led.get("fleet_by_fuel_before") or {}
        basis_c = resolve_thermal_accreditation_basis("PJM", control, model_year)
        basis_a = resolve_thermal_accreditation_basis("PJM", armed, model_year)

        per_class: dict[str, dict] = {}
        acc_c = acc_a = 0.0
        for fuel in sorted(fleet):
            mw = float(fleet[fuel])
            fc = thermal_accreditation_fraction(fuel, EFORD, "PJM", control, model_year)
            fa = thermal_accreditation_fraction(fuel, EFORD, "PJM", armed, model_year)
            acc_c += mw * fc
            acc_a += mw * fa
            per_class[fuel] = {
                "nameplate_mw": mw,
                "rating_control": fc,
                "rating_arm": fa,
                "delta_rating": round(fa - fc, 12),
                "delta_accredited_mw": mw * (fa - fc),
            }

        delta = acc_a - acc_c
        window_total += delta
        clearing = led.get("capacity_clearing") or {}
        out["years"][dy] = {
            "model_year": model_year,
            "basis_control": basis_c,
            "basis_arm": basis_a,
            "on_elcc_axis": basis_a == "elcc_class_rating",
            "thermal_accredited_control_mw": acc_c,
            "thermal_accredited_arm_mw": acc_a,
            "delta_accredited_thermal_mw": delta,
            "delta_by_class_mw": {
                f: v["delta_accredited_mw"] for f, v in per_class.items()
            },
            "per_class": per_class,
            # Context from the reference ledger, reported not gated.
            "screen_entering_firm_mw": led.get("screen_entering_firm_mw"),
            "screen_adequacy_requirement_mw": led.get("screen_adequacy_requirement_mw"),
            "screen_reserve_position": led.get("screen_reserve_position"),
            "census_mw": clearing.get("census_mw"),
            "census_position": clearing.get("census_position"),
            "cleared_mw": clearing.get("cleared_mw"),
            "clearing_price_usd_per_mw_day": clearing.get("price_usd_per_mw_day"),
            "predicted_screen_position_arm": (
                (led["screen_entering_firm_mw"] + delta)
                / led["screen_adequacy_requirement_mw"]
                if led.get("screen_entering_firm_mw")
                and led.get("screen_adequacy_requirement_mw")
                else None
            ),
        }

    # THE IDENTITY, checked two ways: the per-class sum above, and the direct
    # registry-difference form the screen will be graded on.
    identity: dict = {}
    for dy, model_year in DY_TO_MODEL_YEAR.items():
        fleet = _ledger(model_year).get("fleet_by_fuel_before") or {}
        if out["years"][dy]["basis_arm"] != "elcc_class_rating":
            direct = 0.0
        else:
            vint = THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"].get(dy, {})
            base = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]
            direct = sum(
                float(fleet.get(f, 0.0)) * (vint[f] - base[f])
                for f in vint
                if f in base
            )
        identity[dy] = {
            "from_shipped_path_mw": out["years"][dy]["delta_accredited_thermal_mw"],
            "from_registry_difference_mw": direct,
            "abs_gap_mw": abs(direct - out["years"][dy]["delta_accredited_thermal_mw"]),
        }
    out["identity_check"] = {
        "rows": identity,
        "holds": all(r["abs_gap_mw"] < 1e-9 for r in identity.values()),
    }

    live = {
        dy: r["delta_accredited_thermal_mw"]
        for dy, r in out["years"].items()
        if abs(r["delta_accredited_thermal_mw"]) > 1e-9
    }
    out["prediction"] = {
        "in_window_delivery_years_on_the_elcc_axis": [
            dy for dy, r in out["years"].items() if r["on_elcc_axis"]
        ],
        "delivery_years_that_move": sorted(live),
        "delta_accredited_thermal_mw_by_dy": dict(sorted(live.items())),
        "window_total_mw": window_total,
        "sign": "UP" if window_total > 0 else ("DOWN" if window_total < 0 else "ZERO"),
    }
    out["stop_gate"] = {
        "verdict": "INERT — LANE ENDS" if not live else "LIVE — proceed to the screen",
        "reason": (
            "no delivery year in the 2021-2025 window moves"
            if not live
            else f"{len(live)} delivery year(s) move: {sorted(live)}"
        ),
    }
    return out


if __name__ == "__main__":
    result = main()
    (Path(__file__).with_suffix(".json")).write_text(
        json.dumps(result, indent=1) + "\n"
    )
    print(json.dumps(result["prediction"], indent=1))
    print(json.dumps(result["identity_check"], indent=1))
    print(json.dumps(result["stop_gate"], indent=1))
