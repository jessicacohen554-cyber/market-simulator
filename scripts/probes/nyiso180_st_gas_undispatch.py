"""nyiso-180 phase 0 — WHY in-the-money ``ST_GAS`` goes un-dispatched.

Gates are fixed in ``results/calibration/PREREG-nyiso180-st-gas-undispatch.md``,
committed with this file BEFORE either ran. Zero solves.

The object is nyiso-179 §6.1: 3.84 / 9.09 / 3.99 TWh a year of ``ST_GAS`` that
the model's own offer prices into the money at its own P1 zonal price and that
it does not run. §6.1 named three candidate explanations; PREREG §0 refutes (a)
and (b) STRUCTURALLY by code reading (the loss coefficient lands on Flow
columns only; the price overlays are ERCOT-gated), leaving:

* **G1** — (c) a capacity/label-basis mismatch. The dual-fuel re-attribution
  (``_dispatch_frame`` :455) relabels every oil-switched (gen, hour) to
  ``klass == "oil"``, so ``class_hourly``'s ``ST_GAS`` UNDERCOUNTS the class by
  exactly the switched MWh while the ITM denominator counts every bin in every
  hour. Bounded exactly from both sides; the pooled ``oil`` class gives a
  strict upper bound.
* **G2** — (d) a binding LP row other than the energy balance (armed
  ``ramp_limits`` plant-group envelopes). ONE-SIDED BY CONSTRUCTION: the rows
  are per (plant, bucket) group and the committed artifact is a class
  aggregate, so this can IMPLICATE but never exonerate (PREREG §2 G2).
* **G3** — the armed-row inventory, establishing PREREG §0.1: the LP optimality
  condition is the REDUCED COST, not ``mc <= price_z``, so the object's
  inherited premise does not hold on this keeper.

The switch mask is reconstructed EXACTLY, with no re-derivation: the LP's
``apply_dual_fuel_pricing`` writes ``min(gas, oil)`` in place, so a switched
generator-hour is precisely one where the pre-min array exceeds the post-min
array. Both arrays are already built by nyiso-179's ``build_year``.

Run: PYTHONPATH=.:src python scripts/probes/nyiso180_st_gas_undispatch.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# Reuse nyiso-179's / nyiso-178's VALIDATED instruments verbatim (brief).
from scripts.probes.nyiso179_st_gas_offer_position import (  # noqa: E402
    HOURS,
    ISO,
    KEEPER,
    KLASS,
    YEARS,
    _cfg_obj,
    build_year,
    model_hourly,
)

OUT = REPO / "results/calibration/_nyiso180_st_gas_undispatch.json"

# ---------------------------------------------------------------------------
# Bars — ALL fixed in the PREREG before this file ran. None is movable.
# ---------------------------------------------------------------------------
#: G1 floor and statistic are INHERITED from nyiso-179, not chosen here.
G1_R_FLOOR = 0.70
#: G1 instrument check: R_lo must reproduce nyiso-179's published medians.
G1_PUBLISHED_MEDIAN = {2023: 0.775, 2024: 0.448, 2025: 0.816}
G1_REPRO_TOL = 0.005
#: G2 (one-sided): share of hours whose class delta reaches the envelope.
G2_CLIP_FRAC = 0.95
G2_IMPLICATE_BAR = 0.05


def _ratio(num: np.ndarray, itm: np.ndarray) -> np.ndarray:
    """nyiso-179's per-hour ratio, verbatim (its §8.2 guarded form)."""
    return num / np.maximum(itm, 1.0)


def gate1(st: dict, year: int) -> dict:
    """G1 — (c) the oil-relabelling bound. Two EXACT bounds; can fail both ways."""
    itm = ((st["mc"] <= st["p_model"]) * st["pmax"][:, None] * st["avail"]).sum(axis=0)
    n_lo = model_hourly(year, KLASS)
    oil = model_hourly(year, "oil")
    n_hi = n_lo + oil

    # s(t): ST_GAS's share of SWITCHED capacity, over the whole LP fleet.
    # Reported only -- PREREG §2 forbids it deciding the verdict.
    sw_st = (st["fuel_nodf"] > st["fuel"]) * st["pmax"][:, None] * st["avail"]
    sw_st_mw = sw_st.sum(axis=0)
    sw_all_mw = _switched_capacity_all_classes(year)
    s_t = np.divide(
        sw_st_mw, sw_all_mw, out=np.zeros(HOURS), where=sw_all_mw > 1e-9
    )
    n_mid = n_lo + s_t * oil

    def rep(n):
        r = _ratio(n, itm)
        return {
            "median_R": float(np.median(r)),
            "aggregate_R": float(n.sum() / itm.sum()),
            "mean_mw": float(n.mean()),
        }

    lo, hi, mid = rep(n_lo), rep(n_hi), rep(n_mid)
    repro = abs(lo["median_R"] - G1_PUBLISHED_MEDIAN[year])
    return {
        "year": year,
        "mean_itm_mw": float(itm.mean()),
        "mean_oil_mw": float(oil.mean()),
        "R_lo": lo,
        "R_hi": hi,
        "R_mid_REPORT_ONLY": mid,
        "st_gas_share_of_switched_capacity_mean": float(s_t[sw_all_mw > 1e-9].mean())
        if (sw_all_mw > 1e-9).any()
        else 0.0,
        "hours_any_switch": int((sw_all_mw > 1e-9).sum()),
        "reproduces_nyiso179": bool(repro <= G1_REPRO_TOL),
        "repro_abs_diff": float(repro),
        "clears_floor_lo": bool(lo["median_R"] >= G1_R_FLOOR),
        "clears_floor_hi": bool(hi["median_R"] >= G1_R_FLOOR),
    }


