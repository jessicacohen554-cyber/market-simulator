#!/usr/bin/env python3
"""ercot-189: how much of C3a-2023 is the accepted C3c object — a READ, no solve.

Reads ONLY committed artifacts of the ERCOT keeper `2026-08-11-run188-arm-topfine-cliff`
(bundle resolved from the registry sidecar) plus the committed actuals:

  * ``<bundle>/hourly/system_2023.parquet``       — zonal hourly LP dual + demand (P1)
  * ``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet``  — hub RT (H_tail source)
  * ``data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet``   — per-LZ RT (rt_lw source)
  * the run's payload/bench/attestation via ``calibration_verdict.load_artifacts``

and re-scores COUNTERFACTUAL price series in the gate's own units by rebuilding the
payload ``lmp`` aggregates exactly as the committed payload builder does
(``scripts/render_calibration_html.py:2107-2155``: per-zone demand-weighted ``p``/``pMon``
rounded 2dp, ``d``/``dMon`` in TWh rounded 4dp, unweighted-mean fallback for zero-demand
zones, month edges = non-leap cumulative hours) and calling the rubric's own
``score_price_mean`` / ``score_price_shape`` / ``score_price_tail`` /
``determine_from_artifacts``.  H_tail is the committed C3c definition: the 181 hours
where the actual hub RT series > $200 strict (``derive_actual_tail.py`` / ``rt_gt``).

No solve, no replay, no model input touched; actuals are substituted only inside
counterfactual SCORING (rule 13 clean).  The baseline gate must reproduce the committed
payload dict-for-dict and the keeper's scored C3a/C3b/C3c/determination before any
counterfactual row is emitted; a full-substitution seam gate (CF-0) bounds the
reconciliation error of the crosswalk frame against the bench ``rt_lw`` actual.

Output: ``results/calibration/ercot189_c3a_c3c_overlap.json`` — every figure quoted by
``docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md``.
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts import calibration_verdict as cv  # noqa: E402  (stdlib-only module)

RUN_ID_DEFAULT = "2026-08-11-run188-arm-topfine-cliff"
JSON_DEFAULT = REPO / "results" / "calibration" / "ercot189_c3a_c3c_overlap.json"
YEAR = 2023
THRESHOLD = 200.0  # TAIL_THRESHOLD["ERCOT"], calibration_verdict.py:451
HOURS = 8760
# Non-leap month-hour edges — identical to render_calibration_html._CUM (line 235).
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum([0] + list(_DAYS)) * 24
AUG_SEP = (int(_CUM[7]), int(_CUM[9]))  # [5088, 6552) — calendar Aug+Sep hour span

# Replicated from scripts/data/derive_actual_lmp.py:929-937 (the module imports
# numpy/openpyxl/market_sim at module level, so it is AST-guarded, never imported).
CROSSWALK: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}


def _crosswalk_drift_guard() -> str:
    """Assert CROSSWALK matches the deriver source literal; abort on drift."""
    src = (REPO / "scripts" / "data" / "derive_actual_lmp.py").read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        targets = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets = [node.target]
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "ERCOT_MODEL_ZONE_TO_LZ":
                found = ast.literal_eval(node.value)
                if found != CROSSWALK:
                    raise SystemExit(
                        f"CROSSWALK DRIFT vs derive_actual_lmp.py: {found!r}"
                    )
                return "PASS"
    raise SystemExit("ERCOT_MODEL_ZONE_TO_LZ not found in derive_actual_lmp.py")


def build_lmp(price_by_zone: dict[str, np.ndarray], demand_by_zone: dict[str, np.ndarray]) -> dict:
    """Rebuild the payload ``lmp`` block exactly as render_calibration_html:2107-2155."""
    lmp: dict[str, dict] = {}
    for zone in price_by_zone:
        price = price_by_zone[zone]
        dem = demand_by_zone[zone]
        d_tot = float(dem.sum())
        p = float((price * dem).sum()) / d_tot if d_tot > 0 else float(price.mean())
        hr = np.arange(HOURS)
        midx = np.clip(np.searchsorted(_CUM, hr, side="right") - 1, 0, 11)
        p_mon: list = [None] * 12
        d_mon = [0.0] * 12
        for m in range(12):
            sel = midx == m
            if not sel.any():
                continue
            dd = float(dem[sel].sum())
            p_mon[m] = (
                round(float((price[sel] * dem[sel]).sum()) / dd, 2)
                if dd > 0
                else round(float(price[sel].mean()), 2)
            )
            d_mon[m] = round(dd / 1e6, 4)
        lmp[zone] = {"p": round(p, 2), "d": round(d_tot / 1e6, 4), "pMon": p_mon, "dMon": d_mon}
    return lmp


def tail_hours(price_by_zone: dict[str, np.ndarray], threshold: float) -> int:
    """render_calibration_html._tail_hours (line 817): max across zones, NaN -> -inf, strict >."""
    stack = np.vstack([np.nan_to_num(v, nan=-np.inf) for v in price_by_zone.values()])
    return int((stack.max(axis=0) > threshold).sum())


def monthly_model_vector(lmp: dict) -> list:
    """The scorer's C3b model vector: per-month demand-weighted mean across zones."""
    out = []
    for m in range(12):
        pairs = [
            (z["pMon"][m], z["dMon"][m])
            for z in lmp.values()
            if z["pMon"][m] is not None
        ]
        num = sum(p * d for p, d in pairs)
        den = sum(d for _, d in pairs)
        out.append(num / den if den > 0 else None)
    return out


