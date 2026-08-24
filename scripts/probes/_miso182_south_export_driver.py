"""miso-182 — decompose MISO's South under-EXPORT by counterparty, and test the
Manitoba-precedent firm-block FORM against the measured seam.

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``): every number is a measurement of committed artifacts against
measured actuals, written to a JSON record for the finding.

The object (miso-174 §1, committed; miso-178 §7 lever 3 / §10 D-3): the model
UNDER-EXPORTS the South seam by **+0.63 / +0.35 / +1.19 GW** (2023/24/25 scarce
sets) — the largest single 2025 seam component — while over-pricing MISO-South
+18.8 / +21.0 / +17.0 %. The model's South gross import is ~0, so no import-side
lever can reach it. The admissible shape on the table is the **Manitoba
precedent**: an annual-flat, per-year firm block
(``MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR = {2023: 726, 2024: 531, 2025: 224}``).

Everything below is frozen by
``results/calibration/PREREG-miso182-south-export-driver-2026-08-24.md``
(committed BEFORE any adjudicating quantity was computed). No alternative key,
hour set, statistic, anchor, threshold or block form is computed here.

Stages:
  0 footing  — reproduce the scarce-set sizes (11/14/47) and the committed
               miso-174 South gaps, so every later number stands on a verified
               reproduction rather than an assumption.
  A level    — per-counterparty (SOCO/TVA/AECI/LGEE/SIKE) measured net flow by
               hour set and year, plus each counterparty's share of the seam's
               gross export (the ≥20% materiality screen).
  B signature— S-1..S-6 per counterparty AND for the two ANCHORS: MHEB
               (Manitoba, the seam the model reproduces) and PJM (the
               arbitrage-like seam the model fails).
  C G-1b     — anchored midpoint scoring: thresholds are the MHEB/PJM midpoints
               (measured-derived, no invented parameter); a dimension counts
               only if the anchors separate by >=25% of the larger |anchor|.
  D K-1      — THE FORM TEST (load-bearing). B_y closes the ANNUAL gap; K-1
               fires iff applying it flat WORSENS the scarce-set residual in
               >=2 of 3 years.

Hour key: the keeper's committed **-1 h** DIBA key (miso-174 §4 / miso-175;
r = 1.0000 / 0.8286 / 0.999998), on the model's fixed non-leap 8760 CST clock.
NOT re-solved here — frozen by the PREREG.

Sign conventions, stated on every table:
  * EIA-930 ``mw`` is + when MISO EXPORTS. ``net_import = -mw``.
  * S-3 (stress response) is reported in **net-import** terms for every seam,
    the miso-174 §3b convention: **positive = the seam helps MISO under stress**.
  * S-1 / S-4 / S-6 are computed on flow in the seam's **own dominant
    direction** (so an export seam is comparable to import anchors).
  * S-5 is reported as signed r on net import AND as |r|; the midpoint
    discriminant uses **|r|**, the direction-neutral reading required to compare
    an export seam against import anchors (disclosed, not swept).

Model side: the per-seam model split lives only in the PRUNED
``miso169_gated_A`` ``unit_hourly`` bundle (miso-181 §5), so it is CITED from
the committed ``_miso174_seam_overimport_decomposition.json`` record with its
measured vintage drift carried on every model-side number. Nothing is
re-derived.

Run:
  uv run --no-project --with pyarrow,pandas,numpy --python 3.12 \
    python scripts/probes/_miso182_south_export_driver.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402

CAL = ROOT / "results" / "calibration"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
ZONAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_zonal_MISO.parquet"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
M174 = CAL / "_miso174_seam_overimport_decomposition.json"
OUT = CAL / "_miso182_south_export_driver.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
SCARCE_RT = 200.0
FORESEEN_DA = 150.0
TOPN = 47

DIBA_KEY_SHIFT = -1  # FROZEN by the PREREG (miso-174 §4 / miso-175); never searched here
SOUTH = MISO_SEAM_DIBA["South"]
ANCHOR_MANITOBA = "MHEB"
ANCHOR_ARBITRAGE = "PJM"
DISCRIM_FLOOR = 0.25  # PREREG §3 G-1b: anchors must separate by >=25% of larger |anchor|
MATERIAL_SHARE = 0.20  # PREREG §3 G-1b: seam-level read over counterparties >=20% gross export


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def diba_wide(year: int, shift_h: int = DIBA_KEY_SHIFT) -> pd.DataFrame:
    """Measured per-DIBA NET IMPORT (MW, + = MISO imports) on the model hour key.

    The model's FIXED NON-LEAP 8760 clock: Feb 29 is dropped and every later day
    shifts back one, so a leap year maps onto the same 8760 positions as a
    common year (the miso-174 construction, reused verbatim).
    """
    d = pd.read_parquet(E930_DIBA).copy()
    ts = pd.DatetimeIndex(d["local_time"]) + pd.Timedelta(hours=shift_h)
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    d = d[keep]
    ts = ts[keep]
    doy = ts.dayofyear.to_numpy()
    if bool(pd.Timestamp(f"{year}-12-31").dayofyear == 366):
        doy = np.where(doy > 60, doy - 1, doy)
    d = d.assign(hour=(doy - 1) * 24 + ts.hour.to_numpy())
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)]
    w = d.pivot_table(index="hour", columns="diba", values="mw", aggfunc="first")
    return (-w).reindex(range(HOURS))  # net import


def actual_lmp(year: int) -> pd.DataFrame:
    """MISO's measured RT and DA hub LMP for ``year``, on the model hour key."""
    a = pd.read_parquet(ACTUAL)
    return a[a["year"] == year][["hour", "rt", "da"]].reset_index(drop=True)


