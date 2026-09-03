"""nyiso-179 — POST-GATE ROBUSTNESS on G1, explicitly labelled as such.

The gate probe ``nyiso179_st_gas_offer_position.py`` is FROZEN: its verdicts are
recorded in ``_nyiso179_st_gas_offer_position.json`` and this file changes none
of them. G1 fired stop condition S1, so it is the one gate whose failure mode is
worth bounding, and two alternative explanations for ``R < 1`` are checked here
that the gate as pre-registered cannot distinguish:

**R1 — the MARGINAL-TRANCHE artifact.** ``ITM`` counts a tranche in the money on
``mc <= price``. A tranche whose ``mc`` EQUALS the clearing price is marginal and
is only partially loaded by the LP, so counting it whole inflates ``ITM`` and
depresses ``R`` for a model that is behaving correctly. R1 recomputes ``R`` on a
STRICT bound (``mc < price - eps``) at several eps. If ``R`` moves into
``[0.70, 1.43]``, G1's failure is an accounting artifact and the finding must
say so; if it does not, the un-dispatched in-the-money capacity is real.

**R2 — reserve holding.** In a co-optimised LP, capacity that is in the money on
energy can still be held back to carry reserve. R2 cross-tabs the low-``R``
hours against the keeper's own ``reserve_family_<year>.parquet`` — the ONLY
artifact in which a locational reserve family's binding is observable — to see
whether the withheld MW coincides with a binding reserve family.

Neither is a gate. Both are reports, and both can contradict the finding's
preferred reading.

Run: PYTHONPATH=.:src python scripts/probes/nyiso179_g1_robustness.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyiso178_offer_side_idling import (  # noqa: E402
    HOURS,
    KEEPER,
    KLASS,
    YEARS,
    model_hourly,
)
from scripts.probes.nyiso179_st_gas_offer_position import (  # noqa: E402
    G1_R_HI,
    G1_R_LO,
    _cfg_obj,
    _decile_idx,
    build_year,
    price_rt,
)

OUT = REPO / "results/calibration/_nyiso179_g1_robustness.json"
EPS = (0.0, 0.01, 0.10, 1.00, 5.00)


def r1_strict(states: dict) -> dict:
    """R = model / ITM under progressively STRICTER in-the-money bounds."""
    per_year = {}
    for y in YEARS:
        st = states[y]
        cap = st["pmax"][:, None] * st["avail"]
        mo = model_hourly(y, KLASS)
        top = _decile_idx(price_rt(y))[-1]
        rows = []
        for eps in EPS:
            itm = np.where(st["mc"] <= st["p_model"] - eps, cap, 0.0).sum(axis=0)
            rows.append({
                "eps_usd_per_mwh": eps,
                "mean_itm_mw": round(float(itm.mean()), 1),
                "aggregate_R_all_hours": round(
                    float(mo.sum() / max(itm.sum(), 1.0)), 4
                ),
                "aggregate_R_top_decile": round(
                    float(mo[top].sum() / max(itm[top].sum(), 1.0)), 4
                ),
                "median_R": round(
                    float(np.median(mo / np.maximum(itm, 1.0))), 4
                ),
            })
        # How much of ITM sits within $1/MWh of the clearing price (marginal)?
        near = np.where(
            (st["mc"] <= st["p_model"]) & (st["mc"] > st["p_model"] - 1.0), cap, 0.0
        ).sum(axis=0)
        itm0 = np.where(st["mc"] <= st["p_model"], cap, 0.0).sum(axis=0)
        per_year[y] = {
            "by_eps": rows,
            "mean_marginal_mw_within_1usd": round(float(near.mean()), 1),
            "marginal_share_of_itm": round(
                float(near.sum() / max(itm0.sum(), 1e-9)), 4
            ),
        }
    # Does ANY eps bring every year into band on the aggregate?
    rescued = None
    for i, eps in enumerate(EPS):
        if all(
            G1_R_LO <= per_year[y]["by_eps"][i]["aggregate_R_all_hours"] <= G1_R_HI
            for y in YEARS
        ):
            rescued = eps
            break
    return {
        "bar": {"R_low": G1_R_LO, "R_high": G1_R_HI},
        "per_year": per_year,
        "eps_that_brings_all_years_into_band": rescued,
        "verdict": ("ARTIFACT — G1 rescued by a strict bound" if rescued is not None
                    else "REAL — un-dispatched in-the-money capacity survives"),
    }


def r2_reserve(states: dict) -> dict:
    """Do the low-R hours coincide with a BINDING reserve family?"""
    per_year = {}
    for y in YEARS:
        path = KEEPER / f"hourly/reserve_family_{y}.parquet"
        if not path.exists():
            per_year[y] = {"status": "no reserve_family sidecar"}
            continue
        d = pd.read_parquet(path)
        cols = list(d.columns)
        st = states[y]
        cap = st["pmax"][:, None] * st["avail"]
        itm = np.where(st["mc"] <= st["p_model"], cap, 0.0).sum(axis=0)
        mo = model_hourly(y, KLASS)
        gap = np.maximum(itm - mo, 0.0)  # in-the-money but not dispatched
        lowR = gap > 0.10 * np.maximum(itm, 1.0)

        pcol = next((c for c in ("price", "dual", "reserve_price", "shadow_price")
                     if c in cols), None)
        hcol = "hour" if "hour" in cols else None
        summary = {"columns": cols}
        if pcol and hcol:
            binding = (
                d.assign(_b=d[pcol].astype(float) > 1e-6)
                .groupby(hcol)["_b"].any()
                .reindex(range(HOURS)).fillna(False).to_numpy()
            )
            summary.update({
                "hours_any_family_binding": int(binding.sum()),
                "hours_withholding_gt_10pct": int(lowR.sum()),
                "hours_both": int((binding & lowR).sum()),
                "share_of_withholding_hours_with_binding_reserve": round(
                    float((binding & lowR).sum() / max(lowR.sum(), 1)), 4
                ),
            })
        summary.update({
            "mean_withheld_itm_mw": round(float(gap.mean()), 1),
            "total_withheld_twh": round(float(gap.sum()) / 1e6, 3),
        })
        per_year[y] = summary
    return {"per_year": per_year}


def r3_p1_markup(states: dict, cfg) -> dict:
    """Is the reconstructed mc the P1 BID cost, or only the P0 BASE cost?

    THE CONCERN, raised against this session's own instrument. P1 clears on
    ``mc_bid = mc_base + compute_monthly_markup(...)`` (``pipeline/solve.py:295``)
    while ``assemble_mc`` returns ``mc_base``. If ``ST_GAS`` carried a markup,
    every ITM figure above would be computed against an offer CHEAPER than the
    one the LP actually cleared, ITM would be overstated and R understated —
    i.e. it would manufacture G1's failure.

    THE ANSWER IS STRUCTURAL, not an estimate. ``commitment.py:312`` reads
    ``if gen.fuel_type == "gas_st" and not gas_st_startup_cost: continue`` — the
    ST_GAS limb is skipped outright — and this keeper carries
    ``gas_st_startup_cost = False``. Every ``ST_GAS`` row's markup is therefore
    IDENTICALLY ZERO and ``mc_bid == mc_base`` for the class, so the
    reconstruction is the LP's exact P1 objective coefficient.

    Verified here rather than asserted: the flag's value is read from the
    keeper's own config and every ST_GAS bin's ``fuel_type`` is confirmed to be
    the ``gas_st`` the guard keys on. ``mc_bid_adjust`` is ERCOT-only (None
    here); the three P1 bridges inject ``min_gen`` floors, never offer changes.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    ic = get_iso_config("NYISO")
    zones = [z.name for z in ic.zones]
    cfg_y = cfg.with_overrides(weather_year=2023)
    bins = load_or_synthesize_bins(cfg_y, "NYISO", ic, [])
    gens, _ = bins_to_fleet(bins, zones, cfg_y)
    fts = sorted({
        str(getattr(g, "fuel_type", "")) for g in gens
        if str(getattr(g, "plant_group", "")) == KLASS
    })
    flag = bool(getattr(cfg, "gas_st_startup_cost", False))
    guard_fires = (not flag) and fts == ["gas_st"]
    return {
        "keeper_gas_st_startup_cost": flag,
        "st_gas_fuel_types_in_lp": fts,
        "guard_at_commitment_py_312": "fuel_type == 'gas_st' and not gas_st_startup_cost",
        "markup_identically_zero_for_st_gas": guard_fires,
        "mc_bid_adjust_scope": "ERCOT-only (None for NYISO)",
        "verdict": ("CLOSED — reconstruction IS the P1 bid cost for ST_GAS"
                    if guard_fires else
                    "OPEN — ST_GAS carries a P1 markup the instrument omits"),
    }


