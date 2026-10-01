"""PJM-NEXT-14 card 3 (zero LP): what the mid-curve floor does at the low end of the stack.

Two questions about the EXISTING mechanism (``pjm_offer_midcurve_conditional``), no new lever:

(a) THE NORMALIZER. The derive divides each measured offer by the delivered-gas day
    (HH + PJM basis) and the mechanism multiplies the stored multiplier back by the SAME
    day series, so in $/MWh the floor returns the measured offer level up to within-bin
    daily gas variation, whatever normalizer is used. For CC_LIKE the keeper runs the SHAPE
    form (``pjm_offer_midcurve_shape_segments = [CC_LIKE]``): the plant's own committed-rung
    cost times a measured ratio, so the normalizer cancels outright. This probe measures,
    from the ``fleet_only`` dump, the share of CC econ capacity whose bid comes from the
    shape form vs the level/floor fallback.

(b) THE AGGREGATE. The stored ladder is the capacity-weighted MEDIAN multiplier per
    (segment, year, net-load bin, within-unit share). As a raise-only floor applied to every
    unit of the segment, a median lifts every model row whose own cost sits below it, while
    in the measured fleet the lower half of the capacity offered below it. From the offers
    corpus (same segmentation and share sampling as ``derive_pjm_offer_midcurve.py``,
    all-hours, no net-load bin) this probe measures the full capacity-weighted distribution
    p10/p25/p50/p75/p90 of the multiplier per (segment, year, share). It then compares, on
    the dump's LONG_RUN econ rows (COAL_* and ST_GAS), the keeper's floored bid
    ``max(own, p50 x gas)`` with a RANK-MATCHED counterfactual ``max(own, q_r x gas)``,
    where ``q_r`` is the measured multiplier at the row's own capacity-weighted cost rank
    inside its class-year. Reported as the capacity-weighted mean $/MWh difference, so the
    size of the aggregate's lift is on the table before anyone designs anything.

Writes ``results/phase0/pjm/_pjmnext14_midcurve_dist.json``.
Run: ``python3 scripts/probes/_pjmnext14_midcurve_dist.py <dump_dir> <year> [...]``
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
from scripts.data.derive_pjm_offer_midcurve import (  # noqa: E402
    MULT_GRID,
    SHARES,
    _month_files,
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _pjm_fuel_daily,
)

OUT = REPO / "results/phase0/pjm/_pjmnext14_midcurve_dist.json"
QS = (0.10, 0.25, 0.50, 0.75, 0.90)
LONG_RUN_CLASSES = ("COAL_BIT", "COAL_WC", "COAL_PRB", "ST_GAS")


def _quantile_from_hist(h: np.ndarray, q: float) -> float:
    """Weighted quantile of a MULT_GRID histogram (cell upper edge)."""
    c = np.cumsum(h)
    if c[-1] <= 0:
        return float("nan")
    i = int(np.searchsorted(c, q * c[-1]))
    return float(MULT_GRID[min(i, len(MULT_GRID) - 1)])


def measured_distribution(y: int) -> dict:
    """Capacity-weighted multiplier quantiles per (segment, share), all hours of ``y``."""
    files, _ = _month_files([y])
    per_unit = _unit_physics(files)
    segs = _segments(per_unit)
    unit_seg = pd.Series("", index=per_unit.index, dtype=object)
    for s, idx in segs.items():
        unit_seg.loc[idx] = s
    names = sorted(segs)
    hist = np.zeros((len(names), len(SHARES), len(MULT_GRID) + 1))
    fuel = _pjm_fuel_daily()
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        seg = df["unit_code"].astype(str).map(unit_seg).fillna("")
        df, seg = df[seg != ""], seg[seg != ""]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        gas = fuel.reindex(pd.DatetimeIndex(ts.dt.normalize())).to_numpy(float)
        mws, bids = df[_MW_COLS].to_numpy(float), df[_BID_COLS].to_numpy(float)
        mw_max = np.nanmax(mws, axis=1)
        ok = np.isfinite(gas) & (gas > 0) & (mw_max > 0)
        r = np.where(ok)[0]
        sc = mws[r] / mw_max[r][:, None]
        ss = np.where(np.isfinite(sc), sc, np.inf)
        si_seg = seg.iloc[r].map({s: i for i, s in enumerate(names)}).to_numpy()
        w = df["avg_ecomax"].to_numpy(float)[r]
        for si, s in enumerate(SHARES):
            pos = np.minimum((ss < s).sum(axis=1), np.isfinite(sc).sum(axis=1) - 1)
            mult = bids[r][np.arange(len(r)), pos] / gas[r]
            m = np.isfinite(mult)
            cell = np.searchsorted(MULT_GRID, mult[m], side="right")
            np.add.at(hist, (si_seg[m], si, cell), w[m])
        print(f"  {p.name}", flush=True)
    out = {}
    for i, s in enumerate(names):
        out[s] = {
            f"{sh:.3f}": {
                f"p{int(q * 100)}": _quantile_from_hist(hist[i, j], q) for q in QS
            }
            for j, sh in enumerate(SHARES)
        }
    return out


def _share_col(share: float) -> str:
    """Nearest sampled share key."""
    return f"{SHARES[int(np.argmin(np.abs(SHARES - share)))]:.3f}"


def model_side(y: int, f: dict, dist: dict) -> dict:
    """Shape-form coverage for CC econ rows; median vs rank-matched floor on LONG_RUN."""
    uid = f["unit_ids"].astype(str)
    grp = f["plant_group"].astype(str)
    pc = f["plant_code"].astype(str)
    cap = f["pmax"]
    mc = f["mc_base"][:, :8760]
    mk = f.get("midcurve_markup")
    mk = np.zeros_like(mc) if mk is None else mk[:, :8760]
    days = pd.date_range(f"{y}-01-01", periods=8760, freq="h").normalize()
    gas = _pjm_fuel_daily().reindex(days).to_numpy(float)
    is_econ = np.char.find(uid.astype("U"), "_econ") >= 0

    # (a) CC econ rows: does the plant have a committed rung (shape form) or not?
    cc = np.where((grp == "CC_REGULAR") & is_econ)[0]
    plants_with_c = {
        pc[i] for i in np.where(grp == "CC_REGULAR")[0] if uid[i].endswith("_committed")
    }
    shape_mw = float(sum(cap[i] for i in cc if pc[i] in plants_with_c))
    res = {
        "cc_econ_mw_shape_form_share": round(shape_mw / float(cap[cc].sum()), 3),
    }

    # (b) LONG_RUN econ rows: within-plant share midpoint, own mult, rank inside class.
    lr = dist.get("LONG_RUN", {})
    for cls in LONG_RUN_CLASSES:
        rows = np.where((grp == cls) & is_econ)[0]
        if not len(rows) or not lr:
            continue
        # within-plant cumulative share midpoint of each econ row
        share = np.zeros(len(rows))
        for k, i in enumerate(rows):
            sel = np.where(pc == pc[i])[0]
            order = sorted(sel, key=lambda j: float(mc[j].mean()))
            c = np.cumsum(cap[order])
            pos = order.index(i)
            lo = c[pos - 1] if pos else 0.0
            share[k] = (lo + cap[i] / 2) / c[-1]
        own = mc[rows] / gas[None, :]  # (r, T) own implied mult
        own_mean = own.mean(axis=1)
        w = cap[rows]
        o = np.argsort(own_mean)
        rank = np.empty(len(rows))
        rank[o] = (np.cumsum(w[o]) - w[o] / 2) / w.sum()
        p50 = np.array([lr[_share_col(s)]["p50"] for s in share])
        pts = np.array(
            [[lr[_share_col(s)][f"p{int(q * 100)}"] for q in QS] for s in share]
        )
        q_r = np.array([np.interp(r, QS, pts[k]) for k, r in enumerate(rank)])
        bid_med = np.maximum(mc[rows], p50[:, None] * gas[None, :])
        bid_rank = np.maximum(mc[rows], q_r[:, None] * gas[None, :])
        cw = w[:, None] * np.ones((1, 8760))
        res[cls] = {
            "econ_mw": round(float(w.sum()), 0),
            "share_caphours_floored_at_p50": round(
                float((cw * (mc[rows] < p50[:, None] * gas[None, :])).sum() / cw.sum()),
                3,
            ),
            "keeper_markup_positive_share": round(
                float((cw * (mk[rows] > 0.01)).sum() / cw.sum()), 3
            ),
            "mean_bid_median_floor": round(float((bid_med * cw).sum() / cw.sum()), 2),
            "mean_bid_rank_matched": round(float((bid_rank * cw).sum() / cw.sum()), 2),
            "delta_rank_minus_median": round(
                float(((bid_rank - bid_med) * cw).sum() / cw.sum()), 2
            ),
            "own_mult_capw_p25_p50_p75": [
                round(float(np.percentile(np.repeat(own_mean, 1), q)), 2)
                for q in (25, 50, 75)
            ],
        }
    return res


def main() -> None:
    """Per year: measured distribution, then the model-side comparison."""
    d = Path(sys.argv[1])
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in [int(a) for a in sys.argv[2:]]:
        dist = measured_distribution(y)
        z = np.load(d / f"pjmnext13_fleet_{y}.npz", allow_pickle=True)
        rec = {
            "measured": {
                s: {
                    k: v
                    for k, v in dist[s].items()
                    if k in ("0.250", "0.450", "0.650", "0.850")
                }
                for s in dist
            },
            "model": model_side(y, {k: z[k] for k in z.files}, dist),
        }
        out[str(y)] = rec
        print(y, json.dumps(rec, indent=1), flush=True)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