def south_zonal_rt(year: int) -> np.ndarray:
    """MISO-South measured RT price (hub-mean grain) on the model hour key."""
    z = pd.read_parquet(ZONAL)
    z = z[(z["year"] == year) & (z["zone"] == "MISO-South")]
    s = z.groupby("hour")["rt"].mean().reindex(range(HOURS))
    return s.to_numpy(dtype=float)


def hour_sets(year: int) -> dict[str, np.ndarray]:
    """The FROZEN miso-174/178 hour sets as boolean masks over 8760."""
    a = actual_lmp(year)
    rt = a.set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)
    da = a.set_index("hour")["da"].reindex(range(HOURS)).to_numpy(dtype=float)
    idx = np.arange(HOURS)
    summer = (idx >= SUMMER[0]) & (idx < SUMMER[1])
    scarce = summer & (rt > SCARCE_RT)
    foreseen = summer & (da > FORESEEN_DA)
    top = np.zeros(HOURS, dtype=bool)
    order = np.argsort(-np.nan_to_num(rt, nan=-np.inf)[summer])
    top[idx[summer][order[:TOPN]]] = True
    return {"annual": np.ones(HOURS, dtype=bool), "summer": summer,
            "scarce": scarce, "da_foreseen": foreseen, "top47_rt": top}


def _mean(x: np.ndarray, m: np.ndarray) -> float:
    v = x[m]
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