def _py(o):
    """JSON-serialize numpy scalars/arrays."""
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"unserializable: {type(o)}")


def _rec(records, year, key=None):
    """Pick the (criterion, year, key) record out of a scorer's return."""
    if isinstance(records, dict):
        records = [records]
    for r in records:
        if r.get("year") == year and r.get("key") == key:
            return r
    raise KeyError(f"record year={year} key={key} not found")


def score_matrix(
    art: dict,
    run_id: str,
    price_by_zone: dict[str, np.ndarray],
    demand_by_zone: dict[str, np.ndarray],
) -> dict:
    """Rebuild the 2023 payload aggregates from a price matrix and re-score everything.

    Deep-copies the artifacts so the committed payload is never mutated; only
    ``years['2023'].lmp`` and the recomputed ``ordc.hoursGt200.model`` move.
    """
    art_cf = copy.deepcopy(art)
    ypay = art_cf["payload"]["years"][str(YEAR)]
    rebuilt = build_lmp(price_by_zone, demand_by_zone)
    for zone, blk in rebuilt.items():
        ypay["lmp"][zone].update(blk)
    n_tail_model = tail_hours(price_by_zone, THRESHOLD)
    ypay["ordc"]["hoursGt200"]["model"] = n_tail_model
    ybench = art_cf["bench"][YEAR]
    rm = _rec(cv.score_price_mean(YEAR, ypay, ybench), YEAR)
    rs = _rec(cv.score_price_shape(YEAR, ypay, ybench), YEAR)
    rt = _rec(cv.score_price_tail(YEAR, ypay, "ERCOT"), YEAR)
    v = cv.determine_from_artifacts(run_id, art_cf)
    crit = v.get("criteria", {})
    c3c_2023 = None
    for r in crit.get("price_tail", {}).get("records", []):
        if r.get("year") == YEAR and r.get("key") is None:
            c3c_2023 = {"status": r["status"], "classification": r.get("classification")}
    return {
        "c3a": {
            "model": rm["model"],
            "actual": rm["actual"],
            "magnitude": rm["magnitude"],
            "status": rm["status"],
        },
        "c3b": {"nrmse": rs["model"], "magnitude": rs["magnitude"], "status": rs["status"]},
        "c3b_model_mon": monthly_model_vector(ypay["lmp"]),
        "tail_count_model": n_tail_model,
        "c3c": {"model": rt["model"], "actual": rt["actual"], "status": rt["status"]},
        "determination_replay": {
            "determination": v["determination"],
            "reasons": v.get("reasons", []),
            "criteria": {k: c.get("status") for k, c in crit.items()},
            "c3c_2023_record": c3c_2023,
        },
        "clears_c3a_band": rm["status"] == "PASS",
        "clears_c3b_band": rs["status"] == "PASS",
    }


