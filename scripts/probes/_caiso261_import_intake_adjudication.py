"""caiso-261 (ZERO LP): the hod 22-23 import DATA-INTAKE adjudication.

Registered in
``results/calibration/PRECOMMIT-caiso261-import-intake-adjudication-2026-09-06.md``
(pushed before this instrument was run). The object is the ~1.8 GW of net
import the market moved at hod 22-23 in 2025 at hub parity that no armed WECC
rung offers at the node dual (caiso-258 §5). The caiso-258 queue asked for a
measured, forward-regenerating source for contracted / self-scheduled import
VOLUME beyond what the firm block already carries, with rule-13 admissibility
adjudicated BEFORE any wiring. This probe scores that hypothesis (H-INTAKE)
on committed artifacts and the published DMM record, and it has no branch
that reaches a solve.

Legs, in the PRECOMMIT's order:

* **G-REPRO (P-1 / P-1b)** - the caiso-258 closure re-run on the caiso-260
  keeper (``_caiso258_hod2223_closure.py --import-stack --session caiso-261``,
  read from its json): the 22-23 import deficit and the CC_REGULAR error.
* **E-1 (P-2)** - the self-scheduled hypothesis: the keeper's summed firm
  ``min_gen`` at 22-23 by month (D-3 rebuild) against the measured
  price-insensitive intertie CEILING (caiso-151, ``PUB_DAM_GRP``). If the clip
  binds, no self-scheduled / <= $0 intertie volume remains un-carried.
* **E-2 (P-3 / P-4)** - the showing hypothesis: DMM 2025 §17 Figure 17.3
  final shown-RA imports on the PWT tie points (Jun-Sep, transcribed in the
  PRECOMMIT, +/-100 MW) against the ceiling and the keeper's summer floor;
  the historic non-RA component of the ISO's estimate.
* **E-3 (P-5)** - attribution of the residual (class C, DIAGNOSTIC ONLY,
  never wired): the dynamic WEIM net transfer into the CAISO BA at 22-24
  (DMM Figure 4.2 chart read) against the deficit.
* **E-4 (P-6 / P-7)** - exposures on the caiso-260 bundle: the 22-23 share of
  the 2025 gas MSE (from the closure json's D-4) and how many of the keeper's
  2023 model hours > $200 sit at hod 22-23 (sidecar load-weighted price).

Every number the FINDING cites is written to
``results/calibration/_caiso261_import_intake_adjudication.json``. Nothing
here is an input to anything.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso261_import_intake_adjudication.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER = "2026-09-06-caiso-260-b1-demand"
BUNDLE = REPO / "results/calibration/caiso260_demand_vintage"
CLOSURE = REPO / "results/calibration/_caiso261_closure_on_caiso260.json"
CEILING = REPO / "data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv"
HOLDINGS = REPO / "results/calibration/_caiso245_allocation_split.json"
OUT = REPO / "results/calibration/_caiso261_import_intake_adjudication.json"
YEARS = (2023, 2024, 2025)
GAP = (22, 23)
T = 8760
HOD = np.arange(T) % 24
MOH = np.repeat(
    np.arange(1, 13), np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
)

# --- transcribed operands (PRECOMMIT-caiso261 §3; DMM 2025 Annual Report,
# sha256 7c89fdc4...15ea9). Chart reads, +/-100 MW, cross-checked against the
# report's own text (over-estimates 1,500 / 900 / 1,600 / 2,100 MW =
# 42 / 22 / 39 / 52 %). They score NO prediction on their own; they are
# operands for P-3 / P-4 / P-5.
DMM_S1_FINAL_SHOWN_RA_MW = {6: 3600.0, 7: 4300.0, 8: 4050.0, 9: 4150.0}
DMM_S1_ESTIMATE_MW = {6: 5100.0, 7: 5200.0, 8: 5600.0, 9: 6300.0}
DMM_S1_HISTORIC_NON_RA_MW = {6: 250.0, 7: 50.0, 8: 600.0, 9: 300.0}
DMM_S1_TEXT_OVERESTIMATE_MW = {6: 1500.0, 7: 900.0, 8: 1600.0, 9: 2100.0}
DMM_S1_TEXT_OVERESTIMATE_PCT = {6: 42.0, 7: 22.0, 8: 39.0, 9: 52.0}
DMM_S1_MALIN_FINAL_MW = {7: 1050.0, 8: 980.0, 9: 1010.0}
DMM_S1_NOB_FINAL_MW = {6: 900.0, 7: 980.0, 8: 900.0, 9: 820.0}
# Figure 4.2, "California ISO" bar, hours 22-24, net IMPORT into the BA
# (dynamic WEIM transfers only - footnote 148 excludes base schedules).
DMM_S5_WEIM_DYNAMIC_2224_MW = {"Q1": 800.0, "Q2": 700.0, "Q3": 900.0, "Q4": 800.0}
DMM_S5_READ_TOL_MW = 150.0
DMM_S1_READ_TOL_MW = 100.0

# --- registered tolerances / bands (PRECOMMIT §4)
P1_TOL_MW = 300.0
P1_PUB_DEFICIT = {2023: -972.0, 2024: -1467.0, 2025: -1763.0}  # caiso-258 §1
P1B_PUB_CC_2025 = {22: 1536.0, 23: 1546.0}  # caiso-258 §1
P2_BIND_MW = 150.0
P2_FALSIFY_MW = 500.0
P3_TOL_MW = 600.0
P4_MAX_NON_RA_MW = 700.0
P5_LO_MW, P5_HI_MW = 400.0, 1200.0
P5_RESIDUAL_MIN_MW = 600.0
P6_LO, P6_HI = 0.08, 0.11
P7_MAX_HOURS = 3
TAIL_THRESHOLD = 200.0  # calibration_verdict.TAIL_THRESHOLD["CAISO"]
C3C_2023_MODEL_H, C3C_2023_ACTUAL_H = 23, 47  # caiso-260 §4
C4_2025 = {"nrmse": 0.298, "bound": 0.30}


def _ceiling_2223_by_month() -> list[float]:
    f = pd.read_csv(CEILING)
    tab = np.full((12, 24), np.nan)
    tab[f["month"].to_numpy() - 1, f["hod"].to_numpy()] = f["ceiling_mw"].to_numpy(
        float
    )
    assert np.all(np.isfinite(tab)), "incomplete ceiling table"
    return [float(tab[mm, list(GAP)].mean()) for mm in range(12)]


def _lw_price_by_hod_tail(year: int) -> dict:
    """Keeper model hours > TAIL_THRESHOLD in ``year`` on the sidecar's
    load-weighted system price, by hod. Basis note: the scorer counts the
    committed payload's hourly scarcity series; this is the sidecar
    reconstruction of the same quantity and its total is reported beside the
    scored 23 h so the basis can be checked."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s["demand"] > 0]
    g = s.groupby("hour")
    lw = (
        g.apply(lambda d: float((d["price"] * d["demand"]).sum() / d["demand"].sum()))
    ).to_numpy(float)
    hours = np.asarray(sorted(s["hour"].unique()))
    tail = lw > TAIL_THRESHOLD
    hod = hours % 24
    by_hod = {int(h): int(tail[hod == h].sum()) for h in range(24)}
    return {
        "n_tail_hours_lw": int(tail.sum()),
        "scored_model_h": C3C_2023_MODEL_H if year == 2023 else None,
        "by_hod": by_hod,
        "at_2223": int(sum(by_hod[h] for h in GAP)),
        "max_lw_price": float(lw.max()),
    }