# --------------------------------------------------------------------------
# stage B — the signature
# --------------------------------------------------------------------------
def signature(net_import: np.ndarray, summer: np.ndarray, scarce: np.ndarray,
              price_south: np.ndarray, price_sys: np.ndarray) -> dict:
    """S-1..S-6 for one counterparty/anchor in one year (PREREG §2)."""
    ann = _mean(net_import, np.ones(HOURS, dtype=bool))
    dom = 1.0 if ann >= 0 else -1.0          # seam's own dominant direction
    flow_d = net_import * dom                 # + = the seam's dominant direction

    # S-2 seasonality: CV of the 12 monthly means (robust to a near-zero mean)
    monthly = [_mean(net_import, _month_mask(m)) for m in range(12)]
    mm = np.array(monthly, dtype=float)
    denom = float(np.nanmean(np.abs(mm)))
    s2_cv = float(np.nanstd(mm) / denom) if denom > 1e-9 else float("nan")

    # S-4 volatility
    d1 = np.abs(np.diff(net_import))
    d1 = d1[np.isfinite(d1)]
    s4_abs = float(d1.mean()) if d1.size else float("nan")
    s4_rel = float(s4_abs / abs(ann)) if abs(ann) > 1e-9 else float("nan")

    # S-5 price sensitivity (summer), signed on NET IMPORT; |r| is the discriminant
    r_south = _pearson(net_import[summer], price_south[summer])
    r_sys = _pearson(net_import[summer], price_sys[summer])

    # S-6 blockiness on the dominant-direction flow
    s6_modal, s6_levels = _blockiness(flow_d)

    return {
        "S1_level_annual_mw_dominant": float(ann * dom),
        "S1_level_summer_mw_dominant": float(_mean(net_import, summer) * dom),
        "dominant_direction": "import" if dom > 0 else "export",
        "S2_monthly_means_net_import_mw": [None if not np.isfinite(v) else round(float(v), 2)
                                           for v in monthly],
        "S2_seasonality_cv": s2_cv,
        "S3_stress_response_gw_net_import": (_mean(net_import, scarce)
                                             - _mean(net_import, summer)) / 1000.0,
        "S4_volatility_mw_per_h": s4_abs,
        "S4_volatility_rel": s4_rel,
        "S5_r_vs_south_rt_signed": r_south,
        "S5_r_vs_system_rt_signed": r_sys,
        "S5_abs_r_vs_south_rt": abs(r_south) if np.isfinite(r_south) else float("nan"),
        "S6_modal_level_share": s6_modal,
        "S6_levels_covering_80pct": s6_levels,
    }


def _month_mask(m: int) -> np.ndarray:
    idx = np.arange(HOURS)
    return (idx >= MONTH_START[m]) & (idx < MONTH_START[m + 1])


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 3:
        return float("nan")
    x, y = a[ok], b[ok]
    if x.std() < 1e-12 or y.std() < 1e-12:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def _blockiness(flow: np.ndarray) -> tuple[float, int]:
    """Share of hours within +-25 MW of the modal 100-MW level; #levels for 80%."""
    v = flow[np.isfinite(flow)]
    if v.size == 0:
        return float("nan"), -1
    binned = np.round(v / 100.0) * 100.0
    levels, counts = np.unique(binned, return_counts=True)
    modal = float(levels[np.argmax(counts)])
    share = float(np.mean(np.abs(v - modal) <= 25.0))
    order = np.argsort(-counts)
    cum = np.cumsum(counts[order]) / v.size
    n80 = int(np.searchsorted(cum, 0.80) + 1)
    return share, n80


# --------------------------------------------------------------------------
# stage C — anchored midpoint scoring
# --------------------------------------------------------------------------
DIMS = [
    ("S1", "S1_level_annual_mw_dominant"),
    ("S2", "S2_seasonality_cv"),
    ("S3", "S3_stress_response_gw_net_import"),
    ("S4", "S4_volatility_rel"),
    ("S5", "S5_abs_r_vs_south_rt"),
    ("S6", "S6_modal_level_share"),
]


