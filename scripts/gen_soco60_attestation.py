"""SOCO-60: write ``calibration_attestation.json`` for the combined hydro keeper candidate.

The run is the keeper ``2026-09-22-soco-h4-hydro-ror`` (``hydro_ror_split``) plus
SOCO-59's 2025 hydro input repair (``hydro_eia930_monthly=True`` with
``EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025``). Built ON the two lanes'
generators rather than copied from them, so every inherited check is re-run on
THIS bundle:

* :func:`gen_soco58_attestation._verify` / ``_verify_scope`` — the offer-curve
  identity (gate G17), every SOCO-53f … SOCO-58 posture, the warm-boiler scope;
* :func:`gen_soco_h4_attestation.retag` — the hydro-4 DOF entries
  (``hydro_ror_split``, ``hydro_backfill_year``) and the offer-curve re-tag;
* SOCO-59's registry / fold-evidence checks (:func:`gen_soco59_attestation.
  _verify_scope` parts (a), (c), (d)).

What this module adds, BY EXECUTION (:func:`_verify_combined`):

1. ``hydro_ror_split`` is armed and ``hydro_min_flow_floor`` is not (rule 19);
2. the hydro budget the recipe builds (``ror_split=True, backfill_year=2024,
   eia930_monthly=True``) is byte-identical to the keeper construction in 2023
   and 2024 and equals 2025's own EIA-930 level in 2025;
3. the RoR carve matches PRECOMMIT-soco-60 §1: 14 LP plants flat at exactly
   their pinned ``budget / hours`` (clipped to nameplate), 2025 fleet flat base
   230.9 MW-avg, and the nameplate clip within the declared 5.45 GWh.

Pre-registration: ``docs/handoffs/PRECOMMIT-soco-60-2026-09-23.md``.
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
import gen_soco_h4_attestation as h4  # noqa: E402

BUNDLE = Path("results/calibration/soco60_hydro_ror_span")
ARM_META = {"hydro_backfill_year": 2024, "hydro_eia930_monthly": True}
ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
#: PRECOMMIT-soco-60 §1, measured at zero LP (``_soco60_phase0.py``).
RoR_PLANTS_IN_LP = 14
RoR_FLAT_MW_AVG_2025 = 230.9
CLIP_GWH_2025_MAX = 5.5


def _verify_combined(sc: dict, meta: dict, years: list[int]) -> dict:
    """Raise unless the combined recipe, the budgets and the RoR carve are as claimed."""
    import numpy as np  # noqa: PLC0415

    import market_sim.config.constants as K  # noqa: PLC0415
    from market_sim.data.eia_loader import measured_monthly_hydro  # noqa: PLC0415
    from market_sim.data.hydro import (  # noqa: PLC0415
        build_hydro_fleet,
        eia930_wat_level_folded,
        hours_per_month,
    )

    if sc.get("hydro_ror_split") is not True or sc.get("hydro_min_flow_floor"):
        raise SystemExit("hydro_ror_split must be armed and hydro_min_flow_floor off")
    for k, v in ARM_META.items():
        if meta.get(k) != v:
            raise SystemExit(f"bundle meta {k}={meta.get(k)!r}, expected {v!r}")
    rows = (
        json.loads((BUNDLE / "run_config.json").read_text()).get("solve_surface") or {}
    ).get("rows")
    if rows != 184:
        raise SystemExit(f"bundle solve_surface rows {rows!r}, expected 184")
    if K.EIA930_PS_SPLIT_COMPLETE_FROM.get("SOCO") != 2025:
        raise SystemExit("EIA930_PS_SPLIT_COMPLETE_FROM['SOCO'] is not 2025")
    for y, want in ((2023, True), (2024, True), (2025, False)):
        if eia930_wat_level_folded("SOCO", y) != want:
            raise SystemExit(f"SOCO {y} folded predicate != {want}")

    hpm = hours_per_month().astype(float)
    out: dict = {}
    for y in years:
        uc, bc = build_hydro_fleet("SOCO", y, ZONES, backfill_year=2024, ror_split=True)
        ua, ba = build_hydro_fleet(
            "SOCO", y, ZONES, backfill_year=2024, eia930_monthly=True, ror_split=True
        )
        bc, ba = np.asarray(bc, float), np.asarray(ba, float)
        ror = np.array([g.hydro_ror_flat_monthly_mw is not None for g in ua])
        if int(ror.sum()) != RoR_PLANTS_IN_LP:
            raise SystemExit(
                f"{y}: {int(ror.sum())} RoR plants in the LP, expected {RoR_PLANTS_IN_LP}"
            )
        flat = np.array(
            [g.hydro_ror_flat_monthly_mw for g in ua if g.hydro_ror_flat_monthly_mw]
        )
        pmax = np.array([g.pmax_mw for g in ua])[ror]
        raw = ba[ror] / hpm
        if not np.allclose(flat, np.minimum(raw, pmax[:, None])):
            raise SystemExit(f"{y}: RoR flat level != pinned budget / hours (clipped)")
        clip_gwh = float(((raw - flat).clip(0) * hpm).sum() / 1e3)
        flat_avg = float((flat.sum(0) * hpm).sum() / hpm.sum())
        if y < 2025:
            if bc.shape != ba.shape or not np.array_equal(bc, ba):
                raise SystemExit(
                    f"{y}: pinned budget differs from the keeper's — pin NOT refused"
                )
        else:
            target = float(np.nansum(measured_monthly_hydro("SOCO", y)))
            if abs(ba.sum() - target) > 1.0:
                raise SystemExit(
                    f"{y}: budget {ba.sum():.0f} != EIA-930 level {target:.0f} MWh"
                )
            if abs(flat_avg - RoR_FLAT_MW_AVG_2025) > 0.1:
                raise SystemExit(
                    f"2025 RoR flat {flat_avg:.1f} MW-avg != phase 0's {RoR_FLAT_MW_AVG_2025}"
                )
            if clip_gwh > CLIP_GWH_2025_MAX:
                raise SystemExit(
                    f"2025 nameplate clip {clip_gwh:.2f} GWh > declared {CLIP_GWH_2025_MAX}"
                )
        out[str(y)] = {
            "keeper_TWh": round(bc.sum() / 1e6, 4),
            "combined_TWh": round(ba.sum() / 1e6, 4),
            "ror_flat_mw_avg": round(flat_avg, 1),
            "ror_clip_GWh": round(clip_gwh, 2),
        }
    return out


def main() -> None:
    """Verify the combined run and write its attestation."""
    base.BUNDLE = BUNDLE
    att_path = BUNDLE / "calibration_attestation.json"
    att = json.loads(att_path.read_text()) if att_path.exists() else {}
    sc = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    meta = json.loads((BUNDLE / "meta.json").read_text())
    base._verify(sc)
    years = sorted(int(y) for y in meta["years"])
    warm = base._verify_scope(years)
    hyd = _verify_combined(sc, meta, years)
    print(f"combined hydro verification: {json.dumps(hyd, indent=1)}")

    att["schema"] = "calibration-attestation/v1"
    att["exceptions"] = []
    att["governance"] = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "attested_by": (
            "SOCO-60 (lane). The keeper 2026-09-22-soco-h4-hydro-ror COMBINED with "
            "SOCO-59's 2025 hydro input repair. ONE input moves against the keeper: "
            "hydro_eia930_monthly=True (the keeper already carries "
            "hydro_backfill_year=2024 and hydro_ror_split=True), solved at a HEAD "
            "carrying EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025. Every inherited "
            "posture is machine-verified by gen_soco58_attestation._verify / "
            f"_verify_scope (warm-boiler predicate {warm['warm_boiler_predicate_min_pct']}% "
            f"over {warm['plant_years_checked']} coal plant-years). "
            "VERIFIED BY EXECUTION: hydro_ror_split armed, hydro_min_flow_floor off "
            "(rule 19); the budget is byte-identical to the keeper's in 2023/2024 "
            f"({hyd['2023']['combined_TWh']} / {hyd['2024']['combined_TWh']} TWh — "
            "SOCO's pre-split EIA-930 hydro folds pumped-storage discharge, so the "
            "registry refuses the pin) and equals 2025's own EIA-930 hydro-ex-PS "
            f"level in 2025 ({hyd['2025']['keeper_TWh']} -> {hyd['2025']['combined_TWh']} TWh); "
            f"the RoR carve is {RoR_PLANTS_IN_LP} LP plants flat at exactly their "
            "pinned budget / hours, 2025 fleet flat base "
            f"{hyd['2025']['ror_flat_mw_avg']} MW-avg, nameplate clip "
            f"{hyd['2025']['ror_clip_GWh']} GWh (0.09 % of 2025 hydro; the uniform "
            "monthly rescale lifts three small RoR plants above nameplate in May/June "
            "— reported, not repaired; nameplate_aware_target is not this run's delta). "
            "RULE 13: a water-availability input with a forward analogue "
            "(hydro_forecast_budget); nothing measured about thermal dispatch is fed "
            "back. RULE 19: zero thermal fleet keys move in any year; in 2025 only the "
            "14 RoR hydro units' availability/min_gen move (their flat level). "
            "RULES 21/24/25: zero free parameters, zero new fields, SOCO's own data. "
            "GATE G17: SOCO has no price benchmark; every offer_curve_by_group band "
            "is 1.0 and AUTHORIZED PRICE TUNING IS DECLARED NONE (no "
            "authorized_price_tuning key). THIS RUN BUYS NO GATE: 2023/2024 are "
            "unchanged and every 2025 C1 row is SKIPPED on the preliminary vintage; "
            "it is taken on rule 14 [R-ACCURATE] alone. IF THE ONLY ARGUMENT FOR "
            "THIS ARM WERE THAT 2025 C4 COAL PASSES, IT WOULD NOT BE TAKEN."
        ),
    }
    att["disclosures"] = {
        "precommit": "docs/handoffs/PRECOMMIT-soco-60-2026-09-23.md",
        "composed_from_lanes": "SOCO hydro-4 (hydro_ror_split) + SOCO-59 (2025 hydro pin + PS-split registry)",
        "ror_nameplate_clip_2025": f"{hyd['2025']['ror_clip_GWh']} GWh clipped (plants 706, 54322, 54462; May/June)",
        "eia930_wat_gap": "SOCO NG: WAT missing 2024-11-25..12-31 (not used: 2024 refuses the pin)",
        "scarcity_2025": "2025-07-29 peak hours shed load (a routed demand-basis finding, RESULT-soco-hydro-4 §3)",
        "c8_hydro_attribution": "D-2 does not attribute the RoR min_gen stamps; hydro forced share reads 0.0 by construction",
    }
    h4.retag(att, sc, "ror")
    fp = att["free_parameters"]
    for entry in fp["entries"]:
        if entry["name"] == "hydro_backfill_year":
            entry["basis"] = (
                "SOCO-53b data repair, not a tuned value: the 2025 EIA-923 early release "
                "carries 5 of 42 SOCO hydro plants; the 2024 final census supplies the "
                "per-plant coverage, and under SOCO-60 the 2025 LEVEL and monthly SHAPE "
                "are then pinned to 2025's own EIA-930 hydro-ex-PS series (5.926 TWh). "
                "Array-equal no-op on the 2023 and 2024 budgets (verified by execution)."
            )
    fp["retag_note"] = fp.get("retag_note", "") + (
        " SOCO-60 ADDS NO ENTRY: hydro_eia930_monthly pins the level to a measured "
        "series, and EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025 is a measured date."
    )
    att_path.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {att_path} (n_residual={fp['n_residual']})")


if __name__ == "__main__":
    main()
