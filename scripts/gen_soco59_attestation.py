"""SOCO-59: write ``calibration_attestation.json`` for the 2025 hydro-hole arm.

Built ON :mod:`scripts.gen_soco58_attestation` rather than copied from it: every
inherited governance check (the offer-curve identity, gate G17, the six inherited
postures, the rule-19 exclusions on the coal committed band, SOCO-58's own
by-execution warm-boiler scope) is re-run on THIS bundle by calling that module
with its ``BUNDLE`` pointed here. A bundle that silently dropped any inherited
posture therefore fails exactly as it would have failed SOCO-58's attestation.

THE DELTA. Three things, and the attestation claims all three:

* ``meta.json`` ``hydro_backfill_year = 2024`` and ``hydro_eia930_monthly = True``
  — the NEISO / MISO keeper construction, carried as ``solve_and_persist``
  kwargs (not ``ScenarioConfig`` fields, so they are asserted off ``meta.json``);
* ``EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] == 2025`` at the HEAD the legs solved
  on, which REFUSES the EIA-930 level pin in 2023 and 2024 because SOCO's
  pre-split EIA-930 hydro column folds pumped-storage DISCHARGE.

**THE VERIFICATION SHAPE.** This lane ships a registry row, not a CSV, and no
fleet grain moves in 2023/2024. :func:`_verify_scope` therefore checks BY
EXECUTION the four factual claims the attestation makes, and raises otherwise:
(a) the live registry row is 2025 and SOCO's predicate reads folded for 2023 /
2024 and clean for 2025; (b) the hydro budget the recipe builds is
byte-identical to the control construction in 2023 and 2024 and equals 2025's own
EIA-930 level in 2025; (c) the fold evidence (nameplate breach, diurnal swing)
reproduces from the raw EIA-930 extract; (d) every leg recorded 184 solve-surface
rows, i.e. solved WITH the registration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen_soco58_attestation as base  # noqa: E402

BUNDLE = Path("results/calibration/soco59_hydro_split")
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
#: SOCO's conventional-hydro EIA-860 nameplate (soco-data-audit §2 table).
HY_NAMEPLATE_MW = 3317.6


def _verify_scope(years: list[int]) -> dict:
    """Raise unless the registration, the budgets and the fold evidence are as claimed."""
    import numpy as np  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    import market_sim.config.constants as K  # noqa: PLC0415
    from market_sim.data.eia_loader import measured_monthly_hydro  # noqa: PLC0415
    from market_sim.data.hydro import (  # noqa: PLC0415
        build_hydro_fleet,
        eia930_wat_level_folded,
    )

    # (a) the registry row and the predicate it drives
    if K.EIA930_PS_SPLIT_COMPLETE_FROM.get("SOCO") != 2025:
        raise SystemExit("EIA930_PS_SPLIT_COMPLETE_FROM['SOCO'] is not 2025")
    if "SOCO" in K.EIA930_PS_FOLDED_INTO_WAT:
        raise SystemExit("SOCO is flat-listed — the split registry would be moot")
    for y, want in ((2023, True), (2024, True), (2025, False)):
        if eia930_wat_level_folded("SOCO", y) != want:
            raise SystemExit(f"SOCO {y} folded predicate != {want}")

    # (b) the budgets: control construction vs this recipe, per year
    budgets = {}
    for y in years:
        _, ctrl = build_hydro_fleet("SOCO", y, ZONES)
        _, arm = build_hydro_fleet(
            "SOCO", y, ZONES, backfill_year=2024, eia930_monthly=True
        )
        ctrl, arm = np.asarray(ctrl, float), np.asarray(arm, float)
        if y < 2025:
            if ctrl.shape != arm.shape or not np.array_equal(ctrl, arm):
                raise SystemExit(
                    f"{y}: arm hydro budget differs from control — the pin was NOT refused"
                )
        else:
            target = float(np.nansum(measured_monthly_hydro("SOCO", y)))
            if abs(arm.sum() - target) > 1.0:  # MWh
                raise SystemExit(
                    f"{y}: arm budget {arm.sum():.0f} != EIA-930 level {target:.0f} MWh"
                )
        budgets[str(y)] = {
            "control_TWh": round(ctrl.sum() / 1e6, 4),
            "arm_TWh": round(arm.sum() / 1e6, 4),
        }

    # (c) the fold evidence, recomputed from the raw extract
    fold = {}
    for y, col in (
        (2023, "Net Generation (MW) from Hydropower and Pumped Storage"),
        (2025, "Net Generation (MW) from Hydropower Excluding Pumped Storage"),
    ):
        d = pd.concat(
            pd.read_parquet(_ROOT / f"data/raw/eia-930/EIA930_BALANCE_{y}_{h}.parquet")
            for h in ("Jan_Jun", "Jul_Dec")
        )
        d = d[d["Balancing Authority"] == "SOCO"]
        x = pd.to_numeric(d[col], errors="coerce")
        hr = pd.to_datetime(d["Local Time at End of Hour"]).dt.hour
        prof = x.groupby(hr).mean()
        fold[str(y)] = {
            "hours_above_nameplate": int((x > HY_NAMEPLATE_MW).sum()),
            "diurnal_swing": round(float(prof.max() / prof.min()), 2),
        }
    if not (
        fold["2023"]["hours_above_nameplate"] > 0
        and fold["2025"]["hours_above_nameplate"] == 0
    ):
        raise SystemExit(f"nameplate-breach fingerprint does not reproduce: {fold}")
    if not fold["2023"]["diurnal_swing"] > 1.5 * fold["2025"]["diurnal_swing"]:
        raise SystemExit(f"diurnal-swing fingerprint does not reproduce: {fold}")

    # (d) the bundle's own recipe and its legs' solve surfaces
    meta = json.loads((BUNDLE / "meta.json").read_text())
    for k, v in ARM_META.items():
        if meta.get(k) != v:
            raise SystemExit(f"bundle meta {k}={meta.get(k)!r}, expected {v!r}")
    rows = (
        json.loads((BUNDLE / "run_config.json").read_text()).get("solve_surface") or {}
    ).get("rows")
    if rows != 184:
        raise SystemExit(f"bundle solve_surface rows {rows!r}, expected 184")
    return {"registry": {"SOCO": 2025}, "budgets": budgets, "fold_evidence": fold}


def main() -> None:
    """Write ``calibration_attestation.json`` into the SOCO-59 bundle."""
    base.BUNDLE = BUNDLE
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    base._verify(sc)  # every inherited governance assertion, SOCO-58's delta included
    years = sorted(
        int(y) for y in json.loads((BUNDLE / "meta.json").read_text())["years"]
    )
    warm = base._verify_scope(years)  # SOCO-58's warm-boiler scope, re-verified here
    hydro = _verify_scope(years)
    print(f"hydro scope verification: {json.dumps(hydro, indent=1)}")

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    b = hydro["budgets"]
    f = hydro["fold_evidence"]
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-59 (lane). ONE mechanism moves against the incumbent keeper "
            "2026-09-22-soco58-warm-committed: the conventional-hydro energy budget "
            "input. The run carries hydro_backfill_year=2024 and "
            "hydro_eia930_monthly=True (the NEISO / MISO keeper construction), with "
            "EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025 registered at the HEAD it "
            "solved on. Everything else is the keeper's recipe unchanged, "
            "machine-verified by re-running gen_soco58_attestation._verify and "
            "_verify_scope on this bundle (the warm-boiler predicate holds at "
            f"{warm['warm_boiler_predicate_min_pct']}% over "
            f"{warm['plant_years_checked']} coal plant-years here too). "
            "THE CLAIM IS ABOUT AN INPUT, NOT THE RESIDUAL. The keeper's 2025 hydro "
            f"budget was {b['2025']['control_TWh']} TWh because the preliminary "
            "EIA-923 vintage carries 5 of SOCO's 42 hydro plants; this run carries "
            f"{b['2025']['arm_TWh']} TWh, 2025's own measured EIA-930 hydro-ex-PS "
            "monthly series, with per-plant shares from the 2024 census. 2023 and "
            f"2024 are unchanged ({b['2023']['arm_TWh']} / {b['2024']['arm_TWh']} TWh, "
            "byte-identical to the control construction, verified by execution) "
            "because their EIA-930 column FOLDS PUMPED-STORAGE DISCHARGE and the "
            "registration refuses the pin there. "
            "THE FOLD IS MEASURED ON SOCO'S OWN DATA, recomputed here from the raw "
            f"extract: the pre-split column exceeds the {HY_NAMEPLATE_MW} MW "
            f"conventional nameplate in {f['2023']['hours_above_nameplate']} h of 2023 "
            f"against {f['2025']['hours_above_nameplate']} h of 2025's clean column, "
            f"and its diurnal swing is {f['2023']['diurnal_swing']}x against "
            f"{f['2025']['diurnal_swing']}x. SOCO's pumped storage is endogenous "
            "(1,306.6 MW), so pinning a pre-split year would double-count its "
            "discharge. soco-data-audit §3.3's 'never negative' reading excluded "
            "folded PUMPING only; NEISO's fold (neiso-72) was discharge-only too. "
            "RULE 13 [R-MEASURED]: a hydro energy budget is a water-availability "
            "input with a forward analogue (hydro_forecast_budget, mutually exclusive "
            "with the backcast pin in build_hydro_fleet). Nothing measured about "
            "thermal dispatch is fed back. "
            "RULE 19 [R-ONE-MECH]: keyed by unit_id, 2023 and 2024 move 0 of 327 "
            "units on fuel_prices / mc_base / pmax / availability / heat_rate; 2025 "
            "adds 37 hydro units and moves 0 of 290 shared keys. "
            "RULES 21 / 24 / 25: zero free parameters, zero new ScenarioConfig "
            "fields, the registry row is SOCO's own measurement and no other ISO's "
            "row moves; SOCO's cache key does not move either (a first-time per-ISO "
            "row has no frozen declaration). "
            "GATE G17 — SOCO HAS NO PRICE BENCHMARK AND GAINS NONE. Every "
            "offer_curve_by_group band is exactly 1.0; AUTHORIZED PRICE TUNING IS "
            "DECLARED NONE and no authorized_price_tuning key is written. "
            "WHAT THIS LANE DOES NOT CLAIM: it does not reach the run's only failing "
            "row (2024 CC_REGULAR), which it cannot touch by construction; every "
            "2025 C1 row it improves is SKIPPED on the preliminary vintage, so it "
            "buys no gate; and the 2025 coal overshoot is mostly NOT a hydro "
            "artifact — the water displaces CT_PEAKER and CC first. IF THE ONLY "
            "ARGUMENT FOR THIS ARM WERE THAT A 2025 ROW IMPROVES, IT WOULD NOT BE TAKEN."
        ),
    }
    att["disclosures"] = base._disclosures(warm)
    att["disclosures"]["note"] = (
        "SOCO-59 determination basis. Items 1-7 are SOCO-58's, carried because the "
        "mechanisms they describe are inherited unchanged; items 8+ are this lane's. "
        "Two SOCO-58 statements are CORRECTED by item 9 and item 10."
    )
    att["disclosures"]["8_THIS_ARM_BUYS_NO_GATE_AND_DOES_NOT_REACH_THE_FAILING_ROW"] = (
        "The only failing criterion-row, 2024 CC_REGULAR (+10.42 TWh of a +/-7.47 "
        "band, +4.03 pp of +/-3.00), is untouched by construction: 2024's hydro "
        "budget is byte-identical. Every 2025 C1 row is SKIPPED. The arm is taken on "
        "rule 14 [R-ACCURATE] alone."
    )
    att["disclosures"]["9_CORRECTION_THE_SCHERER_LEAD_WAS_A_NAME_SWAP"] = (
        "SOCO-58's tables (and item 4 above) label plant 703 'Scherer' and 6257 "
        "'Bowen'. EIA-923, CAMPD and the model's own tranche table all say 703 = "
        "Bowen (100 % bituminous, $5.08/MMBtu delivered 2024) and 6257 = Scherer "
        "(100 % Wyoming PRB, $3.12). Class and price are correct at all six coal "
        "plants to <= $0.02/MMBtu; there is no coal-price repair."
    )
    att["disclosures"][
        "10_CORRECTION_HYDRO_DOES_NOT_ABSORB_THE_2025_COAL_OVERSHOOT"
    ] = (
        "Item 3 above (SOCO-58) said correcting hydro 'would push 2025 coal DOWN by "
        "up to ~5.7 TWh'. That was the arithmetic ceiling; the merit order puts the "
        "water on CT_PEAKER and CC first. See the FINDING for the measured split."
    )
    att["disclosures"]["11_BENCHMARK_HYDRO_ROW_FOLDS_PS_IN_2023_2024"] = (
        "SOCO's C1 benchmark hydro row for 2023 / 2024 reads the PS-folded EIA-930 "
        "column (8.447 / 7.080 TWh). Hydro is not a scored free class, so no gate "
        "moves; it is a benchmark-side rule-14 defect ROUTED, not fixed here."
    )
    base._retag(att, sc, warm)
    att["free_parameters"]["retag_note"] += (
        " SOCO-59 ADDS NO ENTRY: the hydro energy budget is a measured input "
        "(EIA-923 HY census / EIA-930 hydro-ex-PS level) with no scalar of its "
        "own, and EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025 is a measured date."
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path}")


if __name__ == "__main__":
    main()
