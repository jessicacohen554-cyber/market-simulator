"""miso-181 — NO-LP pre-checks for the D-2 coincident-peak seam-RESPONSE
envelope: the rank-displacement predictor (K-a), the 2023 against-interest
bound (K-b), the conditioning-sanity check (K-c), and the frozen
combination-arm condition — every rule fixed in the committed PREREG.

PREREG ``PREREG-miso181-seam-coincident-envelope-2026-08-24.md`` (committed
and pushed at ``9e9d1a1`` BEFORE this probe existed — the
miso-176/177/179/180 discipline). Descends from TWO committed machines:

* the ``_miso180_anchored_spread_precheck.py`` model side — the ``_miso178``
  wrapper repoints ``_miso156`` to the keeper bundle ``miso177_rho_B``;
  ``carry_price_demand``; the frozen affected mask; ``weighted_quantiles``;
  the committed dispersion vector + ``MISO_OFFER_SPREAD_ANCHOR_RANK``;
* the ``_miso174_seam_overimport_decomposition.py`` measured side —
  ``diba_wide`` at the solved −1 h hour-ending key, ``e930_balance``, the
  non-leap 8760 fold.

The frozen constructions (PREREG §2/§4):

* driver ``b(t)`` = the within-year percentile rank of EIA-930 PJM demand
  (``PJM_region.parquet`` type D, UTC −6 h to the model CST clock);
* ``cond_cap(b)`` = the p90 (``MISO_SEAM_FLOW_PERCENTILE``) of the measured
  PJM-seam net import over the year's hours in bin *b* of the DECLARED grid
  [0, 50, 75, 90, 95, 97.5, 99, 100], clip ≥ 0;
* removal series: ``R_bound`` (keeper aggregate import-class net minus −TI,
  clip ≥ 0 — the charter's K-a ceiling), ``R_hi`` (armed p90 PJM cap minus
  ``cond_cap(b(t))``, clip ≥ 0 — the mechanism's own ceiling), ``R_lo`` =
  min of the two;
* the rank-displacement predictor: ``r′ = min(r* + R/W, 1)``; ungrafted
  ``ΔP = max(0, Q_t(r′) − Q_t(r*))`` on the affected stack's own per-hour
  availcap-weighted quantile step function; grafted evaluates
  ``Q^g_t(r) = max(Q_t(r), A_m + (Q̂(r) − Q̂(0.875)) × G_ref)`` above the
  anchor.

Kills (adjudicated a → b → c AFTER everything is computed and reported):
K-a STOP→``I``: predicted C3a-2025 shift under ``R_bound`` < +0.5 pp on
BOTH stack variants. K-b KILL→``R``: predicted C3a-2023 under ``R_hi``
(ungrafted) outside ±10 %. K-c STOP→``R``: in ANY year, < 50 % of
``Σ R_hi`` in driver-percentile ≥ 90 hours, or > 10 % in < 50 hours.
Combination arm (PREREG §3): C-2 grafted 2023 inside ±10; C-3 ≥ 20 hours
of 2025 with ``R_lo > 0`` and ``r′ ≥ 0.875``; C-4 grafted-minus-ungrafted
reach at ``R_lo`` ≥ +0.10 pp.

Rule 22 ``[R-HOLDOUT]``: 2023–2025 only. Rule 13 ``[R-MEASURED]``: reads
committed artifacts and measured series; feeds nothing to any solve.

Usage::

    cd <repo root> && uv run --no-project \\
      --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \\
      python scripts/probes/_miso181_seam_response_precheck.py
"""

from __future__ import annotations

