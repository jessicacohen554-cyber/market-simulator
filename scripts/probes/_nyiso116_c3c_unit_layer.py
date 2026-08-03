"""Score the nyiso-116 pre-registered gates and predictions, into one gate JSON.

``PREREG-nyiso116-c3c-unit-layer-2026-08-03.md`` registers five construction
gates (G1 replay fidelity, G2 C3c-tail fidelity, G3 sidecar well-formedness,
G4 the §6 re-verification, G5 span) and five predictions (P1-P5), plus three
NO-LP results measured up front in its §0. This script measures all of them
from committed/produced bundle artifacts and writes
``results/calibration/_nyiso116_c3c_unit_layer_gates.json``, which is the ONLY
place ``gen_nyiso116_attestation.py`` and the FINDING may read numbers from —
nothing is typed in twice (the nyiso-114 discipline).

Read-only: no LP is solved, no config touched, nothing written into any bundle.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso116_c3c_unit_layer.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
CAL = REPO / "results/calibration"
KEEPER = CAL / "nyiso113_lilocational_B"
RECIPE = CAL / "nyiso114_lilocational_confirm"
ARM = CAL / "nyiso116_c3c_unitlayer"
OUT = CAL / "_nyiso116_c3c_unit_layer_gates.json"

YEARS = (2023, 2024, 2025)
THR = 300.0  # TAIL_THRESHOLD["NYISO"] (calibration_verdict.py)
TAIL_LO, TAIL_HI, TAIL_SMALL = 0.5, 2.0, 10  # calibration_verdict.py:337-338
ACTUAL_TAIL = {2023: 10, 2024: 12, 2025: 42}  # frontend/.../actual_tail.json (RT)
PIN_HOURS_2024 = (4528, 4529, 4530)
LI = "Long_Island"

# MW tolerance for every "is this cell at its bound?" test.
#
# POST-HOC CORRECTION, disclosed (nyiso-116 §5): this was first written as 1e-6
# and BOTH G3 and P4 failed on it. The failures were the gate's, not the
# instrument's — ``_unit_hourly_frame`` stores ``mw`` and ``cap_mw`` as
# **float32**, whose spacing is 7.6e-06 MW at 113 MW and 6.1e-05 MW at 838 MW,
# so a 1e-6 absolute tolerance is 8-60x BELOW the representable precision and no
# float32 column can ever satisfy it. Measured consequences of the bad
# tolerance: 131,038 cells (2.0 %) read as "dispatch exceeds cap" with a MAXIMUM
# excess of 1e-04 MW (1.2e-07 relative), and 15 units read as "part-loaded" of
# which 14 sat exactly at their cap. 1e-3 MW = 1 kW is a physically meaningful
# floor and ~130x above float32 spacing at fleet scale. The gate was changed
# AFTER seeing the result; both readings are reported in the finding.
TOL_MW = 1e-3

# Region -> member model zones, from config/reserve_config.py
# (NYISO_RCPF_LOCATIONAL + NYISO_RCPF_LOCATIONAL_LI). ``ALL`` = the NYCA tier.
FAM_ZONES: dict[str, object] = {
    "east_10min_total": ("Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"),
    "seny_30min_total": ("Lower_Hudson", "NYC", "Long_Island"),
    "nyc_30min_total": ("NYC",),
    "nyc_10min_total": ("NYC",),
    "li_30min_total": ("Long_Island",),
    "li_10min_total": ("Long_Island",),
    "nyca_30min_total": "ALL",
    "nyca_10min_total": "ALL",
    "nyca_10min_spin": "ALL",
}


def _sys(bundle: Path, year: int) -> "pd.DataFrame | None":
    f = bundle / "hourly" / f"system_{year}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    return d[d["pass"] == "P1"]


def _price_pivot(bundle: Path, year: int) -> "pd.DataFrame | None":
    d = _sys(bundle, year)
    return None if d is None else d.pivot_table(
        index="hour", columns="zone", values="price"
    )


def _fam_duals(bundle: Path, year: int) -> "pd.DataFrame | None":
    f = bundle / "hourly" / f"reserve_family_{year}.parquet"
    if not f.exists():
        return None
    d = pd.read_parquet(f)
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="family", values="dual")


def _zone_adder(piv: pd.DataFrame, dual: pd.DataFrame) -> pd.DataFrame:
    """Per-zone locational reserve adder = sum of duals of containing regions."""
    zones = list(piv.columns)
    add = pd.DataFrame(0.0, index=piv.index, columns=zones)
    pos = dual.clip(lower=0)
    for fam in pos.columns:
        scope = FAM_ZONES.get(fam)
        tgt = zones if scope == "ALL" else [z for z in (scope or ()) if z in zones]
        for z in tgt:
            add[z] = add[z] + pos[fam]
    return add


def _c3c_verdict(model: int, actual: int) -> dict:
    """Reproduce calibration_verdict._c3c banding for one year."""
    if actual < TAIL_SMALL:
        return {
            "basis": "small-count",
            "pass": bool(abs(model - actual) <= TAIL_SMALL),
            "ratio": None,
        }
    ratio = model / actual if actual else float("inf")
    return {
        "basis": "ratio",
        "pass": bool(TAIL_LO <= ratio <= TAIL_HI),
        "ratio": round(ratio, 4),
        "hours_needed_to_pass": int(np.ceil(TAIL_LO * actual)),
    }


def section0_no_lp() -> dict:
    """The three §0 results, measured on COMMITTED artifacts only."""
    settlement, knife = {}, {}
    for y in YEARS:
        piv, dual = _price_pivot(RECIPE, y), _fam_duals(RECIPE, y)
        add = _zone_adder(piv, dual)
        energy_max = piv.max(axis=1)
        settle_max = (piv + add).max(axis=1)
        binding = (dual.clip(lower=0) > 0).any(axis=1)
        settlement[str(y)] = {
            "c3c_energy_only": int((energy_max > THR).sum()),
            "c3c_settlement": int((settle_max > THR).sum()),
            "max_zone_adder": round(float(add.max().max()), 4),
            "hours_any_family_binding": int(binding.sum()),
            "binding_hours_with_energy_gt_250": int(
                (binding & (energy_max > 250.0)).sum()
            ),
            "adder_in_hours_below_threshold_max": round(
                float(add[energy_max <= THR].max().max()), 4
            ),
            # The inertness PROOF, not just the observation: the highest
            # settlement price attainable in any hour the energy-only series
            # leaves below the gate. If this is < THR the overlay cannot move
            # the count, with the stated margin, rather than happening not to.
            "max_settlement_among_subthreshold_hours": round(
                float(settle_max[energy_max <= THR].max()), 4
            ),
            "inertness_margin_usd": round(
                float(THR - settle_max[energy_max <= THR].max()), 4
            ),
        }
        # Knife-edge: measured on the KEEPER's own committed prices.
        kmax = _price_pivot(KEEPER, y).max(axis=1)
        need = _c3c_verdict(int((kmax > THR).sum()), ACTUAL_TAIL[y])
        n_needed = need.get("hours_needed_to_pass")
        # Take enough hours to reach the one the gate actually turns on.
        top = kmax.nlargest(max(8, (n_needed or 8) + 1))
        nth = float(top.values[n_needed - 1]) if n_needed else None
        knife[str(y)] = {
            "c3c_model": int((kmax > THR).sum()),
            "c3c_actual_rt": ACTUAL_TAIL[y],
            "verdict": need,
            "top8_max_zonal": [round(float(v), 4) for v in top.values[:8]],
            "nth_hour_that_must_clear": n_needed,
            "nth_hour_value": None if nth is None else round(nth, 4),
            "nth_hour_shortfall_usd": None if nth is None else round(THR - nth, 4),
            "nth_hour_shortfall_pct": (
                None if nth is None else round(100.0 * (THR - nth) / nth, 2)
            ),
        }
    # Tail fidelity of the recipe vs the keeper (licenses using a recipe bundle).
    fidelity = {}
    for y in YEARS:
        a, b = _price_pivot(KEEPER, y), _price_pivot(RECIPE, y)
        ma, mb = a.max(axis=1), b.max(axis=1)
        top = ma.nlargest(20).index
        fidelity[str(y)] = {
            "all_zone_hours_max_abs_dprice": round(float((a - b).abs().max().max()), 4),
            "top20_tail_max_abs_dprice": round(float((ma[top] - mb[top]).abs().max()), 6),
            "c3c_keeper": int((ma > THR).sum()),
            "c3c_recipe": int((mb > THR).sum()),
        }
    return {
        "settlement_basis_inert": settlement,
        "knife_edge_reframing": knife,
        "recipe_tail_fidelity": fidelity,
        "tail_hour_coincidence": tail_hour_coincidence(),
    }


def tail_hour_coincidence() -> dict:
    """Are the model's tail hours reality's tail hours? (the caiso-144 check)

    C3c counts hours, so a model can score the gate while pricing scarcity in
    entirely the wrong hours. This measures the OVERLAP between the two tail
    sets, and what the model was doing during the actual's tail — which is the
    difference between closing a gate and inventing a mis-timed tail.
    """
    from market_sim.config.paths import CALIBRATION_DIR

    a = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet")
    out = {}
    for y in YEARS:
        rt = a[a["year"] == y].sort_values("hour").set_index("hour")["rt"]
        mx = _price_pivot(KEEPER, y).max(axis=1)
        idx = sorted(set(rt.index) & set(mx.index))
        rt, mx = rt.loc[idx], mx.loc[idx]
        ah = set(rt[rt > THR].index)
        mh = set(mx[mx > THR].index)
        in_actual_tail = mx[sorted(ah)] if ah else mx.iloc[:0]
        out[str(y)] = {
            "actual_tail_hours": len(ah),
            "model_tail_hours": len(mh),
            "overlap_hours": len(ah & mh),
            "model_only_hours": len(mh - ah),
            "model_price_during_actual_tail": {
                "min": round(float(in_actual_tail.min()), 2) if len(in_actual_tail) else None,
                "median": round(float(in_actual_tail.median()), 2) if len(in_actual_tail) else None,
                "max": round(float(in_actual_tail.max()), 2) if len(in_actual_tail) else None,
            },
            "percentiles": {
                p: {
                    "model": round(float(mx.quantile(q)), 2),
                    "actual": round(float(rt.quantile(q)), 2),
                }
                for p, q in (("p50", 0.5), ("p95", 0.95), ("p99", 0.99), ("p999", 0.999))
            },
            "max": {"model": round(float(mx.max()), 2), "actual": round(float(rt.max()), 2)},
            # The meaningful timing statistic. "Overlap / actual tail" is
            # degenerate when the model has no tail at all (2024), so the
            # precision measure is: of the model's OWN tail hours, how many
            # were real tail hours? nyiso-85 §7d concluded "not timing"; this
            # is that conclusion restated as a rate.
            "model_tail_precision": (
                None if not mh else round(len(mh & ah) / len(mh), 4)
            ),
            "false_positive_hours": len(mh - ah),
        }
        if y == 2024:
            # Is the celebrated $297.54 pin even a real tail hour? And what was
            # reality doing in the hours the model ranks just below it?
            out[str(y)]["pin_hour_reality_check"] = {
                str(h): {
                    "model": round(float(mx.get(h, float("nan"))), 4),
                    "actual": round(float(rt.get(h, float("nan"))), 2),
                    "actual_is_tail_hour": bool(float(rt.get(h, 0)) > THR),
                }
                for h in (4526, 4527, 4528, 4529, 4530, 4531)
            }
    return out


def gate_g1(arm: Path) -> dict:
    per = {}
    for y in YEARS:
        a, b = _price_pivot(KEEPER, y), _price_pivot(arm, y)
        if b is None:
            continue
        d = (a - b).abs()
        per[str(y)] = {
            "max_abs_dprice": round(float(d.max().max()), 4),
            "differing_zone_hours": int((d > 1e-9).sum().sum()),
            "total_zone_hours": int(d.size),
            "mean_price_pct_delta": round(
                float(100.0 * (b.values.mean() - a.values.mean()) / a.values.mean()), 6
            ),
        }
    reproduces = all(v["max_abs_dprice"] <= 1e-9 for v in per.values())
    return {"per_year": per, "reproduces_keeper": bool(reproduces),
            "status": "PASS" if reproduces else "FAIL"}


def gate_g2(arm: Path) -> dict:
    per, ok = {}, True
    for y in YEARS:
        a, b = _price_pivot(KEEPER, y), _price_pivot(arm, y)
        if b is None:
            continue
        ma, mb = a.max(axis=1), b.max(axis=1)
        top = ma.nlargest(8).index
        dtop = float((ma[top] - mb[top]).abs().max())
        ca, cb = int((ma > THR).sum()), int((mb > THR).sum())
        good = (ca == cb) and (dtop <= 5.0)
        ok &= good
        per[str(y)] = {
            "c3c_keeper": ca, "c3c_arm": cb,
            "top8_max_abs_dprice": round(dtop, 6), "pass": bool(good),
        }
    return {"per_year": per, "status": "PASS" if ok else "FAIL"}


def gate_g3(arm: Path) -> dict:
    per, ok = {}, True
    for y in YEARS:
        u = arm / "hourly" / f"unit_hourly_{y}.parquet"
        n = arm / "hourly" / f"network_{y}.parquet"
        rec = {"unit_hourly_present": u.exists(), "network_present": n.exists()}
        if u.exists():
            d = pd.read_parquet(u)
            d = d[d["pass"] == "P1"]
            rec |= {
                "unit_rows": int(len(d)),
                "n_units": int(d["unit_id"].nunique()),
                "unit_nan": int(d[["mw", "cap_mw"]].isna().sum().sum()),
                "mw_exceeds_cap_cells": int((d["mw"] > d["cap_mw"] + TOL_MW).sum()),
                "unit_bytes": u.stat().st_size,
            }
        if n.exists():
            d = pd.read_parquet(n)
            d = d[d["pass"] == "P1"]
            rec |= {
                "network_rows": int(len(d)),
                "n_links": int(d[d["kind"] == "link"]["name"].nunique()),
                "network_nan": int(d[["mw", "dual"]].isna().sum().sum()),
                "network_bytes": n.stat().st_size,
            }
        good = (
            rec.get("unit_hourly_present")
            and rec.get("network_present")
            and rec.get("unit_nan", 1) == 0
            and rec.get("mw_exceeds_cap_cells", 1) == 0
            and rec.get("n_units", 0) > 0
        )
        ok &= bool(good)
        rec["pass"] = bool(good)
        per[str(y)] = rec
    return {"per_year": per, "status": "PASS" if ok else "FAIL"}


def gate_g4(arm: Path) -> dict:
    """Re-verify nyiso-114 §6's four claims on 2024 h4528-4530."""
    y = 2024
    out: dict = {"hours": list(PIN_HOURS_2024)}

    # (i) transmission — both LI import paths at their limits
    nf = pd.read_parquet(arm / "hourly" / f"network_{y}.parquet")
    nf = nf[(nf["pass"] == "P1") & (nf["kind"] == "link")]
    legs = {}
    for nm in (f"NYC>{LI}", f"NYISO_external>{LI}"):
        sub = nf[nf["name"] == nm].set_index("hour")
        if sub.empty:
            legs[nm] = {"present": False}
            continue
        rows = sub.loc[list(PIN_HOURS_2024)]
        legs[nm] = {
            "present": True,
            "mw": [round(float(v), 4) for v in rows["mw"]],
            "limit_up": [round(float(v), 4) for v in rows["limit_up"]],
            "at_limit_all_hours": bool(
                np.all(rows["mw"].values >= rows["limit_up"].values - 1e-3)
            ),
        }
    out["claim_i_transmission"] = {
        "legs": legs,
        "verdict": (
            "CONFIRMED"
            if all(v.get("at_limit_all_hours") for v in legs.values())
            else "REFUTED"
        ),
    }

    # (ii) energy-side — no LI reserve family binds, system reserve_price 0
    dual = _fam_duals(arm, y)
    li_fams = [f for f in ("li_10min_total", "li_30min_total") if f in dual.columns]
    li_bind = int((dual[li_fams].clip(lower=0) > 0).any(axis=1).sum())
    sysd = _sys(arm, y)
    rp = sysd[sysd["hour"].isin(PIN_HOURS_2024)]["reserve_price"]
    li_hours = sorted(
        int(h) for h in dual.index[(dual[li_fams].clip(lower=0) > 0).any(axis=1)]
    )
    out["claim_ii_energy_side"] = {
        # The §6 claim is about THE PIN: is it energy-side or reserve-side?
        "reserve_price_at_pin_max": round(float(rp.abs().max()), 6),
        "li_family_binding_at_pin_hours": int(
            (dual.loc[list(PIN_HOURS_2024), li_fams].clip(lower=0) > 0).any(axis=1).sum()
        ),
        "verdict": "CONFIRMED" if float(rp.abs().max()) < 1e-9 else "REFUTED",
        # Reported separately: nyiso-114 §3 P4 asserted ZERO LI-family binding
        # hours in all of 2024. That is a YEAR-level claim, not a pin claim, and
        # it is re-measured here on a different HEAD (see G1).
        "year_level_note": {
            "li_family_binding_hours_year": li_bind,
            "hours": li_hours,
            "nyiso114_recipe_reported": 0,
            "agrees_with_nyiso114": li_bind == 0,
        },
    }

    # (iii)/(iv) marginal unit + idle capacity on Long Island at the pin
    uf = pd.read_parquet(arm / "hourly" / f"unit_hourly_{y}.parquet")
    uf = uf[(uf["pass"] == "P1") & (uf["zone"] == LI)]
    h0 = PIN_HOURS_2024[0]
    at = uf[uf["hour"] == h0].copy()
    at["headroom"] = at["cap_mw"] - at["mw"]
    partial = at[(at["mw"] > TOL_MW) & (at["headroom"] > TOL_MW)]
    running = at[at["mw"] > TOL_MW]
    fully_idle = at[at["mw"] <= TOL_MW]
    piv = _price_pivot(arm, y)
    out["claim_iii_marginal_unit"] = {
        "li_tranches": int(len(at)),
        "li_running": int(len(running)),
        "n_part_loaded": int(len(partial)),
        "part_loaded": [
            {
                "unit_id": str(r.unit_id), "fuel": str(r.fuel),
                "plant_group": str(r.plant_group),
                "mw": round(float(r.mw), 4), "cap_mw": round(float(r.cap_mw), 4),
            }
            for r in partial.itertuples()
        ],
        "li_price_at_pin": round(float(piv.loc[h0, LI]), 6),
        "verdict": (
            "CONFIRMED"
            if len(partial) == 1 and str(partial.iloc[0]["fuel"]).upper().find("OIL") >= 0
            else "REFUTED"
        ),
    }
    out["claim_iv_idle_capacity"] = {
        "fully_idle_mw": round(float(fully_idle["cap_mw"].sum()), 4),
        "fully_idle_tranches": int(len(fully_idle)),
        "total_headroom_mw": round(float(at["headroom"].sum()), 4),
        "claimed_mw": 596.9,
        "verdict": (
            "CONFIRMED"
            if abs(float(fully_idle["cap_mw"].sum()) - 596.9) <= 5.0
            else "REFUTED"
        ),
    }
    return out