def r4_zero_itm_hours(states: dict) -> dict:
    """Sanity: in hours nothing is in the money, what does the model still run?

    Whatever it runs there is forced (min-gen floors / the commitment bridge),
    not economic, so this bounds the forced component that inflates R and is a
    coherence check on the whole reconstruction.
    """
    out = {}
    for y in YEARS:
        st = states[y]
        cap = st["pmax"][:, None] * st["avail"]
        itm = np.where(st["mc"] <= st["p_model"], cap, 0.0).sum(axis=0)
        mo = model_hourly(y, KLASS)
        z = itm < 1.0
        out[y] = {
            "hours_zero_itm": int(z.sum()),
            "mean_model_mw_in_zero_itm_hours": round(
                float(mo[z].mean()) if z.any() else 0.0, 1
            ),
            "max_model_mw_in_zero_itm_hours": round(
                float(mo[z].max()) if z.any() else 0.0, 1
            ),
            "mean_model_mw_all_hours": round(float(mo.mean()), 1),
        }
    return out


def main() -> None:
    cfg = _cfg_obj()
    states = {y: build_year(y, cfg) for y in YEARS}
    rec = {
        "session": "nyiso-179",
        "kind": "POST-GATE ROBUSTNESS — reports only, no gate verdict changes",
        "frozen_gate_record": "results/calibration/_nyiso179_st_gas_offer_position.json",
        "R1_marginal_tranche": r1_strict(states),
        "R2_reserve_holding": r2_reserve(states),
        "R3_p1_bid_cost": r3_p1_markup(states, cfg),
        "R4_zero_itm_hours": r4_zero_itm_hours(states),
    }
    OUT.write_text(json.dumps(rec, indent=2, default=str))

    r1 = rec["R1_marginal_tranche"]
    print(f"R1 {r1['verdict']}   rescuing eps = {r1['eps_that_brings_all_years_into_band']}")
    for y in YEARS:
        p = r1["per_year"][y]
        print(f"  {y}  marginal-within-$1 {p['mean_marginal_mw_within_1usd']:.0f} MW "
              f"({p['marginal_share_of_itm']:.3f} of ITM)")
        for row in p["by_eps"]:
            print(f"      eps {row['eps_usd_per_mwh']:>5.2f}  ITM "
                  f"{row['mean_itm_mw']:>7.1f}  aggR all "
                  f"{row['aggregate_R_all_hours']:.3f}  top "
                  f"{row['aggregate_R_top_decile']:.3f}  median "
                  f"{row['median_R']:.3f}")
    print("\nR2 reserve holding")
    for y in YEARS:
        print(f"  {y}  {rec['R2_reserve_holding']['per_year'][y]}")
    print(f"\nR3 {rec['R3_p1_bid_cost']['verdict']}")
    print(f"   {rec['R3_p1_bid_cost']}")
    print("\nR4 zero-ITM hours")
    for y in YEARS:
        print(f"  {y}  {rec['R4_zero_itm_hours'][y]}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