def score_g1b(sig: dict[str, dict]) -> dict:
    """Midpoint-threshold scoring against the MHEB / PJM anchors (PREREG §3)."""
    man, arb = sig[ANCHOR_MANITOBA], sig[ANCHOR_ARBITRAGE]
    dims: dict[str, dict] = {}
    for did, key in DIMS:
        a, p = float(man.get(key, np.nan)), float(arb.get(key, np.nan))
        if not (np.isfinite(a) and np.isfinite(p)):
            dims[did] = {"discriminating": False, "reason": "anchor not finite"}
            continue
        sep = abs(a - p)
        larger = max(abs(a), abs(p))
        disc = bool(larger > 1e-9 and sep >= DISCRIM_FLOOR * larger)
        dims[did] = {"discriminating": disc, "manitoba": a, "pjm": p,
                     "midpoint": (a + p) / 2.0,
                     "separation_frac_of_larger": (sep / larger) if larger > 1e-9 else float("nan"),
                     "reason": None if disc else "anchors separate by <25% of larger |anchor|"}
    out: dict[str, dict] = {"dimensions": dims}
    n_disc = sum(1 for d in dims.values() if d.get("discriminating"))
    out["n_discriminating"] = n_disc
    for name, s in sig.items():
        if name in (ANCHOR_MANITOBA, ANCHOR_ARBITRAGE):
            continue
        hits, detail = 0, {}
        for did, key in DIMS:
            d = dims[did]
            if not d.get("discriminating"):
                detail[did] = None
                continue
            x = float(s.get(key, np.nan))
            if not np.isfinite(x):
                detail[did] = None
                continue
            # Manitoba-side = on MHEB's side of the midpoint
            side = (x >= d["midpoint"]) if d["manitoba"] >= d["pjm"] else (x <= d["midpoint"])
            detail[did] = bool(side)
            hits += int(side)
        out[name] = {"manitoba_side_hits": hits, "n_discriminating": n_disc,
                     "per_dimension": detail, "g1b_pass": bool(hits >= 3)}
    return out


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    m174 = json.loads(M174.read_text())
    rec: dict = {
        "session": "miso-182",
        "prereg": "PREREG-miso182-south-export-driver-2026-08-24.md",
        "keeper_bundle": "miso177_rho_B (unchanged; no LP spent)",
        "model_side_source": {
            "record": "_miso174_seam_overimport_decomposition.json",
            "bundle": m174.get("unit_hourly_bundle"),
            "note": ("per-seam model split CITED, not re-derived: the only MISO bundle "
                     "carrying unit_hourly (miso169_gated_A) is PRUNED (miso-181 §5). "
                     "Its measured aggregate drift vs the keeper is carried below."),
        },
        "diba_hour_key_shift": DIBA_KEY_SHIFT,
        "sign_convention": ("EIA-930 mw is + when MISO EXPORTS; net_import = -mw. "
                            "S-3 in net-import terms (+ = seam helps MISO under stress). "
                            "S-1/S-4/S-6 on the seam's own dominant direction. "
                            "S-5 discriminant uses |r| (direction-neutral)."),
        "stage0_footing": {}, "stageA_level": {}, "stageB_signature": {},
        "stageC_g1b": {}, "stageD_k1_form_test": {},
    }

    for y in YEARS:
        ys = str(y)
        sets = hour_sets(y)
        w = diba_wide(y)
        present = [str(c) for c in w.columns]
        south_cols = [c for c in w.columns if str(c) in SOUTH]
        south_net = w[south_cols].sum(axis=1, min_count=1).to_numpy(dtype=float)
        p_south = south_zonal_rt(y)
        p_sys = actual_lmp(y).set_index("hour")["rt"].reindex(range(HOURS)).to_numpy(dtype=float)

        # ---- stage 0: footing
        m174_meas = m174["stage2_measured_by_seam"][ys]
        m174_model = m174["stage3_model_by_seam"][ys]
        rec["stage0_footing"][ys] = {
            "n_scarce": int(sets["scarce"].sum()),
            "n_da_foreseen": int(sets["da_foreseen"].sum()),
            "dibas_present": present,
            "south_dibas_present": [str(c) for c in south_cols],
            "south_dibas_absent": [d for d in SOUTH if d not in present],
            "measured_south_net_import_gw_annual": _mean(south_net, sets["annual"]) / 1000.0,
            "m174_measured_south_net_import_gw_annual":
                m174_meas.get("annual", {}).get("South_gw"),
            "m174_model_south_net_import_gw_annual":
                m174_model.get("annual", {}).get("South_gw"),
            "m174_model_south_gross_import_gw_annual":
                m174_model.get("annual", {}).get("South_imp_gw"),
            "m174_model_drift_vs_keeper": m174_model.get("drift_vs_keeper", {}),
        }

        # ---- stage A: per-counterparty level + gross-export share
        lvl: dict = {}
        gross_exp_total = 0.0
        for c in south_cols:
            v = w[c].to_numpy(dtype=float)
            exp = np.where(np.isfinite(v) & (v < 0), -v, 0.0)  # gross export MW
            gross_exp_total += float(np.nansum(exp))
        for c in south_cols:
            v = w[c].to_numpy(dtype=float)
            exp = np.where(np.isfinite(v) & (v < 0), -v, 0.0)
            lvl[str(c)] = {
                "net_import_gw_by_set": {k: _mean(v, m) / 1000.0 for k, m in sets.items()},
                "net_export_gw_by_set": {k: -_mean(v, m) / 1000.0 for k, m in sets.items()},
                "gross_export_share": (float(np.nansum(exp)) / gross_exp_total
                                       if gross_exp_total > 0 else float("nan")),
                "material_ge_20pct": bool(gross_exp_total > 0
                                          and float(np.nansum(exp)) / gross_exp_total
                                          >= MATERIAL_SHARE),
                "coverage_hours": int(np.isfinite(v).sum()),
            }
        lvl["_SEAM_TOTAL"] = {
            "net_import_gw_by_set": {k: _mean(south_net, m) / 1000.0 for k, m in sets.items()},
            "net_export_gw_by_set": {k: -_mean(south_net, m) / 1000.0 for k, m in sets.items()},
        }
        rec["stageA_level"][ys] = lvl

        # ---- stage B: signature (South counterparties + the two anchors)
        sig: dict[str, dict] = {}
        for name in [str(c) for c in south_cols] + [ANCHOR_MANITOBA, ANCHOR_ARBITRAGE]:
            if name not in [str(c) for c in w.columns]:
                continue
            v = w[name].to_numpy(dtype=float)
            if np.isfinite(v).sum() < 100:  # SIKE-class absence: reported, never gated
                sig[name] = {"excluded": True, "coverage_hours": int(np.isfinite(v).sum())}
                continue
            sig[name] = signature(v, sets["summer"], sets["scarce"], p_south, p_sys)
        sig["_SEAM_SOUTH"] = signature(south_net, sets["summer"], sets["scarce"], p_south, p_sys)
        rec["stageB_signature"][ys] = sig

        # ---- stage C: G-1b anchored scoring
        scoreable = {k: v for k, v in sig.items() if not v.get("excluded")}
        rec["stageC_g1b"][ys] = (score_g1b(scoreable)
                                 if ANCHOR_MANITOBA in scoreable and ANCHOR_ARBITRAGE in scoreable
                                 else {"error": "anchor missing"})

        # ---- stage D: K-1 form test (PREREG §3, load-bearing)
        # Work in NET EXPORT terms: + = MISO exports to the South seam.
        meas_exp_ann = -_mean(south_net, sets["annual"]) / 1000.0
        meas_exp_sc = -_mean(south_net, sets["scarce"]) / 1000.0
        mdl_exp_ann = -float(m174_model["annual"]["South_gw"])
        mdl_exp_sc = -float(m174_model["summer_scarce_rt200"]["South_gw"])
        b_y = meas_exp_ann - mdl_exp_ann                     # the Manitoba-form block (GW)
        gap_sc = meas_exp_sc - mdl_exp_sc                    # pre-block scarce gap
        resid_sc = gap_sc - b_y                              # post-block scarce residual
        rec["stageD_k1_form_test"][ys] = {
            "measured_net_export_gw_annual": meas_exp_ann,
            "model_net_export_gw_annual": mdl_exp_ann,
            "block_B_y_gw": b_y,
            "measured_net_export_gw_scarce": meas_exp_sc,
            "model_net_export_gw_scarce": mdl_exp_sc,
            "gap_scarce_gw_preblock": gap_sc,
            "residual_scarce_gw_postblock": resid_sc,
            "worsened": bool(abs(resid_sc) > abs(gap_sc)),
            "abs_gap_preblock": abs(gap_sc),
            "abs_residual_postblock": abs(resid_sc),
        }

    n_worse = sum(1 for y in YEARS if rec["stageD_k1_form_test"][str(y)]["worsened"])
    rec["stageD_k1_form_test"]["VERDICT"] = {
        "years_worsened": n_worse,
        "line": ">=2 of 3 years worsened => K-1 FIRES (flat-block form REFUTED)",
        "K1_FIRES": bool(n_worse >= 2),
    }

    OUT.write_text(json.dumps(rec, indent=2, default=str))
    print(f"wrote {OUT}")

    # ---- console summary
    print("\n=== stage 0 footing (scarce-set sizes; miso-174 expects 11/14/47) ===")
    for y in YEARS:
        f = rec["stage0_footing"][str(y)]
        print(f"  {y}  n_scarce={f['n_scarce']:3d}  measured South net import "
              f"{f['measured_south_net_import_gw_annual']:+.3f} GW "
              f"(m174 {f['m174_measured_south_net_import_gw_annual']:+.3f})  "
              f"absent={f['south_dibas_absent']}")

    print("\n=== stage A: per-counterparty measured NET EXPORT (GW, + = MISO exports) ===")
    for y in YEARS:
        print(f"  -- {y}")
        for c, d in rec["stageA_level"][str(y)].items():
            if c == "_SEAM_TOTAL":
                continue
            e = d["net_export_gw_by_set"]
            print(f"     {c:6s} annual {e['annual']:+.3f}  summer {e['summer']:+.3f}  "
                  f"scarce {e['scarce']:+.3f}   gross-export share {d['gross_export_share']:.1%}"
                  f"{'  [MATERIAL]' if d['material_ge_20pct'] else ''}")
        t = rec["stageA_level"][str(y)]["_SEAM_TOTAL"]["net_export_gw_by_set"]
        print(f"     {'SEAM':6s} annual {t['annual']:+.3f}  summer {t['summer']:+.3f}  "
              f"scarce {t['scarce']:+.3f}")

    print("\n=== stage B: signature (S-3 stress response, GW net import; + = helps MISO) ===")
    for y in YEARS:
        row = []
        for name, s in rec["stageB_signature"][str(y)].items():
            if s.get("excluded"):
                continue
            row.append(f"{name}={s['S3_stress_response_gw_net_import']:+.2f}")
        print(f"  {y}  " + "  ".join(row))

    print("\n=== stage C: G-1b anchored midpoint scoring ===")
    for y in YEARS:
        g = rec["stageC_g1b"][str(y)]
        if "error" in g:
            print(f"  {y}  {g['error']}")
            continue
        nd = g["n_discriminating"]
        disc = [k for k, v in g["dimensions"].items() if v.get("discriminating")]
        print(f"  {y}  discriminating dims ({nd}): {disc}")
        for name, v in g.items():
            if name in ("dimensions", "n_discriminating"):
                continue
            print(f"       {name:12s} manitoba-side {v['manitoba_side_hits']}/{nd}  "
                  f"G-1b {'PASS' if v['g1b_pass'] else 'fail'}")

    print("\n=== stage D: K-1 FORM TEST (the load-bearing gate) ===")
    for y in YEARS:
        k = rec["stageD_k1_form_test"][str(y)]
        print(f"  {y}  B_y={k['block_B_y_gw']:+.3f} GW   scarce gap {k['gap_scarce_gw_preblock']:+.3f}"
              f" -> residual {k['residual_scarce_gw_postblock']:+.3f}   "
              f"{'WORSE' if k['worsened'] else 'improved'}")
    v = rec["stageD_k1_form_test"]["VERDICT"]
    print(f"  VERDICT: {v['years_worsened']}/3 worsened -> "
          f"K-1 {'FIRES (flat-block form REFUTED)' if v['K1_FIRES'] else 'CLEARS'}")


if __name__ == "__main__":
    main()