def _switched_capacity_all_classes(year: int) -> np.ndarray:
    """(T,) switched pmax*availability over EVERY dual-fuel-capable LP unit.

    Same exact reconstruction as the ST_GAS leg (pre-min > post-min), but over
    the whole fleet, because ``klass == "oil"`` is a POOLED class: CC / CT /
    ST_CHP units relabel into it too, and attributing all of it to ST_GAS is
    only an upper bound (PREREG §2 G1).
    """
    from market_sim.data.fleet.legacy_bins import assemble_mc  # noqa: F401
    from market_sim.data.fuel import resolve_fuel_prices

    from scripts.probes.nyiso178_offer_side_idling import lp_fleet

    cfg_obj = _cfg_obj()
    _g, fa = lp_fleet(year, cfg_obj)
    cfg_y = cfg_obj.with_overrides(weather_year=year)
    cfg_n = cfg_obj.with_overrides(weather_year=year, dual_fuel_switching=False)
    f_on = resolve_fuel_prices(cfg_y, fa, year)
    f_off = resolve_fuel_prices(cfg_n, fa, year)
    sw = (f_off > f_on) * np.asarray(fa.pmax)[:, None] * np.asarray(fa.availability)
    return sw.sum(axis=0)[:HOURS]


def gate2(year: int) -> dict:
    """G2 — (d) the ramp envelope. ONE-SIDED: can implicate, never exonerate."""
    from market_sim.data.fleet.campd_bins import build_ramp_groups

    from scripts.probes.nyiso178_offer_side_idling import lp_fleet

    cfg_obj = _cfg_obj()
    _g, fa = lp_fleet(year, cfg_obj)
    groups = build_ramp_groups(fa, ISO)
    if groups is None:
        return {"year": year, "verdict": "NO RAMP GROUPS", "n_groups": 0}
    gen_idx, group_col, ru, rd = groups
    pg = np.asarray(fa.plant_group, dtype=object)
    st_members = np.asarray([str(pg[g]) == KLASS for g in gen_idx])
    st_groups = np.unique(np.asarray(group_col)[st_members])
    ru_agg = float(np.asarray(ru)[st_groups].sum())
    rd_agg = float(np.asarray(rd)[st_groups].sum())

    mw = model_hourly(year, KLASS)
    d = np.diff(mw)
    up_hits = int((d >= G2_CLIP_FRAC * ru_agg).sum())
    dn_hits = int((-d >= G2_CLIP_FRAC * rd_agg).sum())
    f_up = up_hits / d.size
    f_dn = dn_hits / d.size
    return {
        "year": year,
        "n_ramp_groups_total": int(np.asarray(ru).size),
        "n_groups_with_ST_GAS": int(st_groups.size),
        "ramp_up_agg_mw": ru_agg,
        "ramp_dn_agg_mw": rd_agg,
        "class_pmax_mw": float(np.asarray(fa.pmax)[[g for g in gen_idx]][st_members].sum()),
        "max_abs_delta_mw": float(np.abs(d).max()),
        "share_hours_up_at_envelope": f_up,
        "share_hours_dn_at_envelope": f_dn,
        "implicated": bool(max(f_up, f_dn) >= G2_IMPLICATE_BAR),
    }


def gate3() -> dict:
    """G3 — REPORT: the armed rows that put ST_GAS's P column outside the balance."""
    sc = json.load(open(KEEPER / "run_config.json"))["scenario_config"]
    watched = [
        "ramp_limits",
        "nyiso_nyc_lcr_tsl",
        "nyiso_li_lcr_tsl",
        "nyiso_seam_deliverability_envelope",
        "nyiso_local_selfsupply",
        "nyiso_zonal_loss_surface",
        "reliability_floor",
        "nyiso_gas_commitment_bridge",
        "dual_fuel_switching",
        "dual_fuel_oil_reattribution",
        "ordc_multistep_floor",
    ]
    return {k: sc.get(k) for k in watched}


def main() -> None:
    res = {"gates": {}, "prereg": "PREREG-nyiso180-st-gas-undispatch.md"}
    g1, g2 = [], []
    for y in YEARS:
        # nyiso-182 pinned this call to the LEGACY (defective) offer: build_year's
        # DEFAULT is now the REPAIRED offer (nyiso-181 §11 item 2 — the omitted RGGI
        # allowance price and apply_gas_offer_margin), and this probe's committed
        # record was produced on the legacy one. Re-running it must reproduce that
        # record, not silently restate it on a different basis. A successor that
        # WANTS the repaired basis should drop the flag deliberately and say so.
        st = build_year(y, _cfg_obj(), legacy_defective_offer=True)
        g1.append(gate1(st, y))
        g2.append(gate2(y))
    res["gates"]["G1"] = g1
    res["gates"]["G2"] = g2
    res["gates"]["G3_armed_rows"] = gate3()

    bad = [r for r in g1 if not r["reproduces_nyiso179"]]
    if bad:
        res["G1_verdict"] = "INSTRUMENT FAILURE"
    elif all(r["clears_floor_hi"] for r in g1):
        res["G1_verdict"] = "ARTIFACT"
    else:
        res["G1_verdict"] = "SURVIVES"
    res["G2_verdict"] = (
        "RAMP-IMPLICATED"
        if any(r.get("implicated") for r in g2)
        else "INCONCLUSIVE - PENDING SIDECAR (NOT an exoneration)"
    )
    OUT.write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
