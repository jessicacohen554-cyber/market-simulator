"""Derive the MEASURED PJM DA virtual-bid surface (G-22 lever B).

From PJM's public DataMiner2 ``hrl_da_incs_decs`` feed
(``data/raw/pjm-da-virtuals/``, ``scripts/data/fetch_pjm_da_virtuals.py``),
measure the hourly INCrement-offer (virtual supply) and DECrement-bid
(virtual demand) curves — the *submitted ex-ante* bid ladders that give the
real Day-Ahead market its extra procurement depth at peaks (net cleared
DEC − INC ≈ +7–11 GW at the July-2024 top hours; the ~9-10 GW gap of
docs/FINDING-pjm-offer-surface-noop-2026-07.md) — condition-binned by a
forward-reproducible tightness driver, and freeze them into a condbinned
JSON the LP mechanism reads (``ScenarioConfig.pjm_da_virtual_bids``).

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/20/21)
-----------------------------------------------------------------------
1. Population: hourly RTO-aggregate INC/DEC MW by price point (the feed is
   already aggregated by price by PJM). These are SUBMITTED bid curves —
   participant inputs exactly like generator energy offers. Cleared
   volumes are outcomes and are NEVER used: clearing stays endogenous to
   the LP (the dual finds where the model's own stack crosses
   ``load + DEC(p) − INC(p)``), so nothing is pinned to a measured
   outcome (rule 13).
2. Normalization (forward-native axes):
   * MW axis: fraction of the hour's system load (EIA-930 PJM Demand) —
     a forecast year's own load series regenerates the MW depth.
   * Price axis: implied heat rate vs the model's PJM delivered-gas day
     series (Henry Hub daily + ``GAS_BASIS_DIFFERENTIAL['PJM']`` — the
     identical basis of ``derive_pjm_offer_surface._pjm_fuel_daily``):
     virtual traders price expected LMP, which scales with the marginal
     fuel. A forecast year's gas path regenerates the $ levels.
3. Tightness driver: system net-load percentile within year (EIA-930 PJM
   ``Demand − WND − SUN``) — identical construction to the PJM offer
   surface (``derive_pjm_offer_surface._netload_pct``). Edges default
   ``0.25/0.50/0.75/0.90/0.97`` — quartiles for the all-hours body (the
   virtual layer is a two-sided, all-hours phenomenon: DEC-heavy at
   peaks, INC-heavy off-peak) plus the ERCOT/NEISO-precedent top edges so
   the scarcity tail keeps its own bins.
4. Ladder: within each net-load bin, each side's curve is summarized as
   ``--rungs`` equal-MW rungs: per hour, the rung price is the MW-weighted
   price quantile at the rung's cumulative-share midpoint (DEC descending
   — willingness-to-pay curve; INC ascending — offer curve); per bin, the
   rung's implied-HR multiplier and the side's total MW/load fraction are
   medians across the bin's hours (robust to outlier days, no residual
   feedback).
5. INC steps whose median implied price lands below $0/MWh are DROPPED
   (recorded in provenance): a negative-priced virtual supply step would
   interact with the LP dump-cost guard (see CLAUDE.md objective notes)
   and clears only in negative-price hours the RTO-wide backcast does not
   resolve. DEC negative-price steps are kept (they clear only at
   negative duals — harmless tail).
6. Output: ``data/raw/_validation-source/pjm_da_virtual_surface_condbinned.json``
   + a per-bin summary CSV next to it, with full provenance.

Pre-committed honesty gate (rule 20): these parameters are frozen against
residuals — they re-derive only when the source data updates. If the A/B
degrades the backcast, the surface does NOT move and the probe registers
as REJECTED (rule 15).

Usage:
    python scripts/data/derive_pjm_da_virtual_surface.py [--years 2023 2024 2025]
        [--edges 0.25 0.50 0.75 0.90 0.97] [--rungs 8]
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
RAW_DIR = REPO / "data" / "raw" / "pjm-da-virtuals"
OUT_JSON = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "pjm_da_virtual_surface_condbinned.json"
)
OUT_CSV = (
    REPO / "data" / "raw" / "_validation-source" / "pjm_da_virtual_surface_summary.csv"
)

#: INC steps below this median implied price ($/MWh) are dropped (method §5).
INC_PRICE_FLOOR_USD = 0.0


def _load_hours(years: list[int]) -> pd.DataFrame:
    """(day, hour-ending) -> system load MW (EIA-930 PJM Demand)."""
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    frames = []
    for year in years:
        df = _eia_hourly_frame_filled("PJM", year)
        if df is None:
            raise SystemExit(f"EIA-930 PJM {year}: no clean 8760 frame")
        local = pd.DatetimeIndex(df["Local time"])
        frames.append(
            pd.DataFrame(
                {
                    "day": local.normalize(),
                    "he": local.hour + 1,
                    "load": pd.to_numeric(df["Demand"], errors="coerce")
                    .interpolate(limit_direction="both")
                    .to_numpy(float),
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(["day", "he"], as_index=False).agg(load=("load", "mean"))


def _month_files(years: list[int]) -> tuple[list[Path], dict]:
    files, coverage = [], {}
    for year in years:
        present = sorted(RAW_DIR.glob(f"hrl_da_incs_decs_{year:04d}_*.parquet"))
        coverage[year] = {"months_expected": 12, "files": len(present)}
        missing = sorted(
            {f"{m:02d}" for m in range(1, 13)}
            - {p.stem.rpartition("_")[2] for p in present}
        )
        if missing:
            raise SystemExit(
                f"{year}: missing raw virtual-bid month(s) {missing}; run "
                "scripts/data/fetch_pjm_da_virtuals.py first"
            )
        files.extend(present)
    return files, coverage


def _hour_rungs(prices: np.ndarray, mws: np.ndarray, qs: np.ndarray) -> np.ndarray:
    """MW-weighted price quantiles of one hour's one-sided curve.

    ``qs`` are cumulative-share midpoints in ascending-price order for INC
    (offer curve: cheapest rung first) — the caller passes ``1 - qs`` to
    read a DEC curve in descending willingness-to-pay order.
    """
    order = np.argsort(prices)
    p, w = prices[order], mws[order]
    cw = np.cumsum(w) - 0.5 * w
    return np.interp(qs * w.sum(), cw, p)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--edges", nargs="*", type=float, default=[0.25, 0.50, 0.75, 0.90, 0.97]
    )
    ap.add_argument("--rungs", type=int, default=8)
    args = ap.parse_args(argv)

    from derive_pjm_offer_surface import _netload_pct, _pjm_fuel_daily

    files, coverage = _month_files(args.years)
    nl = _netload_pct(args.years)
    loads = _load_hours(args.years)
    fuel = _pjm_fuel_daily()

    print(f"parsing {len(files)} month files ...", flush=True)
    parts = []
    for p in files:
        df = pd.read_parquet(
            p, columns=["bid_datetime_beginning_ept", "price_point", "inc_mw", "dec_mw"]
        )
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        df = pd.DataFrame(
            {
                "day": ts.dt.normalize().to_numpy(),
                "he": (ts.dt.hour + 1).astype("int8").to_numpy(),
                "price": df["price_point"].to_numpy(dtype="float32"),
                "inc": df["inc_mw"].to_numpy(dtype="float32"),
                "dec": df["dec_mw"].to_numpy(dtype="float32"),
            }
        )
        parts.append(df)
        print(f"  {p.name}: {len(df)} rows", flush=True)
    bids = pd.concat(parts, ignore_index=True)
    del parts

    bids = bids.merge(nl, on=["day", "he"], how="left")
    bids = bids.merge(loads, on=["day", "he"], how="left")
    bids["gas"] = fuel.reindex(pd.DatetimeIndex(bids["day"])).to_numpy(dtype="float32")
    n_unmatched = int(bids["q"].isna().sum())
    bids = bids.dropna(subset=["q", "load", "gas"])
    bids = bids[bids["gas"] > 0.0]
    print(f"bid rows: {len(bids)} ({n_unmatched} net-load-unmatched dropped)")

    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    bids["bin"] = np.searchsorted(
        np.asarray(edges), bids["q"].to_numpy(), side="right"
    ).astype("int8")

    K = int(args.rungs)
    qs = (np.arange(K) + 0.5) / K  # cumulative-share midpoints, cheapest first
    sides = {"INC": ("inc", qs), "DEC": ("dec", 1.0 - qs)}

    # Per-hour summaries: total MW fraction of load + rung prices per side.
    hour_rows = []
    for (day, he), g in bids.groupby(["day", "he"], sort=False):
        load = float(g["load"].iloc[0])
        gas = float(g["gas"].iloc[0])
        row = {
            "bin": int(g["bin"].iloc[0]),
            "load": load,
        }
        for side, (col, side_qs) in sides.items():
            m = g[col].to_numpy(dtype=float)
            keep = m > 0.0
            if keep.sum() == 0 or m[keep].sum() < 1.0:
                row[f"{side}_frac"] = 0.0
                for i in range(K):
                    row[f"{side}_hr{i}"] = np.nan
                continue
            p = g["price"].to_numpy(dtype=float)[keep]
            rung_p = _hour_rungs(p, m[keep], side_qs)
            row[f"{side}_frac"] = float(m[keep].sum() / load)
            for i in range(K):
                row[f"{side}_hr{i}"] = rung_p[i] / gas  # implied HR (MMBtu/MWh)
        hour_rows.append(row)
    hourly = pd.DataFrame(hour_rows)
    print(f"hourly curve summaries: {len(hourly)} hours")

    out: dict = {}
    summary_rows = []
    dropped_inc = []
    for side in sides:
        binned_ladder = []
        for b in range(n_bins):
            sub = hourly[hourly["bin"] == b]
            frac = float(sub[f"{side}_frac"].median()) if len(sub) else 0.0
            rung_frac = frac / K
            ladder = []
            for i in range(K):
                hr = float(sub[f"{side}_hr{i}"].median()) if len(sub) else np.nan
                if not np.isfinite(hr):
                    ladder.append([0.0, 0.0])
                else:
                    ladder.append([round(rung_frac, 5), round(hr, 3)])
            binned_ladder.append(ladder)
            summary_rows.append(
                {
                    "side": side,
                    "bin": b,
                    "n_hours": len(sub),
                    "total_frac": round(frac, 4),
                    **{f"rung{i + 1}_hr": ladder[i][1] for i in range(K)},
                }
            )
        out[side] = {"binned_ladder": binned_ladder}

    # INC price floor (method §5): a rung is priced hr x gas at solve time;
    # drop rungs whose implied HR is negative (price < $0 at any positive gas).
    n_dropped = 0
    for b in range(n_bins):
        ladder = out["INC"]["binned_ladder"][b]
        kept = []
        for frac_hr in ladder:
            if frac_hr[1] < INC_PRICE_FLOOR_USD:
                dropped_inc.append({"bin": b, "frac": frac_hr[0], "hr": frac_hr[1]})
                n_dropped += 1
            else:
                kept.append(frac_hr)
        out["INC"]["binned_ladder"][b] = kept

    out_doc = {
        "_provenance": {
            "source": (
                "PJM DataMiner2 hrl_da_incs_decs feed (monthly raw parquets, "
                f"data/raw/pjm-da-virtuals/), delivery years {args.years}"
            ),
            "method": (
                "hourly RTO-aggregate SUBMITTED INC/DEC bid curves, "
                f"{K} equal-MW rungs per side (MW-weighted price quantiles "
                "at cumulative-share midpoints; DEC read descending, INC "
                "ascending), per-net-load-bin medians across hours; MW "
                "normalized by hourly EIA-930 PJM Demand, price normalized "
                "to implied heat rate vs the model delivered-gas day series "
                "(HH daily + GAS_BASIS_DIFFERENTIAL[PJM]). Submitted bids "
                "only — cleared volumes are outcomes and are never read "
                "(clearing stays endogenous to the LP, rule 13)."
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 PJM Demand "
                "- WND - SUN), forward-native"
            ),
            "netload_pct_edges": list(edges),
            "rungs": K,
            "inc_price_floor_usd": INC_PRICE_FLOOR_USD,
            "inc_rungs_dropped_below_floor": dropped_inc,
            "month_coverage": coverage,
            "n_month_files_parsed": len(files),
            "n_rows_unmatched_netload": n_unmatched,
        },
        **out,
    }
    OUT_JSON.write_text(json.dumps(out_doc, indent=1))
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    print(f"INC rungs dropped below ${INC_PRICE_FLOOR_USD}/MWh: {n_dropped}")
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
