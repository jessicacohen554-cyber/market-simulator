"""pjm-h9 phase 0 (M2) — split PJM's masked LONG_RUN fleet by MEASURED fuel-cost passthrough.

ZERO LP. Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a).
Pre-registration: ``docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md`` §6.
**CORROBORATIVE ONLY** — M1 (``_pjm_h9_longrun_mixture_bound.py``) is the load-bearing
measurement and the PRECOMMIT's decision rule reads M1 alone. A point estimate cannot
overturn a bound; it can only locate the coal-only value inside one.

THE PROBLEM. PJM's ``energy_market_offers`` feed publishes a MASKED ``unit_code`` and no fuel
column, so the ``LONG_RUN`` segment (coal + gas-steam, median ``min_runtime`` > 16 h) cannot be
split by label. Route (b) of ``RESULT-pjm-h8`` §5 asks whether that admixture biases the
comparator high.

THE MEASURED DISCRIMINATOR — a physical property of fuel contracting, not a fitted label.
**A gas-fired unit's offer tracks the daily gas price; a coal unit's does not** (coal is bought
on monthly/quarterly contracts, which is the same take-or-pay physics the model's own coal
passthrough sigmoid encodes). In logs, with calendar-month fixed effects to kill seasonality::

    log(offer_u,d) = alpha_u,m + beta_u * log(P_gas,d) + eps

    beta_u ~ 1  <=>  gas-fired      beta_u ~ 0  <=>  coal-fired

The two hypotheses predict the two ENDPOINTS of the unit interval, so the classifying
threshold is their midpoint **0.5** — an a priori value, fixed in the PRECOMMIT before any
elasticity was computed, never swept.

DESIGN CHOICES FIXED BEFORE THE NUMBERS, and why:

* ``beta`` is estimated at within-unit share **0.55** — the mid-curve, deliberately away from
  BOTH the min-load region (where a must-run unit's floor offer is uninformative about its
  fuel, whatever it burns) and the top of curve (where a price-based offer carries scarcity
  markup, not fuel cost). A robustness table at 0.45 / 0.55 / 0.65 / 0.75 is reported.
* A unit's FUEL does not change with share, so the classification is made ONCE per unit at
  0.55 and then applied at EVERY share when the coal-only ladder is re-derived.
* Capacity weighting, segments, gas series, net-load bins and the mult grid are the frozen
  derive's, imported not re-implemented (rule 23 ``[R-FROZEN-DERIVE]``).

TWO CONTROLS, both reported:

1. **THE VOID CONDITION (PRECOMMIT §6).** ``CC_LIKE`` is a segment whose fuel is known from
   physics — PJM's CC fleet is gas. It must read **>= 80 % gas-linked by capacity**. If it does
   not, the discriminator has no demonstrated power, M2 is DISCARDED and only M1 stands.
2. **BIMODALITY.** If ``LONG_RUN`` is genuinely coal + gas-steam, its capacity-weighted
   ``beta`` histogram should be BIMODAL with mass near 0 and near 1. A unimodal histogram means
   either the segment is homogeneous or the discriminator has no power here — reported either
   way, and it is a diagnostic, not a gate.
3. **IMPLIED ADMIXTURE.** M2's own gas-linked capacity share of ``LONG_RUN`` is compared
   against the independent model-fleet estimate **w-hat = 0.1893** (committed h8 ladder).

Reports MULTIPLIERS AND ELASTICITIES ONLY, never prices (PJM DataMiner2 redistribution
restriction, ``docs/data-licensing.md`` §4).

Run: ``python3 scripts/probes/_pjm_h9_fuel_elasticity.py [--years 2023 2024 2025]``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_pjm_offer_midcurve import (  # noqa: E402
    MULT_GRID,
    SHARES,
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _month_files,
    _netload_pct,
    _pjm_fuel_daily,
)
from scripts.probes._pjm_h9_longrun_mixture_bound import quantile  # noqa: E402

OUT = REPO / "results/calibration/_pjm_h9_fuel_elasticity.json"

#: Share the elasticity is estimated at (PRECOMMIT §6), plus the reported robustness set.
BETA_SHARE = 0.55
ROBUST_SHARES = (0.45, 0.55, 0.65, 0.75)
#: Midpoint of the two theoretical endpoints (gas beta=1, coal beta=0). A priori.
GAS_THRESHOLD = 0.5
#: Minimum distinct days a unit needs before its elasticity is estimated at all.
MIN_DAYS = 60
#: Independent model-fleet admixture estimate (committed h8 ladder, 2023).
W_HAT = 0.1893


def _share_price(mws: np.ndarray, bids: np.ndarray, share: float) -> np.ndarray:
    """Offer price at a within-unit capacity share — the derive's own step rule."""
    mw_max = np.nanmax(mws, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        curve = mws / mw_max[:, None]
    sorted_ = np.where(np.isfinite(curve), curve, np.inf)
    pos = (sorted_ < share).sum(axis=1)
    pos = np.minimum(pos, np.isfinite(curve).sum(axis=1) - 1)
    return bids[np.arange(len(bids)), pos]


def collect(files: list[Path], unit_seg: pd.Series, shares) -> pd.DataFrame:
    """Per (unit, day) median offer at each share, plus the delivered-gas day price."""
    fuel = _pjm_fuel_daily()
    parts = []
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        seg = df["unit_code"].astype(str).map(unit_seg).fillna("")
        df = df[seg != ""]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        day = ts.dt.normalize()
        mws = df[_MW_COLS].to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        rec = {"unit": df["unit_code"].astype(str).to_numpy(), "day": day.to_numpy()}
        for s in shares:
            rec[f"p{int(s * 100)}"] = _share_price(mws, bids, s)
        part = pd.DataFrame(rec)
        part = part.groupby(["unit", "day"], as_index=False).median(numeric_only=True)
        parts.append(part)
        print(f"  [collect] {p.name}: {len(part)} unit-days", flush=True)
    out = pd.concat(parts, ignore_index=True)
    out["gas"] = fuel.reindex(pd.DatetimeIndex(out["day"])).to_numpy(float)
    return out[np.isfinite(out["gas"]) & (out["gas"] > 0.0)]


def elasticities(ud: pd.DataFrame, col: str) -> pd.DataFrame:
    """Per-unit log-log elasticity of offer on delivered gas, month fixed effects.

    Demeaning both sides WITHIN calendar month removes every seasonal level that
    is common to a month, so what is left is day-to-day co-movement only.
    """
    d = ud[["unit", "day", "gas", col]].copy()
    d = d[np.isfinite(d[col]) & (d[col] > 0.0)]
    if d.empty:
        return pd.DataFrame(columns=["unit", "beta", "r2", "n_days"])
    d["ly"] = np.log(d[col].to_numpy(float))
    d["lx"] = np.log(d["gas"].to_numpy(float))
    d["ym"] = pd.DatetimeIndex(d["day"]).to_period("M").astype(str)
    g = d.groupby(["unit", "ym"])
    d["ly"] -= g["ly"].transform("mean")
    d["lx"] -= g["lx"].transform("mean")
    rows = []
    for u, sub in d.groupby("unit"):
        n = len(sub)
        if n < MIN_DAYS:
            continue
        x = sub["lx"].to_numpy()
        y = sub["ly"].to_numpy()
        sxx = float((x * x).sum())
        if sxx <= 1e-12:
            continue
        beta = float((x * y).sum() / sxx)
        syy = float((y * y).sum())
        resid = y - beta * x
        r2 = float(1.0 - (resid * resid).sum() / syy) if syy > 1e-12 else np.nan
        rows.append({"unit": u, "beta": beta, "r2": r2, "n_days": n})
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    args = ap.parse_args(argv)
    t0 = time.time()

    files, coverage = _month_files(args.years)
    print(f"pass 1: unit physics over {len(files)} month files ...", flush=True)
    per_unit = _unit_physics(files)
    segments = _segments(per_unit)
    unit_seg = pd.Series("", index=per_unit.index, dtype=object)
    for seg, idx in segments.items():
        unit_seg.loc[idx] = seg

    print("pass 2: per-unit-day offers at the elasticity shares ...", flush=True)
    ud = collect(files, unit_seg, ROBUST_SHARES)
    ud["segment"] = ud["unit"].map(unit_seg)
    cap = per_unit["ecomax"]

    out: dict = {
        "what": (
            "per-unit log-log elasticity of the offer on the delivered-gas day price "
            "(calendar-month fixed effects); beta~1 = gas-fired, beta~0 = coal-fired"
        ),
        "precommit": "docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md",
        "role": "CORROBORATIVE ONLY -- M1's bound is the load-bearing measurement",
        "beta_share": BETA_SHARE,
        "gas_threshold": GAS_THRESHOLD,
        "min_days": MIN_DAYS,
        "w_hat_model_fleet": W_HAT,
        "month_coverage": coverage,
        "by_share": {},
    }

    beta_main = None
    for s in ROBUST_SHARES:
        col = f"p{int(s * 100)}"
        est = elasticities(ud, col)
        est["segment"] = est["unit"].map(unit_seg)
        est["cap"] = est["unit"].map(cap)
        est = est[np.isfinite(est["cap"])]
        if abs(s - BETA_SHARE) < 1e-9:
            beta_main = est.copy()
        per_seg = {}
        for seg, sub in est.groupby("segment"):
            tot = float(sub["cap"].sum())
            gas_cap = float(sub.loc[sub["beta"] > GAS_THRESHOLD, "cap"].sum())
            per_seg[str(seg)] = {
                "n_units": int(len(sub)),
                "mw": round(tot, 1),
                "gas_linked_capacity_share": round(gas_cap / tot, 4) if tot else None,
                "beta_capwtd_mean": round(
                    float((sub["beta"] * sub["cap"]).sum() / tot), 4
                )
                if tot
                else None,
                "beta_deciles": [
                    round(float(np.percentile(sub["beta"], q)), 3)
                    for q in range(10, 100, 10)
                ],
                "r2_median": round(float(sub["r2"].median()), 3),
            }
        out["by_share"][f"{s:.2f}"] = per_seg
        print(f"\n-- elasticity at share {s:.2f} --")
        for seg, r in sorted(per_seg.items()):
            print(
                f"   {seg:<9} n={r['n_units']:>4} {r['mw']:>9.0f} MW   "
                f"gas-linked cap share={r['gas_linked_capacity_share']}   "
                f"beta_capwtd={r['beta_capwtd_mean']}   r2_med={r['r2_median']}"
            )

    assert beta_main is not None
    cc = out["by_share"][f"{BETA_SHARE:.2f}"].get("CC_LIKE", {})
    void = (cc.get("gas_linked_capacity_share") or 0.0) < 0.80
    out["void_condition"] = {
        "cc_like_gas_linked_capacity_share": cc.get("gas_linked_capacity_share"),
        "bar": 0.80,
        "m2_void": bool(void),
    }
    print(
        f"\nVOID CONDITION: CC_LIKE gas-linked capacity share = "
        f"{cc.get('gas_linked_capacity_share')} (bar 0.80) -> "
        f"{'M2 IS VOID, only M1 stands' if void else 'M2 stands'}"
    )

    # Bimodality diagnostic: cap-weighted beta histogram for LONG_RUN and CC_LIKE.
    hedges = np.round(np.arange(-0.5, 1.7501, 0.125), 4)
    for seg in ("LONG_RUN", "CC_LIKE", "CT_FAST"):
        sub = beta_main[beta_main["segment"] == seg]
        if sub.empty:
            continue
        h, _ = np.histogram(
            sub["beta"].to_numpy(), bins=hedges, weights=sub["cap"].to_numpy()
        )
        out.setdefault("beta_histogram_capwtd", {})[seg] = {
            "edges": [float(x) for x in hedges],
            "mw": [round(float(v), 1) for v in h],
        }

    # The coal-only ladder, if M2 stands: same histogram machinery, coal units only.
    if not void:
        coal_units = set(
            beta_main.loc[
                (beta_main["segment"] == "LONG_RUN")
                & (beta_main["beta"] <= GAS_THRESHOLD),
                "unit",
            ]
        )
        gas_units = set(
            beta_main.loc[
                (beta_main["segment"] == "LONG_RUN")
                & (beta_main["beta"] > GAS_THRESHOLD),
                "unit",
            ]
        )
        out["longrun_split"] = {
            "coal_like_units": len(coal_units),
            "gas_like_units": len(gas_units),
            "coal_like_mw": round(float(cap.reindex(sorted(coal_units)).sum()), 1),
            "gas_like_mw": round(float(cap.reindex(sorted(gas_units)).sum()), 1),
        }
        tot = out["longrun_split"]["coal_like_mw"] + out["longrun_split"]["gas_like_mw"]
        out["longrun_split"]["implied_w"] = (
            round(out["longrun_split"]["gas_like_mw"] / tot, 4) if tot else None
        )
        print(f"\nLONG_RUN split: {out['longrun_split']}")
        out["coal_only_ladder"] = _coal_ladder(
            files, unit_seg, coal_units, args.years, tuple(args.edges)
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


def _coal_ladder(
    files: list[Path],
    unit_seg: pd.Series,
    coal_units: set[str],
    years: list[int],
    edges: tuple[float, ...],
) -> dict:
    """Re-derive the LONG_RUN ladder over the coal-classified units ONLY.

    Identical machinery to the frozen derive (same shares, same mult grid, same
    cap weighting, same net-load bins) — the ONLY change is the population.
    """
    nl = _netload_pct(years, "within-year")
    fuel = _pjm_fuel_daily()
    n_bins = len(edges) + 1
    hist = np.zeros((len(years), n_bins, len(SHARES), len(MULT_GRID) + 1), dtype=float)
    year_pos = {y: i for i, y in enumerate(years)}
    print("pass 3: coal-only ladder ...", flush=True)
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        df = df[df["unit_code"].astype(str).isin(coal_units)]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        day = ts.dt.normalize()
        he = (ts.dt.hour + 1).astype("int16")
        key = pd.DataFrame({"day": day.to_numpy(), "he": he.to_numpy()})
        q = key.merge(nl, on=["day", "he"], how="left")["q"].to_numpy(float)
        gas = fuel.reindex(pd.DatetimeIndex(day)).to_numpy(float)
        hbin = np.searchsorted(np.asarray(edges), q, side="right")
        year = ts.dt.year.to_numpy()
        mws = df[_MW_COLS].to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        w = df["avg_ecomax"].to_numpy(float)
        mw_max = np.nanmax(mws, axis=1)
        ok = np.isfinite(q) & np.isfinite(gas) & (gas > 0.0) & (mw_max > 0.0)
        rows = np.where(ok)[0]
        if rows.size == 0:
            continue
        mws_r, bids_r = mws[rows], bids[rows]
        curve = mws_r / mw_max[rows][:, None]
        sorted_ = np.where(np.isfinite(curve), curve, np.inf)
        gas_r, w_r, bin_r = gas[rows], w[rows], hbin[rows]
        yr_idx = np.array([year_pos.get(int(y), -1) for y in year[rows]])
        keep = yr_idx >= 0
        for si, s in enumerate(SHARES):
            pos = np.minimum(
                (sorted_ < s).sum(axis=1), np.isfinite(curve).sum(axis=1) - 1
            )
            mult = bids_r[np.arange(len(rows)), pos] / gas_r
            cell = np.searchsorted(MULT_GRID, mult, side="right")
            m = keep & np.isfinite(mult)
            np.add.at(hist, (yr_idx[m], bin_r[m], si, cell[m]), w_r[m])
        print(f"  [pass3] {p.name}: {rows.size} rows", flush=True)
    return {
        str(yr): [
            [
                [round(float(s), 2), round(quantile(hist[y, b, si], 0.5), 3)]
                for si, s in enumerate(SHARES)
            ]
            for b in range(n_bins)
        ]
        for y, yr in enumerate(years)
    }


if __name__ == "__main__":
    sys.exit(main())