def main() -> None:
    apar = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    apar.add_argument("--run-id", default=RUN_ID_DEFAULT)
    apar.add_argument("--json", default=str(JSON_DEFAULT))
    args = apar.parse_args()

    guard = _crosswalk_drift_guard()
    art = cv.load_artifacts(args.run_id)
    bundle = REPO / art["sidecar"]["bundle"]
    ypay0 = art["payload"]["years"][str(YEAR)]
    ybench = art["bench"][YEAR]
    actual_rt_lw = float(ybench["avgLMP"]["rt_lw"])
    band_edge = 0.9 * actual_rt_lw  # PRICE_MEAN_TOL = 0.10, lower PASS edge

    # ---- model matrices from the committed hourly sidecar --------------------
    sy = pd.read_parquet(bundle / "hourly" / f"system_{YEAR}.parquet")
    assert set(sy["pass"].astype(str).unique()) == {"P1"}, "expected P1-only sidecar"
    price_by_zone: dict[str, np.ndarray] = {}
    demand_by_zone: dict[str, np.ndarray] = {}
    for zone, zg in sy.groupby("zone", observed=True):
        hr = zg["hour"].to_numpy()
        full = np.full(HOURS, np.nan)
        full[hr] = zg["price"].to_numpy(float)
        price_by_zone[str(zone)] = full
        full_d = np.zeros(HOURS)
        full_d[hr] = zg["demand"].to_numpy(float)
        demand_by_zone[str(zone)] = full_d
    zones = list(price_by_zone)
    assert len(zones) == 7 and len(sy) == 7 * HOURS, "unexpected sidecar shape"

    # ---- GATE 0: baseline reproduction (abort on ANY mismatch) ---------------
    rebuilt = build_lmp(price_by_zone, demand_by_zone)
    committed = {z: {k: ypay0["lmp"][z][k] for k in ("p", "d", "pMon", "dMon")} for z in zones}
    assert rebuilt == committed, "payload lmp rebuild mismatch vs committed payload"
    n58 = tail_hours(price_by_zone, THRESHOLD)
    assert n58 == int(ypay0["ordc"]["hoursGt200"]["model"]) == 58, f"tail rebuild {n58} != 58"
    assert "overlay" not in ypay0["ordc"]["hoursGt200"], "unexpected settlement overlay"
    base = score_matrix(art, args.run_id, price_by_zone, demand_by_zone)
    assert (base["c3a"]["model"], base["c3a"]["actual"]) == (43.23, 64.32)
    assert base["c3a"]["magnitude"] == "-32.8%" and base["c3a"]["status"] == "FAIL"
    assert base["c3b"]["nrmse"] == 0.608 and base["c3b"]["status"] == "FAIL"
    assert base["determination_replay"]["determination"] == "NOT-YET"
    assert set(base["determination_replay"]["criteria"].items()) >= {
        ("price_mean", "FAIL"), ("price_shape", "FAIL"), ("price_tail", "CAVEAT")}
    guards = {}
    for yr, want in ((2024, "+1.2%"), (2025, "-8.0%")):
        r = _rec(cv.score_price_mean(yr, art["payload"]["years"][str(yr)], art["bench"][yr]), yr)
        assert r["magnitude"] == want and r["status"] == "PASS", (yr, r["magnitude"])
        guards[str(yr)] = {"magnitude": r["magnitude"], "status": r["status"]}

    # lmpDeltaHr cross-check (committed unweighted hub instrument, $1 resolution)
    raw = np.frombuffer(__import__("base64").b64decode(ypay0["lmpDeltaHr"]), dtype="<i2")
    delta = raw.astype(float)
    delta[raw == -32768] = np.nan
    neg = np.sort(delta[delta < 0])
    lmp_delta = {
        "mean": float(np.nanmean(delta)),
        "neg181_share_of_neg_mass": float(neg[:181].sum() / neg.sum()),
        "n_neg_hours": int((delta < 0).sum()),
    }

    # in-frame (unrounded) flat demand-weighted model mean — the algebra frame
    P = np.vstack([price_by_zone[z] for z in zones])
    D = np.vstack([demand_by_zone[z] for z in zones])
    d_total = float(D.sum())
    flat_model_lw = float((P * D).sum() / d_total)

    # ---- actuals --------------------------------------------------------------
    vsrc = REPO / "data" / "raw" / "_validation-source"
    hub = pd.read_parquet(vsrc / "actual_lmp_hourly_ERCOT.parquet")
    hub = hub[hub["year"] == YEAR].sort_values("hour")
    hub_rt = np.full(HOURS, np.nan)
    hub_rt[hub["hour"].to_numpy()] = hub["rt"].to_numpy(float)
    assert int(np.isfinite(hub_rt).sum()) == HOURS, "hub RT 2023 not fully covered"
    h_tail = np.where(hub_rt > THRESHOLD)[0]
    tail_part = cv._tail_part()["ERCOT"][str(YEAR)]
    assert len(h_tail) == int(tail_part["rt_gt"]) == int(ypay0["ordc"]["hoursGt200"]["actual"]) == 181

    zonal = pd.read_parquet(vsrc / "actual_lmp_zonal_ERCOT.parquet")
    zonal = zonal[zonal["year"] == YEAR]
    lz_series: dict[str, np.ndarray] = {}
    for lz, g in zonal.groupby("settlement_point"):
        arr = np.full(HOURS, np.nan)
        arr[g["hour"].to_numpy()] = g["rt"].to_numpy(float)
        lz_series[str(lz)] = arr
    act_by_zone: dict[str, np.ndarray] = {}
    for z in zones:
        act_by_zone[z] = np.nanmean(np.vstack([lz_series[lz] for lz in CROSSWALK[z]]), axis=0)
    A = np.vstack([act_by_zone[z] for z in zones])
    nan_cells = {z: int(np.isnan(act_by_zone[z]).sum()) for z in zones}
    nan_in_tail = int(np.isnan(A[:, h_tail]).sum())

    def substituted(hours_idx: np.ndarray, mode: str, level: float | None = None) -> dict[str, np.ndarray]:
        """Price matrix with the counterfactual applied on ``hours_idx`` cells."""
        out = {z: price_by_zone[z].copy() for z in zones}
        for zi, z in enumerate(zones):
            cells = hours_idx[~np.isnan(A[zi, hours_idx])] if mode == "actual" else hours_idx
            if mode == "actual":
                out[z][cells] = A[zi, cells]
            elif mode == "floor":
                out[z][cells] = np.maximum(out[z][cells], level)
        return out

    all_hours = np.arange(HOURS)
    non_tail = np.setdiff1d(all_hours, h_tail)

    # ---- CF-0 seam gate -------------------------------------------------------
    cf0 = score_matrix(art, args.run_id, substituted(all_hours, "actual"), demand_by_zone)
    seam = float(cf0["c3a"]["model"]) - actual_rt_lw
    assert abs(seam) < 0.10, f"CF-0 seam {seam:+.4f} $/MWh exceeds the $0.10 gate"

    # ---- counterfactuals ------------------------------------------------------
    cf1 = score_matrix(art, args.run_id, substituted(h_tail, "actual"), demand_by_zone)
    cf2 = score_matrix(art, args.run_id, substituted(non_tail, "actual"), demand_by_zone)
    cf3 = {
        str(int(x)): score_matrix(art, args.run_id, substituted(h_tail, "floor", x), demand_by_zone)
        for x in (200.0, 500.0, 1000.0)
    }

    # X*: uniform tail floor that exactly reaches the lower band edge (in-frame,
    # unrounded flat mean vs the bench actual; bisection, then scorer-verified).
    def flat_lw_floor(level: float) -> float:
        M = P.copy()
        M[:, h_tail] = np.maximum(M[:, h_tail], level)
        return float((M * D).sum() / d_total)

    lo, hi = THRESHOLD, 6000.0
    assert flat_lw_floor(hi) > band_edge > flat_lw_floor(lo)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if flat_lw_floor(mid) < band_edge:
            lo = mid
        else:
            hi = mid
    x_star = 0.5 * (lo + hi)
    x_star_check = score_matrix(art, args.run_id, substituted(h_tail, "floor", x_star + 0.5), demand_by_zone)

    # Aug–Sep variants: the ercot-177 §7 "132-hour" subset of H_tail.
    as_mask = (h_tail >= AUG_SEP[0]) & (h_tail < AUG_SEP[1])
    h_tail_as = h_tail[as_mask]
    cf1_as = score_matrix(art, args.run_id, substituted(h_tail_as, "actual"), demand_by_zone)
    cf3_as = score_matrix(art, args.run_id, substituted(h_tail_as, "floor", 200.0), demand_by_zone)

    # ---- exact-arithmetic decomposition (in-frame, unrounded) -----------------
    A_eff = np.where(np.isnan(A), P, A)  # NaN actual cells contribute zero gap
    g_h = ((A_eff - P) * D).sum(axis=0)  # $·MWh per hour, + = model low
    total_gap = float(g_h.sum() / d_total)
    pos_gap = float(np.clip(g_h, 0, None).sum() / d_total)

    def contrib(idx: np.ndarray) -> dict:
        c = float(g_h[idx].sum() / d_total)
        cp = float(np.clip(g_h[idx], 0, None).sum() / d_total)
        return {
            "n_hours": int(len(idx)),
            "contrib_dollars_per_mwh": c,
            "share_of_net_gap": c / total_gap,
            "share_of_positive_gap": cp / pos_gap,
        }

    aug_sep_all = all_hours[(all_hours >= AUG_SEP[0]) & (all_hours < AUG_SEP[1])]
    order = np.argsort(g_h)[::-1]
    top100_unrestricted = order[:100]
    as_order = aug_sep_all[np.argsort(g_h[aug_sep_all])[::-1]]
    top100_aug_sep = as_order[:100]
    gt500 = np.where(hub_rt > 500.0)[0]
    gt1000 = np.where(hub_rt > 1000.0)[0]

    sets = {
        "h_tail_181": contrib(h_tail),
        "h_tail_aug_sep": contrib(h_tail_as),
        "top100_aug_sep_lw": contrib(top100_aug_sep),
        "top100_unrestricted_lw": contrib(top100_unrestricted),
        "aug_sep_months": contrib(aug_sep_all),
        "actual_gt500": contrib(gt500),
        "actual_gt1000": contrib(gt1000),
        "complement_of_h_tail": contrib(non_tail),
    }
    additivity = (
        sets["h_tail_181"]["contrib_dollars_per_mwh"]
        + sets["complement_of_h_tail"]["contrib_dollars_per_mwh"]
        - total_gap
    )

    # lw-mean prices inside H_tail (model demand weights, in-frame)
    w_tail = D[:, h_tail]
    tail_means = {
        "model_lw": float((P[:, h_tail] * w_tail).sum() / w_tail.sum()),
        "actual_lw": float((A_eff[:, h_tail] * w_tail).sum() / w_tail.sum()),
        "hub_actual_mean_unweighted": float(hub_rt[h_tail].mean()),
    }

    # ---- pristine post-battery check ------------------------------------------
    v_after = cv.determine_from_artifacts(args.run_id, cv.load_artifacts(args.run_id))
    assert v_after["determination"] == "NOT-YET", "committed artifacts were disturbed"

    out = {
        "probe": "ercot189_c3a_c3c_overlap",
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": args.run_id,
        "bundle": str(bundle.relative_to(REPO)),
        "inputs": {
            "system_parquet_rows": int(len(sy)),
            "zonal_actual_nan_cells": nan_cells,
            "zonal_actual_nan_cells_in_h_tail": nan_in_tail,
        },
        "definitions": {
            "h_tail_rule": "actual hub RT (HB_HUBAVG) > $200/MWh strict — the committed rt_gt set",
            "n_tail": int(len(h_tail)),
            "n_tail_aug_sep": int(len(h_tail_as)),
            "weighting_note": (
                "C3a weights zones by demand (two-stage, rounded); C3c counts model "
                "max-across-zones vs the actual hub series; H_tail is pinned to the "
                "actual-hub rt_gt definition and joined by hour index"
            ),
            "crosswalk": {k: list(v) for k, v in CROSSWALK.items()},
            "crosswalk_drift_guard": guard,
        },
        "baseline_gate": {
            "lmp_dict_equal": True,
            "hours_gt200_model_rebuilt": n58,
            "overlay_key_absent": True,
            **{k: base[k] for k in ("c3a", "c3b", "c3c", "determination_replay")},
            "flat_model_lw_inframe": flat_model_lw,
            "bar": {
                "actual_rt_lw": actual_rt_lw,
                "lower_band_edge": band_edge,
                "gap_to_bar_scorer": round(band_edge - base["c3a"]["model"], 4),
                "gap_to_bar_inframe": band_edge - flat_model_lw,
                "vintage_bar_dollars": 14.44,
                "miss_dollars": base["c3a"]["model"] - actual_rt_lw,
            },
            "guards_2024_2025": guards,
            "lmp_delta_hr": lmp_delta,
        },
        "seam": {
            "cf0_c3a_model": cf0["c3a"]["model"],
            "bench_rt_lw": actual_rt_lw,
            "seam_dollars": seam,
            "note": (
                "full-substitution reconciliation of the crosswalk/nanmean frame + LP "
                "demand weights + payload rounding against the bench rt_lw actual; "
                "bounds the precision of every CF row"
            ),
        },
        "counterfactuals": {
            "cf1_actual_in_tail": cf1,
            "cf1_aug_sep_tail_only": cf1_as,
            "cf2_actual_except_tail": cf2,
            "cf3_doorstep": cf3,
            "cf3_200_aug_sep_tail_only": cf3_as,
            "x_star_uniform_tail_level_to_bar": {
                "level_dollars": x_star,
                "inframe_model_at_level": flat_lw_floor(x_star),
                "scorer_check_at_level_plus_50c": x_star_check["c3a"],
            },
            "tail_price_means": tail_means,
        },
        "decomposition": {
            "frame": "unrounded flat demand-weighted zonal frame (NaN actual cells -> zero gap)",
            "total_gap_dollars_per_mwh": total_gap,
            "positive_gap_dollars_per_mwh": pos_gap,
            "sets": sets,
            "additivity_check_dollars": additivity,
            "reconciliation_vs_committed": {
                "memo184_top100_aug_sep_share_of_positive_gap": 0.681,
                "this_frame_top100_aug_sep": sets["top100_aug_sep_lw"]["share_of_positive_gap"],
                "ercot177_aug_sep_share_of_gap": 0.813,
                "this_frame_aug_sep_share_of_net": sets["aug_sep_months"]["share_of_net_gap"],
                "lmpdeltahr_neg181_share": 0.801,
                "this_probe_lmpdeltahr_neg181_share": lmp_delta["neg181_share_of_neg_mass"],
                "note": (
                    "committed instruments differ by weighting (lw vs unweighted), series "
                    "(zonal vs hub) and hour-set rule; expect close, not identical"
                ),
            },
        },
        "notes": [
            "READ-ONLY: no solve, no model input touched; actuals enter only counterfactual scoring",
            "CF-3 is the C3c-inertness doorstep, NOT the ceiling of quantity mechanisms — "
            "ERCOT-159's forced set reached mean $813 on measured $500-3,000 offers",
            "per-zone p rounded to 2dp before cross-zone weighting floors sub-cent CF resolution",
        ],
    }
    Path(args.json).write_text(json.dumps(out, indent=1, default=_py) + "\n")

    print(f"[gate0] PASS  C3a {base['c3a']['magnitude']}  C3b {base['c3b']['nrmse']}  "
          f"tail {n58}/181  det {base['determination_replay']['determination']}")
    print(f"[seam ] CF-0 model {cf0['c3a']['model']:.2f} vs bench {actual_rt_lw}  seam {seam:+.4f}")
    print(f"[cf1  ] C3a {cf1['c3a']['magnitude']} {cf1['c3a']['status']}  "
          f"C3b {cf1['c3b']['nrmse']} {cf1['c3b']['status']}  tail {cf1['tail_count_model']}  "
          f"det {cf1['determination_replay']['determination']}")
    print(f"[cf2  ] C3a {cf2['c3a']['magnitude']} {cf2['c3a']['status']}  "
          f"C3b {cf2['c3b']['nrmse']} {cf2['c3b']['status']}")
    for x, r in cf3.items():
        print(f"[cf3  ] floor ${x}: C3a {r['c3a']['magnitude']} {r['c3a']['status']} "
              f"(model {r['c3a']['model']:.2f})")
    print(f"[x*   ] uniform tail level to band edge: ${x_star:,.0f}")
    print(f"[decmp] H_tail share of net gap {sets['h_tail_181']['share_of_net_gap']:.3f}, "
          f"of positive gap {sets['h_tail_181']['share_of_positive_gap']:.3f}; "
          f"additivity {additivity:+.2e}")
    print(f"[write] {args.json}")


if __name__ == "__main__":
    main()
