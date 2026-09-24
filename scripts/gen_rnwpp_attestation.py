"""Emit the R-NWPP calibration attestation for ``results/calibration/rnwpp_span``.

R-NWPP (audit ``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md``
§5.3.5) re-solves NWPP on CORRECTED BACKCAST INPUTS: the NWPP-49 keeper's recipe
with the F1 input flags pinned on (year-matched EIA-860, measured CT / coal / ST /
CC / CHP heat rates), the F2 short-coal and unit-partial CAMPD outage families,
and ``mid_vintage_exit_carry`` (the SPP keeper's zero-DOF completion of the vintage
channel). Offer-curve band multipliers are UNCHANGED (sha256 ``ac3344c3…``);
``authorized_price_tuning`` is NONE (NWPP is price-unscored, rubric v3.8).

**ZERO NEW FREE PARAMETERS** (rules 21 / 24): every arm is a measured input or a
set membership over EIA's own sheets. One per-year input difference is declared,
not fitted: ``hydro_backfill_year`` is ``None`` for 2019 / 2021 / 2022 (the 2024
backfill would inject plants not yet built) and the keeper's ``2024`` for
2023-2025. It is a solve kwarg, not a ``ScenarioConfig`` field, so a replay of a
pre-2023 year passes ``--set hydro_backfill_year=null``.

Pre-registration: ``docs/handoffs/PRECOMMIT-r-nwpp-2019-2025-inputs-2026-09-24.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402

DEFAULT_BUNDLE = REPO / "results/calibration/rnwpp_span"
KEEPER_BUNDLE = REPO / "results/calibration/nwpp49_ror_span"
OFFER_CURVE_SHA256 = "ac3344c3ef16e3ae63673a92886aa2873fc7090543eb04e6d6abf89fb52c73c2"

#: This lane's arms (all must read True in every year's run_config).
_ARMED = (
    "eia860_vintage_tracks_solve_year",
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_partial_outage_windows",
    "mid_vintage_exit_carry",
)

#: Inherited from the NWPP-49 keeper and unchanged.
_INHERITED = {
    "unit_outage_short_windows_gas": False,
    "hydro_ror_split": True,
    "nwpp_grid_carried_wind_served": True,
    "hydro_dispatch_envelope": True,
    "hydro_min_flow_floor": True,
    "hydro_cascade_coupling": True,
    "plant_level_fleet": True,
    "use_campd_bins": True,
    "mode": "backcast",
}

_SOURCES = {
    "eia860_vintage_tracks_solve_year": (
        "EIA-860 annual release matching the solve year (vintage_2019..2024; the "
        "canonical 2025ER snapshot for 2025), year-matched eGRID heat-rate join (F1)"
    ),
    "measured_ct_heat_rates": "EPA CAMPD hourly heatInput/grossLoad, per plant, per year (F1; NWPP re-derived on F2's raw)",
    "measured_coal_heat_rates": "EPA CAMPD hourly heatInput/grossLoad, per plant, per year (F1; NWPP re-derived on F2's raw)",
    "measured_st_heat_rates": "EPA CAMPD hourly heatInput/grossLoad, per plant, per year (F1; NWPP re-derived on F2's raw)",
    "measured_cc_heat_rates": "EPA CAMPD hourly heatInput/grossLoad, per plant, per year (F1; NWPP re-derived on F2's raw)",
    "measured_chp_heat_rates": "eGRID + CAMPD power-only CHP credit, per eGRID vintage (F1)",
    "unit_outage_short_windows": "EPA CAMPD sub-5-day coal outage windows (campd-unit-outages-short-NWPP.csv, F2, 2019-2025)",
    "unit_partial_outage_windows": "EPA CAMPD unit partial-derate windows (campd-partial-outages-NWPP.csv, F2, 2019-2025)",
    "mid_vintage_exit_carry": (
        "EIA-860 Retired-and-Canceled sheet: a plant retiring DURING the vintage year "
        "stays online through its published retirement month (SPP-48 mechanism)"
    ),
}


def _check_recipe(bundle: Path) -> list[int]:
    """Refuse a bundle whose any year is not the R-NWPP recipe; return the years."""
    import hashlib

    years = json.loads((bundle / "meta.json").read_text())["years"]
    bad = []
    for y in years:
        sc = json.loads((bundle / f"run_config_{y}.json").read_text())[
            "scenario_config"
        ]
        bad += [
            f"{y} {f} = {sc.get(f)!r}, expected True"
            for f in _ARMED
            if sc.get(f) is not True
        ]
        bad += [
            f"{y} {f} = {sc.get(f)!r}, expected {w!r} (inherited)"
            for f, w in _INHERITED.items()
            if sc.get(f) != w
        ]
        h = hashlib.sha256(
            json.dumps(sc["offer_curve_by_group"], sort_keys=True).encode()
        ).hexdigest()
        if h != OFFER_CURVE_SHA256:
            bad.append(
                f"{y} offer_curve_by_group sha256 {h} != keeper {OFFER_CURVE_SHA256}"
            )
    if bad:
        raise SystemExit(
            "gen_rnwpp_attestation refuses this bundle:\n  " + "\n  ".join(bad)
        )
    return years


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the R-NWPP attestation (after seeding the canonical DOF ledger)."""
    years = _check_recipe(bundle)
    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    keeper = json.loads((KEEPER_BUNDLE / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"
    att["lane"] = "R-NWPP"
    att["bundle"] = bundle.name

    switches = dict(keeper.get("switches", {}))
    for f in _ARMED:
        switches[f] = {
            "value": True,
            "where": f"ScenarioConfig.{f}, pinned through replay_keeper --set",
            "identification": "measured-physical",
            "source": _SOURCES[f],
        }
    switches["hydro_backfill_year"] = {
        "value": {
            "2019": None,
            "2021": None,
            "2022": None,
            "2023": 2024,
            "2024": 2024,
            "2025": 2024,
        },
        "where": "solve_and_persist kwarg (not a ScenarioConfig field); per-year input choice",
        "identification": "measured-physical",
        "source": (
            "EIA-923 hydro monthly generation. The 2024 backfill exists for the 2025 early "
            "release; before 2023 it would inject plants that did not report (or exist) that "
            "year, so it is off there (rule 14). 2023-2025 keep the keeper's value."
        ),
    }
    att["switches"] = switches

    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "authorized_price_tuning": None,
        "notes": (
            "An input correction ordered by the owner (2026-09-24): year-correct EIA-860, "
            "plant-specific measured heat rates, granular CAMPD outages. Every arm is a "
            "measured input that regenerates for any year from that year's own publications "
            "(rule 13). Offer-curve multipliers byte-identical to the NWPP-49 keeper "
            f"(sha256 {OFFER_CURVE_SHA256[:12]}...); nothing swept, nothing selected on a gate. "
            "Short-gas outage windows deliberately NOT armed: the detector's merit guard booked "
            "0 of 9,590 NWPP windows as economic layup (PRECOMMIT section 4)."
        ),
    }
    att["exceptions"] = []
    disc = att.setdefault("disclosures", {})
    disc["years"] = (
        f"Solved {years}. 2020 is DATA-BLOCKED: PSEI demand is absent from EIA-930 for 8,659 "
        "of 8,784 hours of 2020, and the pool loader would interpolate across it."
    )
    disc["structure_gap_pre_2023"] = (
        "hydro_cascade_coupling is armed but INERT in 2019 / 2021 / 2022: the CROHMS-derived "
        "cascade artifact covers 2023-2025 only. Those years run the keeper hydro structure "
        "minus the Columbia/Snake coupling; envelope, min-flow floor and RoR split read "
        "own-year data."
    )
    disc["not_a_pure_ab_against_the_keeper"] = (
        "F1 also rejoined the canonical EIA-860 heat rate to eGRID 2024, which moves "
        "2023-2025 inputs even at the keeper's flag values, so the 2023-2025 deltas are the "
        "whole corrected-input bundle, not one switch."
    )
    return att


def main() -> int:
    """CLI: print or write the attestation."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    bundle = Path(args.bundle)
    att = build(bundle)
    out = bundle / "calibration_attestation.json"
    if args.write:
        out.write_text(json.dumps(att, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
    else:
        print(json.dumps(att, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