import gc
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    str(REPO),
    str(REPO / "src"),
    str(REPO / "scripts" / "probes"),
    str(REPO / "scripts" / "data"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Model-side machinery (the wrapper repoints _miso156 to miso177_rho_B).
import _miso174_seam_overimport_decomposition as _m174  # noqa: E402
import _miso178_c3a_decomposition as _m178  # noqa: E402
from derive_miso_offer_level_dispersion import (  # noqa: E402
    QUANTILE_GRID,
    weighted_quantiles,
)

from market_sim.config.constants import (  # noqa: E402
    MISO_OFFER_SPREAD_ANCHOR_RANK,
    MISO_SEAM_FLOW_PERCENTILE,
)
from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402
from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402

_m156 = _m178._m156
BUNDLE = _m178.BUNDLE
OUT = REPO / "results/calibration/_miso181_seam_response_precheck.json"
ARTIFACT = REPO / "data/raw/_validation-source/miso_offer_level_dispersion.json"
PJM_REGION = REPO / "data/raw/PJM_region.parquet"

#: PREREG §4 pinned digest (the miso-180 dispersion artifact, for the graft).
ARTIFACT_SHA256 = "b4e723127de638068cfacae84dd78c911e5c9a322b8738671c0dc1895eefde28"

YEARS = (2023, 2024, 2025)
HOURS = 8760
RANK_EPS = 0.01  # $/MWh, the frozen <= P_mod + eps rank cut (K-PRE-c verbatim)
CARRY = list(_m156.CARRY)

#: PREREG §2 declared conventions.
BIN_EDGES = (0.0, 50.0, 75.0, 90.0, 95.0, 97.5, 99.0, 100.0)
#: PREREG §4 kill thresholds.
KA_MIN_SHIFT_PP = 0.5
KB_BAND_PCT = 10.0
KC_TOP_SHARE_MIN = 0.50   # share of sum(R_hi) in driver-pctile >= 90 hours
KC_LOW_SHARE_MAX = 0.10   # share of sum(R_hi) in driver-pctile < 50 hours
#: PREREG §3 combination-arm condition.
C3_MIN_CROSS_HOURS = 20
C4_MIN_INCR_PP = 0.10
#: PREREG §4 validity thresholds.
V_DIBA_TI_MIN_R = 0.999   # 2023 and 2025 at the -1 h key
V_DRIVER_MIN_HOURS = 8600
#: Report-only ceiling line (the LP's maxgen slack ceiling, never adjudicating).
CEILING_USD = 500.0

_AFFECTED_SUFFIX = re.compile(r"_(econ\w*|peak\w*)$")
_AFFECTED_CLASS = re.compile(r"^(CC_|CT_|ST_GAS|COAL)")

MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 (the miso-174 line)
SCARCE_RT = 200.0


def carry_price_demand(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(T,) demand-weighted carry-zone P1 price and (T,) carry demand
    (the _miso180 helper verbatim, reading the wrapper's keeper bundle)."""
    sysf = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    sysf = sysf[(sysf["pass"] == "P1") & (sysf["zone"].isin(CARRY))]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    price = price.reindex(columns=CARRY).to_numpy(float)
    dem = dem.reindex(columns=CARRY).to_numpy(float)
    p_lw = (price * dem).sum(axis=1) / dem.sum(axis=1)
    return p_lw, dem.sum(axis=1)


def affected_mask(mb: dict) -> np.ndarray:
    """The frozen affected-stack selector (PREREG-miso179 §2 scope, verbatim)."""
    ids = np.array([str(g.unit_id) for g in mb["fleet"]])
    cls = mb["labels"]
    suf = np.array([bool(_AFFECTED_SUFFIX.search(u)) for u in ids])
    grp = np.array([bool(_AFFECTED_CLASS.match(str(c))) for c in cls])
    return suf & grp


# --------------------------------------------------------------------------
# measured substrate (PREREG §2/§4 constructions)
# --------------------------------------------------------------------------
def pjm_demand_hourly(year: int) -> np.ndarray:
    """EIA-930 PJM demand (MW) on the model's non-leap 8760 CST clock.

    UTC ``period`` − 6 h (the ``e930_balance`` convention), Feb 29 excised
    with the day-of-year fold ``diba_wide`` uses. Missing hours are NaN.
    """
    d = pd.read_parquet(PJM_REGION)
    d = d[d["type"] == "D"]
    ts = pd.DatetimeIndex(d["period"]) - pd.Timedelta(hours=6)
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    d, ts = d[keep], ts[keep]
    doy = ts.dayofyear.to_numpy()
    if bool(pd.Timestamp(f"{year}-12-31").dayofyear == 366):
        doy = np.where(doy > 60, doy - 1, doy)
    hour = (doy - 1) * 24 + ts.hour.to_numpy()
    val = pd.to_numeric(d["value_mwh"], errors="coerce").to_numpy(float)
    arr = np.full(HOURS, np.nan)
    ok = (hour >= 0) & (hour < HOURS)
    arr[hour[ok]] = val[ok]
    return arr


def driver_percentile(demand: np.ndarray) -> np.ndarray:
    """Within-year percentile rank (0–100] of each finite demand value."""
    s = pd.Series(demand)
    return (s.rank(pct=True) * 100.0).to_numpy()


def pjm_seam_measured(year: int) -> np.ndarray:
    """Measured PJM-seam net import (MW) per model hour, at the −1 h key."""
    w = _m174.diba_wide(year, -1)
    cols = [c for c in w.columns if str(c) in MISO_SEAM_DIBA["PJM"]]
    return w[cols].sum(axis=1, min_count=1).to_numpy(float)


def cond_caps(seam_meas: np.ndarray, pct: np.ndarray) -> tuple[np.ndarray, dict]:
    """PREREG §2: per-hour ``cond_cap(b(t))`` and the per-bin record.

    Bin population = same-year hours in the bin with a finite seam
    measurement; cap = ``np.percentile`` (the production estimator) at
    ``MISO_SEAM_FLOW_PERCENTILE``, clip ≥ 0. Hours with a missing driver or
    an empty bin carry NO conditioning (fail-open → +inf here so the min
    composition is inert there).
    """
    cap = np.full(HOURS, np.inf)
    bins: dict = {}
    for lo, hi in zip(BIN_EDGES[:-1], BIN_EDGES[1:]):
        inbin = np.isfinite(pct) & (pct > lo) & (pct <= hi)
        if lo == BIN_EDGES[0]:
            inbin = np.isfinite(pct) & (pct >= lo) & (pct <= hi)
        pop = seam_meas[inbin & np.isfinite(seam_meas)]
        key = f"({lo},{hi}]"
        if pop.size == 0:
            bins[key] = {"n": 0, "cap_mw": None}
            continue
        c = float(max(np.percentile(pop, float(MISO_SEAM_FLOW_PERCENTILE)), 0.0))
        cap[inbin] = c
        bins[key] = {"n": int(pop.size), "cap_mw": round(c, 1),
                     "n_hours_assigned": int(inbin.sum())}
    return cap, bins


def model_net_import(year: int) -> np.ndarray:
    """Keeper P1 ``import``-class net interchange (MW) per hour."""
    return _m174.model_net_import(BUNDLE / "hourly", year).to_numpy(float)


def meas_net_agg(year: int) -> np.ndarray:
    """Measured aggregate net import (MW) = −TI on the committed convention."""
    bal = _m174.e930_balance(year)
    arr = np.full(HOURS, np.nan)
    h = bal["hour"].to_numpy()
    ok = (h >= 0) & (h < HOURS)
    arr[h[ok]] = -bal["TI"].to_numpy(float)[ok]
    return arr


# --------------------------------------------------------------------------
# the rank-displacement predictor (PREREG §4)
# --------------------------------------------------------------------------
def predict(
    mb: dict,
    year: int,
    aff: np.ndarray,
    removal: np.ndarray,
    q_grid: np.ndarray,
    q_vec: np.ndarray,
    a_rank: float,
    rt_actual: np.ndarray,
) -> dict:
    """One (year × removal-series) prediction, BOTH stack variants.

    Returns the predicted C3a for the ungrafted and grafted stacks, the
    displaced-rank record, and the report-only splits.
    """
    p_mod, w_dem = carry_price_demand(year)
    T = p_mod.size
    mc = np.asarray(mb["mc_base"], float)[aff][:, :T]
    av = mb["availcap"][aff][:, :T].astype(float)
    R = np.nan_to_num(np.asarray(removal, float)[:T], nan=0.0)

    order = np.argsort(mc, axis=0, kind="stable")
    mc_s = np.take_along_axis(mc, order, axis=0)
    av_s = np.take_along_axis(av, order, axis=0)
    cum = np.cumsum(av_s, axis=0)
    W = cum[-1, :].copy()
    colix = np.arange(T)

    wmask = av > 0
    below = wmask & (mc <= (p_mod[None, :] + RANK_EPS))
    r_star = np.where(W > 0, np.where(below, av, 0.0).sum(axis=0) / np.maximum(W, 1.0), np.nan)
    dr = np.where(W > 0, R / np.maximum(W, 1.0), 0.0)
    r_prime = np.minimum(np.where(np.isfinite(r_star), r_star, 0.0) + dr, 1.0)
    clipped = np.isfinite(r_star) & (r_star + dr > 1.0)

    def q_at(r: np.ndarray) -> np.ndarray:
        target = r * W
        idx = np.clip((cum < target[None, :]).sum(axis=0), 0, mc_s.shape[0] - 1)
        return mc_s[idx, colix]

    live = np.isfinite(r_star) & (W > 0)
    q_rs = q_at(np.where(live, r_star, 0.0))
    q_rp = q_at(np.where(live, r_prime, 0.0))
    dp_ung = np.where(live, np.clip(q_rp - q_rs, 0.0, None), 0.0)

    # Grafted stack: A_m + (Q(r) − Q(a)) × G_ref above the anchor (miso-180 §3
    # constructions verbatim: pmax weights, month-mean mc, frozen estimator).
    gref = _m156.measured_gas_monthly(year)
    mo = pd.date_range(f"{year}-01-01", periods=T, freq="h").month.to_numpy() - 1
    pmax_aff = np.asarray(mb["arrays"].pmax)[aff].astype(float)
    a_month = np.full(12, np.nan)
    for m in range(12):
        hrs = mo == m
        if hrs.any():
            mc_m = mc[:, hrs].mean(axis=1)
            a_month[m] = float(weighted_quantiles(mc_m, pmax_aff, np.array([a_rank]))[0])
    q_a = float(np.interp(a_rank, q_grid, q_vec))
    graft_rp = a_month[mo] + np.clip(np.interp(r_prime, q_grid, q_vec) - q_a, 0.0, None) * gref[mo]
    q_rp_g = np.where(
        (r_prime > a_rank) & np.isfinite(graft_rp), np.maximum(q_rp, graft_rp), q_rp
    )
    dp_g = np.where(live, np.clip(q_rp_g - q_rs, 0.0, None), 0.0)

    bench = float(_m156.bench_actuals(year)["rt_lw"])
    lw_asis = float((p_mod * w_dem).sum() / w_dem.sum())
    c3a_asis = 100 * (lw_asis / bench - 1)

    su = np.zeros(T, dtype=bool)
    su[SUMMER[0]:SUMMER[1]] = True
    tail = np.isfinite(rt_actual[:T]) & (rt_actual[:T] > SCARCE_RT)

    def leg(dp: np.ndarray) -> dict:
        p_new = p_mod + dp
        lw_new = float((p_new * w_dem).sum() / w_dem.sum())
        c3a_new = 100 * (lw_new / bench - 1)
        moved = dp > 1e-9
        # $500-capped variant, report-only (PREREG §4 ceiling line).
        p_cap = np.minimum(p_new, np.maximum(p_mod, CEILING_USD))
        lw_cap = float((p_cap * w_dem).sum() / w_dem.sum())
        dpw = dp * w_dem
        month_pp = {
            str(m + 1): round(100 * float(dpw[mo == m].sum()) / float(w_dem.sum()) / bench, 4)
            for m in range(12)
            if (mo == m).any() and abs(float(dpw[mo == m].sum())) > 0
        }
        return {
            "c3a_predicted_pct": round(c3a_new, 4),
            "predicted_shift_pp": round(c3a_new - c3a_asis, 4),
            "predicted_shift_pp_ceiling500": round(100 * (lw_cap / bench - 1) - c3a_asis, 4),
            "hours_moved": int(moved.sum()),
            "hours_over_500": int((p_new > CEILING_USD).sum()),
            "mean_raise_on_moved_usd": round(float(dp[moved].mean()) if moved.any() else 0.0, 4),
            "max_raise_usd": round(float(dp.max()), 4),
            "shift_pp_tail_rt200": round(100 * float(dpw[tail].sum()) / float(w_dem.sum()) / bench, 4),
            "shift_pp_summer": round(100 * float(dpw[su].sum()) / float(w_dem.sum()) / bench, 4),
            "predicted_raise_pp_by_month": month_pp,
        }

    return {
        "bench_rt_lw": bench,
        "c3a_asis_pct": round(c3a_asis, 4),
        "removal": {
            "hours_positive": int((R > 0).sum()),
            "mean_positive_mw": round(float(R[R > 0].mean()) if (R > 0).any() else 0.0, 1),
            "max_mw": round(float(R.max()), 1),
            "sum_gwh": round(float(R.sum()) / 1e3, 2),
        },
        "r_star_mean": round(float(np.nanmean(r_star)), 4),
        "r_star_p90": round(float(np.nanquantile(r_star, 0.9)), 4),
        "hours_rank_clipped_at_1": int(clipped.sum()),
        "hours_no_affected_mass": int((~live).sum()),
        "n_cross_anchor": int(((R > 0) & live & (r_prime >= a_rank)).sum()),
        "ungrafted": leg(dp_ung),
        "grafted": leg(dp_g),
    }


# --------------------------------------------------------------------------
def main() -> dict:
    art_bytes = ARTIFACT.read_bytes()
    art_sha = hashlib.sha256(art_bytes).hexdigest()
    art = json.loads(art_bytes)
    q_grid = np.array(art["quantile_grid"], float)
    q_vec = np.array(art["pooled"]["quantiles_mmbtu_per_mwh"], float)
    assert art_sha == ARTIFACT_SHA256, f"artifact sha mismatch: {art_sha}"
    assert np.allclose(q_grid, QUANTILE_GRID), "artifact grid != frozen grid"
    a_rank = float(MISO_OFFER_SPREAD_ANCHOR_RANK)
    assert a_rank == 0.875, f"anchor constant drifted: {a_rank}"

    out: dict = {
        "session": "miso-181",
        "prereg": "PREREG-miso181-seam-coincident-envelope-2026-08-24.md",
        "keeper": "2026-08-22-miso-177-rho-measured",
        "bundle": BUNDLE.name,
        "anchor_rank": a_rank,
        "bin_edges": list(BIN_EDGES),
        "percentile": float(MISO_SEAM_FLOW_PERCENTILE),
    }

    # ---- measured substrate + validity (PREREG §4) ----
    substrate: dict = {}
    series: dict = {}
    for y in YEARS:
        dem = pjm_demand_hourly(y)
        pct = driver_percentile(dem)
        seam = pjm_seam_measured(y)
        agg = meas_net_agg(y)
        cap_env = measured_seam_import_envelope(
            "MISO", y, HOURS, None, "import", hour_ending_key=True
        )
        assert cap_env and "PJM" in cap_env, f"armed PJM envelope missing for {y}"
        cap_p90 = np.asarray(cap_env["PJM"], float)
        ccap, bins = cond_caps(seam, pct)
        # The V-gate correlates the FULL DIBA sum (all seams) against −TI.
        w_all = _m174.diba_wide(y, -1).sum(axis=1, min_count=1).to_numpy(float)
        okv = np.isfinite(w_all) & np.isfinite(agg)
        r_ti = float(np.corrcoef(w_all[okv], agg[okv])[0, 1])
        substrate[str(y)] = {
            "driver_finite_hours": int(np.isfinite(dem).sum()),
            "seam_finite_hours": int(np.isfinite(seam).sum()),
            "ti_finite_hours": int(np.isfinite(agg).sum()),
            "diba_vs_negTI_r_at_minus1h": round(r_ti, 4),
            "bins": bins,
        }
        series[y] = {"pct": pct, "seam": seam, "agg": agg,
                     "cap_p90": cap_p90, "ccap": ccap}
    out["substrate"] = substrate
    v_ok = all(
        substrate[str(y)]["driver_finite_hours"] >= V_DRIVER_MIN_HOURS for y in YEARS
    ) and all(
        substrate[str(y)]["diba_vs_negTI_r_at_minus1h"] >= V_DIBA_TI_MIN_R
        for y in (2023, 2025)
    )
    out["substrate"]["v_2024_diba_ti_note"] = (
        "2024 r reflects the PUBLISHED EIA-930 internal inconsistency "
        "(miso-174 §5, r=0.8286 at the solved key); disclosed, not gating"
    )
    if not v_ok:
        out["ABORT"] = "substrate validity failed (driver coverage or DIBA/TI key)"
        OUT.write_text(json.dumps(out, indent=1))
        print(json.dumps(out["substrate"], indent=1))
        return out

    # ---- removal series (PREREG §4) ----
    removals: dict = {}
    for y in YEARS:
        s = series[y]
        mnet = model_net_import(y)
        r_bound = np.clip(np.nan_to_num(mnet - s["agg"], nan=0.0), 0.0, None)
        tight = np.where(np.isfinite(s["ccap"]), np.clip(s["cap_p90"] - s["ccap"], 0.0, None), 0.0)
        r_hi = tight
        r_lo = np.minimum(r_hi, r_bound)
        removals[y] = {"R_bound": r_bound, "R_hi": r_hi, "R_lo": r_lo}
        series[y]["mnet"] = mnet

    # ---- K-c: conditioning sanity, model-free (all three years) ----
    kc: dict = {}
    kc_fail = False
    for y in YEARS:
        pct = series[y]["pct"]
        r_hi = removals[y]["R_hi"]
        tot = float(r_hi.sum())
        top = float(r_hi[np.isfinite(pct) & (pct >= 90.0)].sum())
        low = float(r_hi[np.isfinite(pct) & (pct < 50.0)].sum())
        mo = np.searchsorted(MONTH_START[1:], np.arange(HOURS), side="right") + 1
        by_month = {str(m): round(float(r_hi[mo == m].sum()) / 1e3, 1)
                    for m in range(1, 13) if float(r_hi[mo == m].sum()) > 0}
        row = {
            "sum_tightening_gwh": round(tot / 1e3, 2),
            "hours_tightened": int((r_hi > 0).sum()),
            "share_pctile_ge90": round(top / tot, 4) if tot > 0 else None,
            "share_pctile_lt50": round(low / tot, 4) if tot > 0 else None,
            "tightening_gwh_by_month": by_month,
        }
        row["pass"] = bool(
            tot > 0
            and row["share_pctile_ge90"] >= KC_TOP_SHARE_MIN
            and row["share_pctile_lt50"] <= KC_LOW_SHARE_MAX
        )
        kc_fail = kc_fail or not row["pass"]
        kc[str(y)] = row
    out["K_c"] = kc

    # ---- model side: 2025 (K-a + reach + combination), 2023 (K-b), 2024 ----
    cfg = _m156.keeper_config()
    preds: dict = {}
    validity: dict = {}
    for y in (2025, 2023, 2024):
        mb = _m156.model_year(cfg, y)
        v1 = _m156.v1_c3a_gate(mb, y)
        v4 = bool(len(mb["fleet"]) == _m156.V4_NGEN[y] and len(mb["carry_idx"]) == 6)
        validity[str(y)] = {"V1_pass": bool(v1["pass"]), "V1_c3a_pct": v1["c3a_pct"],
                            "V4_pass": v4}
        if not (v1["pass"] and v4):
            out["validity"] = validity
            out["ABORT"] = f"V1/V4 validity gate failed for {y}"
            OUT.write_text(json.dumps(out, indent=1))
            print(json.dumps(validity, indent=1))
            return out
        aff = affected_mask(mb)
        rt = _m174.actual_lmp(y)["rt"].to_numpy(float)
        preds[str(y)] = {
            name: predict(mb, y, aff, removals[y][name], q_grid, q_vec, a_rank, rt)
            for name in ("R_bound", "R_hi", "R_lo")
        }
        del mb
        gc.collect()
    out["validity"] = validity
    out["predictions"] = preds

    # ---- adjudication (PREREG §4 order a -> b -> c; §3 combination arm) ----
    ka_ung = preds["2025"]["R_bound"]["ungrafted"]["predicted_shift_pp"]
    ka_g = preds["2025"]["R_bound"]["grafted"]["predicted_shift_pp"]
    ka_fires = bool(ka_ung < KA_MIN_SHIFT_PP and ka_g < KA_MIN_SHIFT_PP)

    kb_ung = preds["2023"]["R_hi"]["ungrafted"]["c3a_predicted_pct"]
    kb_fires = bool(abs(kb_ung) > KB_BAND_PCT)
    kb_graft = preds["2023"]["R_hi"]["grafted"]["c3a_predicted_pct"]
    c2_pass = bool(abs(kb_graft) <= KB_BAND_PCT)

    n_cross = preds["2025"]["R_lo"]["n_cross_anchor"]
    c3_pass = bool(n_cross >= C3_MIN_CROSS_HOURS)
    incr = (
        preds["2025"]["R_lo"]["grafted"]["predicted_shift_pp"]
        - preds["2025"]["R_lo"]["ungrafted"]["predicted_shift_pp"]
    )
    c4_pass = bool(incr >= C4_MIN_INCR_PP)

    session_clear = not (ka_fires or kb_fires or kc_fail)
    out["ADJUDICATION"] = {
        "K_a": {
            "shift_pp_ungrafted": ka_ung, "shift_pp_grafted": ka_g,
            "threshold_pp": KA_MIN_SHIFT_PP,
            "verdict": "STOP_INERT" if ka_fires else "CLEAR",
        },
        "K_b": {
            "c3a_2023_predicted_ungrafted_pct": kb_ung,
            "band_pct": KB_BAND_PCT,
            "verdict": "KILL" if kb_fires else "CLEAR",
        },
        "K_c": {
            "per_year_pass": {y: kc[str(y)]["pass"] for y in map(str, YEARS)},
            "verdict": "STOP_UNIFORM" if kc_fail else "CLEAR",
        },
        "combination_arm": {
            "C2_grafted_2023_pct": kb_graft, "C2_pass": c2_pass,
            "C3_n_cross_anchor_Rlo": n_cross, "C3_pass": c3_pass,
            "C4_incremental_pp_Rlo": round(incr, 4), "C4_pass": c4_pass,
            "n_cross_anchor_Rhi_report": preds["2025"]["R_hi"]["n_cross_anchor"],
            "incremental_pp_Rhi_report": round(
                preds["2025"]["R_hi"]["grafted"]["predicted_shift_pp"]
                - preds["2025"]["R_hi"]["ungrafted"]["predicted_shift_pp"], 4),
            "BUILD_ARM_C": bool(session_clear and c2_pass and c3_pass and c4_pass),
        },
        "PROCEED_TO_BUILD": session_clear,
    }

    OUT.write_text(json.dumps(out, indent=1))

    adj = out["ADJUDICATION"]
    print(f"K-a  2025 shift under R_bound: ungrafted {ka_ung:+.3f} pp, "
          f"grafted {ka_g:+.3f} pp (stop@<+0.5 BOTH) -> {adj['K_a']['verdict']}")
    print(f"K-b  2023 predicted C3a under R_hi (ungrafted) {kb_ung:+.3f} % "
          f"(kill@|.|>10) -> {adj['K_b']['verdict']}")
    print(f"K-c  per-year pass {adj['K_c']['per_year_pass']} -> {adj['K_c']['verdict']}")
    ca = adj["combination_arm"]
    print(f"C-2 grafted 2023 {ca['C2_grafted_2023_pct']:+.3f} % pass={ca['C2_pass']}; "
          f"C-3 n_cross(R_lo)={ca['C3_n_cross_anchor_Rlo']} pass={ca['C3_pass']}; "
          f"C-4 incr(R_lo)={ca['C4_incremental_pp_Rlo']:+.3f} pp pass={ca['C4_pass']}")
    print(f"BUILD_ARM_C = {ca['BUILD_ARM_C']}   PROCEED_TO_BUILD = {adj['PROCEED_TO_BUILD']}")
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