def gate_g5(arm: Path) -> dict:
    meta = json.loads((arm / "meta.json").read_text())
    ys = sorted(int(y) for y in meta.get("years", []))
    ok = ys == list(YEARS)
    return {"years": ys, "status": "PASS" if ok else "FAIL",
            "no_year_outside_training": bool(set(ys) <= set(YEARS))}


def main() -> None:
    arm = ARM
    res: dict = {
        "session": "nyiso-116",
        "prereg": "PREREG-nyiso116-c3c-unit-layer-2026-08-03.md",
        "keeper": "2026-08-02-nyiso-113-li-locational",
        "keeper_bundle": KEEPER.name,
        "arm_bundle": arm.name,
        "threshold_usd": THR,
        "section0_no_lp": section0_no_lp(),
    }
    if (arm / "meta.json").exists():
        res["G1_replay_fidelity"] = gate_g1(arm)
        res["G2_c3c_tail_fidelity"] = gate_g2(arm)
        res["G3_sidecars"] = gate_g3(arm)
        res["G5_span"] = gate_g5(arm)
        # K-A: G4 may only be measured if G2 passes.
        if res["G2_c3c_tail_fidelity"]["status"] == "PASS":
            res["G4_section6_reverification"] = gate_g4(arm)
        else:
            res["G4_section6_reverification"] = {
                "skipped": "K-A fired: G2 failed, no unit-level attribution claimed"
            }
        g4 = res["G4_section6_reverification"]
        res["predictions"] = {
            "P1_g1_fails": res["G1_replay_fidelity"]["status"] == "FAIL",
            "P2_g2_passes": res["G2_c3c_tail_fidelity"]["status"] == "PASS",
            "P3_transmission": g4.get("claim_i_transmission", {}).get("verdict"),
            "P4_marginal_unit": g4.get("claim_iii_marginal_unit", {}).get("verdict"),
            "P5_idle_capacity": g4.get("claim_iv_idle_capacity", {}).get("verdict"),
        }
    OUT.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n")
    print(json.dumps(res, indent=2, sort_keys=True))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
