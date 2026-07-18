"""Derive the MEASURED PJM MID-CURVE offer surface (G-22 lever A').

pjm-99 proved the measured TOP-of-curve surface is inert in PJM: the LP's
marginal unit at the missed summer peaks sits at $30-45 inside a ~21 GW
idle mid-curve (COAL / CT_PEAKER / ST_GAS econ bands), while the measured
fleet prices the SAME capacity band at $35-83+
(docs/FINDING-pjm-offer-surface-noop-2026-07.md). The depth-price sweep on
the 2026-07-12 baseline quantified it: +10 GW of served depth moves the
model's implied price only +$2-4/MWh — the mid-curve, not the peak band,
caps the dual. This derive measures the mid-curve so the P1 mechanism
(``ScenarioConfig.pjm_offer_midcurve_conditional``,
``fleet.build_pjm_offer_midcurve_conditional_markup``) can floor the
model's econ tranches at the measured offer level.

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/20/21)
-----------------------------------------------------------------------
1. Population and physics segments are EXACTLY the pjm-99 derive's
   (``derive_pjm_offer_surface``): fast-start CT-like (median min_runtime
   <= 2 h), CC-like (min_runtime in (2, 16] h and ecomin/ecomax > 0.2),
   plus the LONG-RUN segment that derive deliberately excluded (median
   min_runtime > 16 h — the coal / gas-steam block), all excluding
   $0-top and nuclear-like resources. Segment edges/params are imported,
   never re-tuned (rule 20).
2. WITHIN-UNIT capacity shares, not cross-fleet quantiles: per unit-hour,
   the offer curve (cumulative ``mw1..mw20`` breakpoints, verified
   monotonic) is sampled at fixed within-unit shares
   (0.05, 0.15, ..., 0.95). A share is scale-free, so the model-fleet vs
   measured-segment capacity mismatch (e.g. 26 GW model CT vs 43.6 GW
   measured fast-start) cannot distort the mapping — the model's own
   plant tranches carry their within-plant share and read the surface at
   the same point of the curve.
3. Normalization: implied heat rate ``mult = price / gas_day`` vs the
   model's PJM delivered-gas day series (HH daily + PJM basis, identical
   to the pjm-99 derive). The ladder is stored PER DELIVERY YEAR (the
   mechanism reconstructs a backcast year with that year's own curves and
   the same gas-day series, so the within-year round-trip is exact up to
   within-bin gas variation) plus a pooled cap-weighted version for
   forward years.
4. Tightness driver: within-year net-load percentile (EIA-930 PJM
   ``Demand − WND − SUN``), edges 0.80/0.90/0.97 — the SAME edges as the
   frozen pjm-99 top-of-curve surface so the two mechanisms share one
   tightness state definition.
5. Ladder value: capacity-weighted MEDIAN mult at each
   (segment, year, bin, share), accumulated through a fixed mult-grid
   histogram (memory-bounded single pass per month file).
6. Output: ``data/raw/_validation-source/pjm_offer_midcurve_condbinned.json``
   (+ summary CSV): multipliers only, never prices (PJM DataMiner2
   redistribution restriction — same convention as the pjm-99 JSON).

Pre-committed honesty gate (rule 20): frozen against residuals; if the
A/B degrades the backcast the surface does NOT move and the probe
registers as REJECTED (rule 15).

Usage:
    python scripts/data/derive_pjm_offer_midcurve.py [--years 2023 2024 2025]
        [--edges 0.80 0.90 0.97]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
from derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _month_files,
    _netload_pct,
    _pjm_fuel_daily,
    CC_MAX_MIN_RUNTIME_H,
    CC_MIN_ECOMIN_RATIO,
    FAST_START_MAX_MIN_RUNTIME_H,
    NUCLEAR_ECOMIN_RATIO,
    NUCLEAR_MIN_ECOMAX_MW,
    ZERO_TOP_FLOOR_USD,
)

OUT_JSON = (
    REPO / "data" / "raw" / "_validation-source" / "pjm_offer_midcurve_condbinned.json"
)
OUT_CSV = (
    REPO / "data" / "raw" / "_validation-source" / "pjm_offer_midcurve_summary.csv"
)

#: Within-unit capacity shares the curve is sampled at (share-grid midpoints),
#: plus the top-of-curve belt (0.975 / 0.995 — the "last-5% wall" the decile
#: grid cannot see; 2026-07-13 G-22 lever-C extension). The pjm-99/A' findings
#: located the real $35-83+ price formation in exactly this belt, and the
#: LONG_RUN (coal / gas-steam) segment had no measured top at all — its model
#: peak tranche lives at within-plant shares ~0.85-1.0, so the segment-scoped
#: mid-curve floor (ScenarioConfig.pjm_offer_midcurve_segments) reads these
#: points. A sampling-grid extension only: the s05-s95 medians reproduce
#: identically from the same corpus (same method, same histogram).
SHARES = np.concatenate([np.arange(0.05, 1.0, 0.10), [0.975, 0.995]])

#: Implied-HR histogram grid: 0.05-wide cells from -20 to 400 (under/overflow
#: cells at the ends). Resolution only — not a tunable.
MULT_GRID = np.arange(-20.0, 400.0 + 1e-9, 0.05)


def _unit_physics(files: list[Path]) -> pd.DataFrame:
    """Pass 1: per-unit physics medians (mr, ecomin ratio, top, ecomax)."""
    parts = []
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["unit_code", "min_runtime", "avg_ecomin", "avg_ecomax"]
            + _BID_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        if df.empty:
            continue
        top = np.nanmax(df[_BID_COLS].to_numpy(dtype=float), axis=1)
        parts.append(
            pd.DataFrame(
                {
                    "unit": df["unit_code"].astype(str).to_numpy(),
                    "mr": df["min_runtime"].astype(float).to_numpy(),
                    "ratio": (df["avg_ecomin"] / df["avg_ecomax"]).to_numpy(float),
                    "ecomax": df["avg_ecomax"].astype(float).to_numpy(),
                    "top": top,
                }
            )
        )
        print(f"  [pass1] {p.name}", flush=True)
    allu = pd.concat(parts, ignore_index=True)
    return allu.groupby("unit").median(numeric_only=True)


def _segments(per_unit: pd.DataFrame) -> dict[str, pd.Index]:
    """Physics segmentation — the pjm-99 rules + the LONG_RUN block."""
    nuclear_like = (per_unit["ratio"] >= NUCLEAR_ECOMIN_RATIO) & (
        per_unit["ecomax"] >= NUCLEAR_MIN_ECOMAX_MW
    )
    zero_top = per_unit["top"] < ZERO_TOP_FLOOR_USD
    base = ~nuclear_like & ~zero_top
    return {
        "CT_FAST": per_unit.index[
            (per_unit["mr"] <= FAST_START_MAX_MIN_RUNTIME_H) & base
        ],
        "CC_LIKE": per_unit.index[
            (per_unit["mr"] > FAST_START_MAX_MIN_RUNTIME_H)
            & (per_unit["mr"] <= CC_MAX_MIN_RUNTIME_H)
            & (per_unit["ratio"] > CC_MIN_ECOMIN_RATIO)
            & base
        ],
        "LONG_RUN": per_unit.index[(per_unit["mr"] > CC_MAX_MIN_RUNTIME_H) & base],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    args = ap.parse_args(argv)

    files, coverage = _month_files(args.years)
    print("pass 1: unit physics ...", flush=True)
    per_unit = _unit_physics(files)
    segments = _segments(per_unit)
    unit_seg = pd.Series("", index=per_unit.index, dtype=object)
    for seg, idx in segments.items():
        unit_seg.loc[idx] = seg
        print(
            f"  segment {seg}: {len(idx)} units, "
            f"{per_unit.loc[idx, 'ecomax'].sum() / 1e3:.1f} GW (union of medians)"
        )

    nl = _netload_pct(args.years)
    fuel = _pjm_fuel_daily()
    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    seg_names = sorted(segments)
    n_cells = len(MULT_GRID) + 1  # + overflow

    # hist[(seg, year, bin, share)] -> MW-weighted mult histogram.
    hist = np.zeros(
        (len(seg_names), len(args.years), n_bins, len(SHARES), n_cells), dtype=float
    )
    seg_pos = {s: i for i, s in enumerate(seg_names)}
    year_pos = {y: i for i, y in enumerate(args.years)}

    print("pass 2: mid-curve sampling ...", flush=True)
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        if df.empty:
            continue
        seg = df["unit_code"].astype(str).map(unit_seg).fillna("")
        df = df[seg != ""]
        seg = seg[seg != ""]
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
        ok = np.isfinite(q) & np.isfinite(gas) & (gas > 0.0)
        # Vectorized within-unit share sampling: for each row, step-interp the
        # (cum-MW share, bid) curve at SHARES. Curves have <= 20 points; do it
        # with searchsorted per share over the padded arrays.
        mw_max = np.nanmax(mws, axis=1)
        ok &= mw_max > 0.0
        rows = np.where(ok)[0]
        if rows.size == 0:
            continue
        mws_r = mws[rows]
        bids_r = bids[rows]
        share_curve = mws_r / mw_max[rows][:, None]
        # replace NaN breakpoints with +inf share so searchsorted skips them
        share_sorted = np.where(np.isfinite(share_curve), share_curve, np.inf)
        gas_r = gas[rows]
        seg_idx = seg.iloc[rows].map(seg_pos).to_numpy()
        yr_idx = np.array([year_pos.get(int(y), -1) for y in year[rows]])
        bin_r = hbin[rows]
        w_r = w[rows]
        keep = yr_idx >= 0
        for si, s in enumerate(SHARES):
            # first breakpoint whose cumulative share >= s (step function).
            pos = (share_sorted < s).sum(axis=1)
            pos = np.minimum(pos, np.isfinite(share_curve).sum(axis=1) - 1)
            price = bids_r[np.arange(len(rows)), pos]
            mult = price / gas_r
            cell = np.searchsorted(MULT_GRID, mult, side="right")
            m = keep & np.isfinite(mult)
            np.add.at(
                hist,
                (seg_idx[m], yr_idx[m], bin_r[m], si, cell[m]),
                w_r[m],
            )
        print(f"  [pass2] {p.name}: {rows.size} rows", flush=True)

    # Histogram -> cap-weighted median mult per (seg, year, bin, share) +
    # pooled across years.
    grid_mid = np.concatenate([MULT_GRID - 0.025, [MULT_GRID[-1] + 0.025]])

    def _median(h: np.ndarray) -> float:
        tot = h.sum()
        if tot <= 0.0:
            return float("nan")
        cw = np.cumsum(h)
        return float(grid_mid[int(np.searchsorted(cw, 0.5 * tot))])

    out: dict = {}
    summary = []
    for s, seg_name in enumerate(seg_names):
        per_year: dict = {}
        for y, yr in enumerate(args.years):
            ladders = []
            for b in range(n_bins):
                lad = []
                for si, share in enumerate(SHARES):
                    lad.append(
                        [round(float(share), 2), round(_median(hist[s, y, b, si]), 3)]
                    )
                ladders.append(lad)
                summary.append(
                    {
                        "segment": seg_name,
                        "year": yr,
                        "bin": b,
                        "mw_weight": round(float(hist[s, y, b].sum()), 0),
                        **{
                            f"s{int(sh * 100):02d}": lad[si][1]
                            for si, sh in enumerate(SHARES)
                        },
                    }
                )
            per_year[str(yr)] = ladders
        pooled = []
        for b in range(n_bins):
            pooled.append(
                [
                    [
                        round(float(share), 2),
                        round(_median(hist[s, :, b, si].sum(axis=0)), 3),
                    ]
                    for si, share in enumerate(SHARES)
                ]
            )
        out[seg_name] = {"years": per_year, "pooled": pooled}

    out_doc = {
        "_provenance": {
            "source": (
                "PJM DataMiner2 energy_market_offers feed (monthly raw "
                f"parquets, data/raw/pjm-energy-offers/), delivery years "
                f"{args.years}"
            ),
            "method": (
                "within-unit capacity-share sampling of the full offer curve "
                f"(shares {[round(float(x), 2) for x in SHARES]}), implied-HR "
                "mult = price / delivered-gas day (HH daily + PJM basis), "
                "capacity-weighted median per (physics segment, delivery "
                "year, net-load bin, share) via a fixed mult-grid histogram. "
                "Segments are the pjm-99 physics rules (fast-start CT-like, "
                "CC-like) plus the LONG_RUN block (median min_runtime > "
                f"{CC_MAX_MIN_RUNTIME_H} h - coal / gas-steam), excluding "
                "$0-top and nuclear-like units. Offers only; clearing prices "
                "stay validation-only (rule 13)."
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 PJM Demand "
                "- WND - SUN), forward-native; edges shared with the frozen "
                "pjm-99 top-of-curve surface"
            ),
            "netload_pct_edges": list(edges),
            "shares": [round(float(x), 2) for x in SHARES],
            "segment_units": {s: int(len(segments[s])) for s in seg_names},
            "month_coverage": coverage,
            "n_month_files_parsed": len(files),
        },
        **out,
    }
    OUT_JSON.write_text(json.dumps(out_doc, indent=1))
    sdf = pd.DataFrame(summary)
    sdf.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    print(sdf.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