def main() -> None:
    cl = json.loads(CLOSURE.read_text())
    assert cl["keeper"] == KEEPER, cl["keeper"]
    res: dict = {
        "session": "caiso-261",
        "keeper": KEEPER,
        "control": "form 4 - the keeper's committed bundle; no control solve",
        "closure_json": str(CLOSURE.relative_to(REPO)),
        "precommit": "PRECOMMIT-caiso261-import-intake-adjudication-2026-09-06.md",
        "transcribed_operands": {
            "S1_final_shown_ra_mw": DMM_S1_FINAL_SHOWN_RA_MW,
            "S1_estimate_mw": DMM_S1_ESTIMATE_MW,
            "S1_historic_non_ra_mw": DMM_S1_HISTORIC_NON_RA_MW,
            "S1_malin_final_mw": DMM_S1_MALIN_FINAL_MW,
            "S1_nob_final_mw": DMM_S1_NOB_FINAL_MW,
            "S1_text_overestimate_mw": DMM_S1_TEXT_OVERESTIMATE_MW,
            "S1_text_overestimate_pct": DMM_S1_TEXT_OVERESTIMATE_PCT,
            "S5_weim_dynamic_2224_mw": DMM_S5_WEIM_DYNAMIC_2224_MW,
            "read_tol_mw": {"S1": DMM_S1_READ_TOL_MW, "S5": DMM_S5_READ_TOL_MW},
            "source": "DMM 2025 Annual Report on Market Issues and Performance "
            "(June 2026), sha256 7c89fdc42ef10968b194a3919dfb8f3ecf3ce52b53ffbe4bb9607e92a9915ea9; "
            "§17 pp. 337-342 (Fig 17.3-17.5), §16.5 p. 321 (Fig 16.9), §4.1 p. 175 (Fig 4.2), "
            "§1 pp. 77-78 (Fig 1.52-1.53)",
        },
        "years": {},
        "predictions": {},
    }

    # ---- S-1 internal consistency: chart read vs the report's own text
    s1_chk = {}
    for mm, est in DMM_S1_ESTIMATE_MW.items():
        fin = DMM_S1_FINAL_SHOWN_RA_MW[mm]
        s1_chk[mm] = {
            "chart_over_mw": est - fin,
            "text_over_mw": DMM_S1_TEXT_OVERESTIMATE_MW[mm],
            "chart_over_pct": round(100.0 * (est - fin) / fin, 1),
            "text_over_pct": DMM_S1_TEXT_OVERESTIMATE_PCT[mm],
            "consistent_within_read_tol": abs(
                (est - fin) - DMM_S1_TEXT_OVERESTIMATE_MW[mm]
            )
            <= 2 * DMM_S1_READ_TOL_MW,
        }
    res["S1_chart_vs_text"] = s1_chk

    ceil_m = _ceiling_2223_by_month()
    res["ceiling_2223_by_month_mw"] = ceil_m

    # ---- per-year legs
    for y in YEARS:
        yc = cl["years"][str(y)]
        d3 = yc["D3_import_stack"]
        floor_m = d3["sum_floor_2223_by_month"]
        cap_m = d3["sum_cap_2223_by_month"]
        imp_m = d3["import_2223_by_month"]
        # firm rows only (the floors live on the two firm tranches; the
        # summed min_gen may carry negative export-sink floors, so isolate the
        # non-negative firm part explicitly)
        firm_floor_m = np.zeros(12)
        firm_names = []
        for uid, r in d3["rows"].items():
            fm = np.asarray(r["floor_2223_by_month"], float)
            if np.any(fm > 0):
                firm_floor_m += np.clip(fm, 0.0, None)
                firm_names.append(uid)
        gap_by_hod = np.asarray(yc["import_gap_by_hod_mw"], float)
        deficit_2223 = float(gap_by_hod[list(GAP)].mean())
        e1 = {
            "firm_rows": firm_names,
            "firm_floor_2223_by_month_mw": firm_floor_m.tolist(),
            "ceiling_minus_firm_floor_by_month_mw": (
                np.asarray(ceil_m) - firm_floor_m
            ).tolist(),
            "ceiling_minus_firm_floor_mean_mw": float(
                (np.asarray(ceil_m) - firm_floor_m).mean()
            ),
            "ceiling_minus_firm_floor_max_mw": float(
                (np.asarray(ceil_m) - firm_floor_m).max()
            ),
            "sum_all_floor_2223_by_month_mw": floor_m,
            "sum_cap_2223_by_month_mw": cap_m,
            "committed_import_2223_by_month_mw": imp_m,
        }
        res["years"][str(y)] = {
            "import_deficit_2223_mw": deficit_2223,
            "import_deficit_by_hod_mw": gap_by_hod.tolist(),
            "cc_err_by_hod_mw": yc["cc_err_by_hod_mw"],
            "committed_import_2223_mean_mw": d3["committed_import_2223_mean_mw"],
            "sum_cap_2223_mean_mw": d3["sum_cap_2223_mean_mw"],
            "priced_out_headroom_2223_mean_mw": d3["priced_out_headroom_2223_mean_mw"],
            "rebuild_fallback_lines": d3["rebuild_stderr_fallback_lines"],
            "E1": e1,
            "D4_c4_exposure": yc.get("D4_c4_exposure"),
        }

    # ---- P-1 / P-1b
    p1 = {
        str(y): {
            "measured": res["years"][str(y)]["import_deficit_2223_mw"],
            "published_caiso258": P1_PUB_DEFICIT[y],
            "diff": res["years"][str(y)]["import_deficit_2223_mw"] - P1_PUB_DEFICIT[y],
        }
        for y in YEARS
    }
    res["predictions"]["P1"] = {
        "rows": p1,
        "tol_mw": P1_TOL_MW,
        "holds": all(abs(v["diff"]) <= P1_TOL_MW for v in p1.values()),
    }
    cc25 = res["years"]["2025"]["cc_err_by_hod_mw"]
    p1b = {
        str(h): {
            "measured": cc25[h],
            "published": P1B_PUB_CC_2025[h],
            "diff": cc25[h] - P1B_PUB_CC_2025[h],
        }
        for h in GAP
    }
    res["predictions"]["P1b"] = {
        "rows": p1b,
        "tol_mw": P1_TOL_MW,
        "holds": all(abs(v["diff"]) <= P1_TOL_MW for v in p1b.values()),
    }

    # ---- P-2 (E-1)
    p2 = {
        str(y): {
            "ceiling_minus_firm_floor_mean_mw": res["years"][str(y)]["E1"][
                "ceiling_minus_firm_floor_mean_mw"
            ],
            "ceiling_minus_firm_floor_max_mw": res["years"][str(y)]["E1"][
                "ceiling_minus_firm_floor_max_mw"
            ],
        }
        for y in YEARS
    }
    res["predictions"]["P2"] = {
        "rows": p2,
        "bind_mw": P2_BIND_MW,
        "falsify_mw": P2_FALSIFY_MW,
        "holds": all(
            v["ceiling_minus_firm_floor_mean_mw"] <= P2_BIND_MW for v in p2.values()
        ),
        "falsified_alt_object": any(
            v["ceiling_minus_firm_floor_mean_mw"] >= P2_FALSIFY_MW for v in p2.values()
        ),
    }

    # ---- P-3 / P-4 (E-2)
    ff25 = np.asarray(res["years"]["2025"]["E1"]["firm_floor_2223_by_month_mw"])
    p3 = {}
    for mm, fin in DMM_S1_FINAL_SHOWN_RA_MW.items():
        p3[mm] = {
            "final_shown_ra_mw": fin,
            "ceiling_2223_mw": ceil_m[mm - 1],
            "keeper_firm_floor_2223_2025_mw": float(ff25[mm - 1]),
            "final_minus_ceiling_mw": fin - ceil_m[mm - 1],
            "final_minus_floor_mw": fin - float(ff25[mm - 1]),
        }
    res["predictions"]["P3"] = {
        "rows": p3,
        "tol_mw": P3_TOL_MW,
        "holds": all(
            abs(v["final_minus_ceiling_mw"]) <= P3_TOL_MW
            and abs(v["final_minus_floor_mw"]) <= P3_TOL_MW
            for v in p3.values()
        ),
    }
    res["predictions"]["P4"] = {
        "historic_non_ra_mw": DMM_S1_HISTORIC_NON_RA_MW,
        "max_mw": P4_MAX_NON_RA_MW,
        "holds": max(DMM_S1_HISTORIC_NON_RA_MW.values()) <= P4_MAX_NON_RA_MW,
        "appears_in_final": False,
    }

    # ---- P-5 (E-3, diagnostic)
    weim = float(np.mean(list(DMM_S5_WEIM_DYNAMIC_2224_MW.values())))
    deficit25 = -res["years"]["2025"]["import_deficit_2223_mw"]
    res["predictions"]["P5"] = {
        "weim_dynamic_2224_mean_mw": weim,
        "band_mw": [P5_LO_MW, P5_HI_MW],
        "deficit_2025_mw": deficit25,
        "residual_after_weim_mw": deficit25 - weim,
        "residual_min_mw": P5_RESIDUAL_MIN_MW,
        "holds": (P5_LO_MW <= weim <= P5_HI_MW)
        and (deficit25 - weim >= P5_RESIDUAL_MIN_MW),
        "class": "C - realised flow; DIAGNOSTIC ONLY; never wired",
    }

    # ---- P-6 / P-7 (E-4)
    d4 = res["years"]["2025"]["D4_c4_exposure"] or {}
    share = None
    for k in ("share_of_mse_at_2223", "share_of_gas_mse_2223", "share"):
        if k in d4:
            share = float(d4[k])
            break
    res["predictions"]["P6"] = {
        "D4_raw": d4,
        "share_2223_of_2025_gas_mse": share,
        "band": [P6_LO, P6_HI],
        "holds": (share is not None) and (P6_LO <= share <= P6_HI),
        "c4_2025": C4_2025,
    }
    tail23 = _lw_price_by_hod_tail(2023)
    res["predictions"]["P7"] = {
        "tail_2023": tail23,
        "max_hours_at_2223": P7_MAX_HOURS,
        "holds": tail23["at_2223"] <= P7_MAX_HOURS,
        "scored": {"model_h": C3C_2023_MODEL_H, "actual_h": C3C_2023_ACTUAL_H},
    }

    # ---- holdings (S-3), carried
    hold = json.loads(HOLDINGS.read_text())
    res["S3_holdings"] = {
        y: {
            "total_alloc_mw": hold["years"][y]["total_alloc_mw"],
            "dmm_ra_import_mw": hold["years"][y]["dmm_ra_import_mw"],
            "alloc_over_dmm": hold["years"][y]["alloc_over_dmm"],
        }
        for y in hold["years"]
    }

    # ---- stop rule
    P = res["predictions"]
    h_intake_falsified = P["P2"]["holds"] and P["P3"]["holds"] and P["P4"]["holds"]
    res["stop_rule"] = {
        "5.1_H_INTAKE_falsified": h_intake_falsified,
        "5.2_clip_not_binding_alt_object": P["P2"]["falsified_alt_object"],
        "5.3_intake_named": not (P["P3"]["holds"] and P["P4"]["holds"]),
        "solve_reached": False,
    }
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")

    print(f"caiso-261 on {KEEPER}")
    for k, v in P.items():
        print(f"  {k}: holds={v.get('holds')}")
    for y in YEARS:
        r = res["years"][str(y)]
        e = r["E1"]
        print(
            f"  {y}: deficit 22-23 {r['import_deficit_2223_mw']:.0f} MW; "
            f"firm floor mean {np.mean(e['firm_floor_2223_by_month_mw']):.0f}; "
            f"ceiling-floor mean {e['ceiling_minus_firm_floor_mean_mw']:.0f} "
            f"max {e['ceiling_minus_firm_floor_max_mw']:.0f}; "
            f"committed import {r['committed_import_2223_mean_mw']:.0f} of cap {r['sum_cap_2223_mean_mw']:.0f}"
        )
    print("  stop rule:", res["stop_rule"])
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
