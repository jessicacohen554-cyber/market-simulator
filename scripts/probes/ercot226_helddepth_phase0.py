"""ercot-226 Phase-0: kill preconditions + F2 location screen (NO solve).

Computes the PRECOMMIT-ercot226-held-sequestration-2026-08-22 §5.4
pre-registered measurements from committed artifacts only:

* the keeper 2023 miss set — hours with actual RT > $200 whose keeper
  max-zonal model price is ≤ $200 (committed keeper sidecar vs the committed
  hourly RT actual);
* **F1 kill check**: p50 at the miss set of
  ``sum_p max(0, held_p − plan_p)``, p ∈ {REGUP, RRS, ECRS} (rigid
  products); < 100 MW ⇒ F1 REFUTED-P0, no solve, no field built;
* **F1b materiality**: the same for NSPIN/NSRS;
* **F1 feasibility margins** (for the record even when F1 dies):
  ``margin_fast = rtolcap − LR credit − storage credit − Σ_fast req_p``;
* **F2 location screen**: p50 at the miss set of the held MW sitting on the
  dispatch-relevant thermal classes (gas_cc + coal + gas_st, rigid
  products); ≥ 500 MW ⇒ the misallocation hypothesis has mass and the F2
  build proceeds;
* the documentation numbers for the F3/F4/F5 rows (data-absence facts and
  the storage telemetry-vs-award consistency the derive printed).

Writes ``results/calibration/ercot226_helddepth_phase0.json`` (committed —
the W-2 probe-record channel). Report-only: this script gates nothing by
itself; the verdict lines it prints are the precommit's §5.4 rules applied.

Run:
    python scripts/probes/ercot226_helddepth_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results" / "calibration" / "ercot223_release_arm"
ACTUAL = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
RESP = REPO / "data" / "raw" / "ercot-AS" / "ercot_2023_as_responsibility_hourly.parquet"
RESP_CLS = (
    REPO / "data" / "raw" / "ercot-AS"
    / "ercot_2023_as_responsibility_by_class_hourly.parquet"
)
ORDC = REPO / "data" / "raw" / "ercot" / "ercot_2023_ordc_reserves_hourly.parquet"
OUT = REPO / "results" / "calibration" / "ercot226_helddepth_phase0.json"

YEAR = 2023
RIGID = {"REGUP": "regup", "RRS": "rrs", "ECRS": "ecrs"}  # DECISION-2: no rrsffr
THERMAL = ("gas_cc", "coal", "gas_st")
F1_KILL_MW = 100.0
F2_SCREEN_MW = 500.0


def _pct(x: np.ndarray, q: float) -> float:
    return float(np.percentile(x, q))


def main() -> None:
    from market_sim.results.scarcity import ercot_as_plan_requirement_mw

    sy = pd.read_parquet(KEEPER / "hourly" / f"system_{YEAR}.parquet")
    sy = sy[(sy["year"] == YEAR) & (sy["pass"] == "P1")]
    hours = 8760
    stack = np.full((sy["zone"].nunique(), hours), -np.inf)
    for i, (_, zg) in enumerate(sy.groupby("zone", observed=True)):
        stack[i, zg["hour"].to_numpy()] = zg["price"].to_numpy(float)
    model_max = stack.max(axis=0)

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR]
    rt = np.full(hours, np.nan)
    rt[act["hour"].to_numpy(int)] = act["rt"].to_numpy(float)

    tail = np.nan_to_num(rt, nan=-np.inf) > 200.0
    miss = tail & (model_max <= 200.0)
    caught = tail & (model_max > 200.0)
    phantom = (~tail) & (model_max > 200.0) & np.isfinite(rt)
    print(f"[phase0] 2023 actual tail {int(tail.sum())} h: "
          f"caught {int(caught.sum())} / missed {int(miss.sum())} / "
          f"phantom {int(phantom.sum())}")

    resp = pd.read_parquet(RESP)
    plan = {c: np.asarray(ercot_as_plan_requirement_mw(YEAR, hours, c), float)
            for c in list(RIGID) + ["NSPIN"]}
    held = {c: resp[col].to_numpy(float) for c, col in RIGID.items()}
    held["NSPIN"] = resp["nsrs"].to_numpy(float)

    delta_rigid = sum(np.maximum(0.0, held[c] - plan[c]) for c in RIGID)
    delta_nspin = np.maximum(0.0, held["NSPIN"] - plan["NSPIN"])
    f1 = {
        "delta_sum_p50_miss": _pct(delta_rigid[miss], 50),
        "delta_sum_p90_miss": _pct(delta_rigid[miss], 90),
        "delta_sum_max_year": float(delta_rigid.max()),
        "delta_hours_gt0_year": int((delta_rigid > 0).sum()),
        "held_over_plan_ratio_p50_miss": {
            c: float(np.median(held[c][miss] / np.maximum(plan[c][miss], 1e-9)))
            for c in RIGID
        },
    }
    f1["verdict"] = (
        "REFUTED-P0" if f1["delta_sum_p50_miss"] < F1_KILL_MW else "PROCEED"
    )
    f1b = {
        "delta_p50_miss": _pct(delta_nspin[miss], 50),
        "delta_p90_miss": _pct(delta_nspin[miss], 90),
        "delta_max_year": float(delta_nspin.max()),
        "verdict": (
            "REFUTED-P0" if _pct(delta_nspin[miss], 50) < F1_KILL_MW else "PROCEED"
        ),
    }
    print(f"[phase0] F1 delta p50@miss = {f1['delta_sum_p50_miss']:.1f} MW "
          f"(kill < {F1_KILL_MW}) -> {f1['verdict']}")
    print(f"[phase0] F1b delta p50@miss = {f1b['delta_p50_miss']:.1f} MW "
          f"-> {f1b['verdict']}")

    ordc = pd.read_parquet(ORDC)
    cap = np.full(hours, np.nan)
    hh = ordc["hour"].to_numpy(int)
    cap[hh[hh < hours]] = ordc["rtolcap"].to_numpy(float)[hh < hours]
    from market_sim.results.scarcity import (
        ercot_load_resource_reserve_mw,
        ercot_storage_as_reserve_mw,
    )

    lr = np.asarray(ercot_load_resource_reserve_mw(YEAR, hours), float)
    st = np.asarray(ercot_storage_as_reserve_mw(YEAR, hours), float)
    req_f1_fast = sum(np.maximum(plan[c], held[c]) for c in RIGID)
    margin_fast = cap - lr - st - req_f1_fast
    fin = np.isfinite(margin_fast)
    feas = {
        "margin_fast_min": float(np.nanmin(margin_fast)),
        "margin_fast_neg_hours": int((margin_fast[fin] < 0).sum()),
        "margin_fast_p5": _pct(margin_fast[fin], 5),
    }
    print(f"[phase0] F1 feasibility: margin_fast min {feas['margin_fast_min']:.0f} MW, "
          f"negative hours {feas['margin_fast_neg_hours']}")

    cls = pd.read_parquet(RESP_CLS)
    th = sum(
        cls[f"{c}_{col}"].to_numpy(float)
        for c in THERMAL
        for col in RIGID.values()
    )
    by_cls_miss = {
        c: float(np.median(sum(cls[f"{c}_{col}"].to_numpy(float)
                               for col in RIGID.values())[miss]))
        for c in THERMAL + ("storage",)
    }
    f2 = {
        "thermal_held_p50_miss": _pct(th[miss], 50),
        "thermal_held_p90_miss": _pct(th[miss], 90),
        "thermal_held_p50_year": _pct(th, 50),
        "by_class_p50_miss": by_cls_miss,
        "verdict": (
            "PROCEED-BUILD" if _pct(th[miss], 50) >= F2_SCREEN_MW else "REFUTED-P0"
        ),
    }
    print(f"[phase0] F2 thermal held p50@miss = {f2['thermal_held_p50_miss']:.0f} MW "
          f"(screen >= {F2_SCREEN_MW}) -> {f2['verdict']}; "
          f"by class @miss: " + ", ".join(f"{k}={v:.0f}" for k, v in by_cls_miss.items()))

    out = {
        "probe": "ercot226_helddepth_phase0",
        "charter": "PRECOMMIT-ercot226-held-sequestration-2026-08-22 §5.4",
        "keeper": "2026-08-20-ercot223-arm-eventrelease",
        "year": YEAR,
        "miss_set": {
            "actual_tail_h": int(tail.sum()),
            "caught": int(caught.sum()),
            "missed": int(miss.sum()),
            "phantom": int(phantom.sum()),
        },
        "F1": f1,
        "F1b": f1b,
        "F1_feasibility": feas,
        "F2": f2,
        "F3": {
            "verdict": "REFUTED-P0",
            "basis": "no committed 2023 RUC-MW series (data/raw/ercot has RUC "
            "AS disclosure for 2025/2026 only); predicted sign ~0/negative "
            "(RUC adds supply; model already matches physical dispatch ±8%); "
            "RUC price side owned by ercot_rtordpa_overlay (K) — rule 19",
        },
        "F4": {
            "verdict": "REFUTED-P0",
            "basis": "no measured DA-load-forecast series in the repo; demand "
            "is measured actual and must remain; procurement-sizing entry "
            "double-counts the armed ASPLANNP433 plan (rule 19); ORDC entry "
            "channel-forbidden (precommit §1)",
        },
        "F5": {
            "verdict": "ALREADY-CARRIED",
            "basis": "armed representation is maximal (ECRS_withheld single "
            "VOLL step full width; RRS/RegUp rigid through RTC+B; OBDRR048 "
            "floor date-gated); storage AS measured-credited "
            "(telemetered vs DAM award means: regup 205/269, rrs 882/844, "
            "ecrs 127/120, nonspin 16/15 MW — derive validation (c)); "
            "online-NSPIN depth measured under F1b",
        },
        "notes": [
            "held basis is Gen-resource ONLINE\\ONTEST telemetered "
            "responsibilities — Load Resources and offline NSPIN are outside "
            "the corpus, so held < plan is expected by construction wherever "
            "LR/offline provision is material (the F1 kill's meaning: the "
            "conservatism depth is not in the system-level GEN quantity)",
            "rrsffr telemetered column is ~identically 0 in this corpus "
            "(battery FFR responsibility reports under the RRS column), so "
            "DECISION-2's exclusion is inert in practice",
        ],
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(f"[phase0] wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
