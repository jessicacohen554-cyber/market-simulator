"""Derive the MEASURED NEISO fast-start offer surface (charter Limb B).

The ISO-NE analogue of ``scripts/derive_dam_offer_hrmults.py --condition-binned``
(the ERCOT G-22 §8 heterogeneity-preserving surface): from the public
Day-Ahead Energy Market historical offer data
(``data/raw/NEISO-AS/da-energy-offers/``, masked asset IDs,
``scripts/fetch_neiso_da_energy_offers.py``), measure the fast-start
(peaker-like) fleet's TOP-OF-CURVE offer distribution, condition-binned by a
forward-reproducible tightness driver, and freeze it into a condbinned JSON
the P1-only markup mechanism reads
(``ScenarioConfig.neiso_offer_surface_conditional``).

Method (measured, NOT fit to any residual — CLAUDE.md rules 1/13/21)
--------------------------------------------------------------------
1. Population: per (day, hour, asset) rows with ``Unit Status`` ECONOMIC or
   MUST_RUN and ``Economic Maximum`` > 0. The fast-start segment is selected
   by PHYSICS, not fuel labels (the data is masked): assets whose claimed
   30-minute capability covers >= 90% of their Economic Maximum
   (``Claim 30 >= 0.9 x EcoMax`` — ISO-NE's own fast-start concept: the whole
   unit is deliverable within 30 minutes). This is the population the model's
   ``CT_PEAKER`` class represents.
2. Per asset-hour, the TOP-OF-CURVE offer price = the highest-priced offer
   segment (segments are incremental MW blocks from Economic Min up). The
   heat-rate multiplier basis mirrors the ERCOT derive::

       mult = (top_price / fuel_price_day) / base_HR(CT_PEAKER)

   ``fuel_price_day`` is the model's OWN NEISO delivered-gas day series
   (Algonquin Citygate daily spot, ``data.fuel.ALGONQUIN_DAILY_PATH``,
   forward-filled between anchors exactly as sparse daily series are used
   model-side), and ``base_HR`` is the cap-weighted CT_PEAKER heat rate from
   the model's NEISO fleet — the same HR the mechanism later multiplies, so
   the multiplier round-trips.
3. Tightness driver: system net load (EIA-930 ISNE ``Demand − NG:WND −
   NG:SUN``), percentile-ranked within each year — the identical
   forward-native construction the mechanism applies at solve time (a
   forecast year's own load/VRE forecast regenerates it).
4. Ladder: within each net-load bin (edges default 0.80/0.90/0.97 — the
   ERCOT precedent), each asset contributes its own MEDIAN top-of-curve
   multiplier (so a frequently-offering asset cannot dominate), then assets
   are capacity-weighted (EcoMax) into 5 equal-capacity quantile rungs
   (cap shares 0.2). Rungs are clamped below by the class's all-hours p50
   (a loose bin never lowers an offer below the body) — the same clamp as
   the ERCOT derive. The ISO-NE $1,000/MWh energy offer cap is already IN
   the measured offers; no synthetic cap is imposed here.
5. Output: ``data/raw/_validation-source/neiso_offer_surface_condbinned.json``
   (the exact ``offer_curve_dam_hrmults_condbinned.json`` schema, CT_PEAKER
   entry) + a per-bin summary CSV next to it, with full provenance (edges,
   day coverage incl. the endpoint's known unpublished-day gaps, the
   critical tail-event days verified present).

Pre-committed honesty gate (G-22 §5 discipline): these parameters are frozen
against residuals (rule 20 — they re-derive only when the source data
updates); if the A/B degrades the backcast the surface does NOT move and the
probe registers as REJECTED; measured prices stay validation-only.

Usage:
    python scripts/derive_neiso_offer_surface.py [--years 2023 2024 2025]
        [--edges 0.80 0.90 0.97] [--rungs 5]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

RAW_DIR = REPO / "data" / "raw" / "NEISO-AS" / "da-energy-offers"
OUT_JSON = (
    REPO / "data" / "raw" / "_validation-source" / "neiso_offer_surface_condbinned.json"
)
OUT_CSV = (
    REPO / "data" / "raw" / "_validation-source" / "neiso_offer_surface_summary.csv"
)

#: Fast-start selection: claimed 30-minute capability covers this fraction of
#: Economic Maximum (ISO-NE fast-start concept; physics, not a tuned value).
FAST_START_CLAIM30_FRAC = 0.9

#: The DA>$300 tail-event days (docs/calibration-log.md 2026-07-10 entry);
#: the derive hard-errors if any is missing from the raw archive.
CRITICAL_DAYS = (
    "20230203",
    "20230204",
    "20240620",
    "20240715",
    "20240716",
    "20250624",
    "20250716",
    "20250729",
    "20251208",
)


def _load_algonquin_daily() -> pd.Series:
    """The model's NEISO delivered-gas day series, forward-filled to daily."""
    from market_sim.data.fuel import ALGONQUIN_DAILY_PATH

    df = pd.read_csv(ALGONQUIN_DAILY_PATH, parse_dates=["date"])
    s = df.set_index("date")["algonquin_citygate_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    return s.reindex(full).ffill()


def _ct_peaker_base_hr() -> float:
    """Cap-weighted gas-CT heat rate from the model's NEISO fleet cache.

    ``data/raw/_processed-legacy/neiso_fleet_binned.parquet`` is the exact
    fleet the NEISO solve builds its CT_PEAKER class from, so the heat rate
    divided by here is the one the mechanism later multiplies (the ERCOT
    derive's round-trip convention).
    """
    df = pd.read_parquet(
        REPO / "data" / "raw" / "_processed-legacy" / "neiso_fleet_binned.parquet"
    )
    ct = df[df["fuel_type"] == "gas_ct"]
    if ct.empty:
        raise SystemExit("no gas_ct units in the NEISO binned fleet cache")
    return float(np.average(ct["heat_rate"], weights=ct["pmax_mw"]))


def _day_files(years: list[int]) -> tuple[list[Path], dict]:
    files, coverage = [], {}
    for year in years:
        present = sorted(RAW_DIR.glob(f"hbdayaheadenergyoffer_{year}*.csv"))
        n_days = (dt.date(year, 12, 31) - dt.date(year, 1, 1)).days + 1
        nonempty = [p for p in present if p.stat().st_size > 1000]
        coverage[year] = {"days_in_year": n_days, "files": len(present)}
        files.extend(nonempty)
    missing_critical = [
        d
        for d in CRITICAL_DAYS
        if int(d[:4]) in years
        and not (RAW_DIR / f"hbdayaheadenergyoffer_{d}.csv").exists()
    ]
    if missing_critical:
        raise SystemExit(
            f"critical tail-event day(s) missing from raw: {missing_critical}; "
            f"run scripts/fetch_neiso_da_energy_offers.py first"
        )
    return files, coverage


def _parse_day(path: Path) -> pd.DataFrame | None:
    """One day's fast-start top-of-curve offers: (day, hour, asset, top, cap)."""
    recs = []
    with path.open(newline="") as fh:
        for r in csv.reader(fh):
            if not r or r[0] != "D":
                continue
            try:
                eco_max = float(r[7] or 0.0)
                claim30 = float(r[34] or 0.0)
            except (ValueError, IndexError):
                continue
            status = r[35].strip() if len(r) > 35 else ""
            if eco_max <= 0.0 or status not in ("ECONOMIC", "MUST_RUN"):
                continue
            if claim30 < FAST_START_CLAIM30_FRAC * eco_max:
                continue
            # segments: columns 13..32 as (price, mw) pairs; top-of-curve =
            # highest-priced non-null segment.
            top = None
            for k in range(13, 33, 2):
                v = r[k] if k < len(r) else ""
                if v not in ("", None):
                    p = float(v)
                    top = p if top is None else max(top, p)
            if top is None:
                continue
            he = int(r[2].strip().upper().rstrip("X"))  # 02X -> 2 (fall-back)
            recs.append((r[1], he, int(r[4]), top, eco_max))
    if not recs:
        return None
    df = pd.DataFrame(recs, columns=["day", "he", "asset_id", "top_price", "eco_max"])
    df["day"] = pd.to_datetime(df["day"], format="%m/%d/%Y")
    return df


def _netload_pct(years: list[int]) -> pd.DataFrame:
    """(local day, hour-ending) -> within-year net-load percentile."""
    from market_sim.data.eia_loader import _eia_hourly_frame

    frames = []
    for year in years:
        df = _eia_hourly_frame("ISNE", year)
        if df is None:
            raise SystemExit(f"EIA-930 ISNE {year}: no clean 8760 frame")
        net = (
            df["Demand"].to_numpy(float)
            - df["NG: WND"].to_numpy(float)
            - df["NG: SUN"].to_numpy(float)
        )
        q = pd.Series(net).rank(pct=True).to_numpy()
        local = pd.DatetimeIndex(df["Local time"])
        frames.append(
            pd.DataFrame(
                {
                    "day": local.normalize(),
                    "he": local.hour + 1,  # hour-ending label basis
                    "q": q,
                    "year": year,
                }
            )
        )
    out = pd.concat(frames, ignore_index=True)
    # DST fall-back repeats (day, he) — keep the mean percentile for the join.
    return out.groupby(["day", "he"], as_index=False).agg(
        q=("q", "mean"), year=("year", "first")
    )


def _wquantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v, w = values[order], weights[order]
    cw = np.cumsum(w) - 0.5 * w
    return float(np.interp(q * w.sum(), cw, v))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    ap.add_argument("--rungs", type=int, default=5)
    args = ap.parse_args(argv)

    files, coverage = _day_files(args.years)
    print(f"parsing {len(files)} day files ...", flush=True)
    days = [d for d in (_parse_day(p) for p in files) if d is not None]
    offers = pd.concat(days, ignore_index=True)
    print(
        f"fast-start offer rows: {len(offers)} ({offers.asset_id.nunique()} assets)",
        flush=True,
    )

    gas = _load_algonquin_daily()
    base_hr = _ct_peaker_base_hr()
    offers["fuel"] = gas.reindex(offers["day"]).to_numpy()
    offers = offers[offers["fuel"] > 0]
    offers["mult"] = (offers["top_price"] / offers["fuel"]) / base_hr

    nl = _netload_pct(args.years)
    offers = offers.merge(nl, on=["day", "he"], how="left")
    n_unmatched = int(offers["q"].isna().sum())
    offers = offers.dropna(subset=["q"])

    edges = tuple(args.edges)
    n_bins = len(edges) + 1
    offers["bin"] = np.searchsorted(
        np.asarray(edges), offers["q"].to_numpy(), side="right"
    )

    # all-hours class p50 (per-asset median, cap-weighted): the ladder's floor.
    per_asset_all = offers.groupby("asset_id").agg(
        m=("mult", "median"), cap=("eco_max", "median")
    )
    body_p50 = _wquantile(
        per_asset_all["m"].to_numpy(), per_asset_all["cap"].to_numpy(), 0.50
    )

    cap_share = 1.0 / args.rungs
    qs = [(i + 0.5) * cap_share for i in range(args.rungs)]
    binned_ladder, summary_rows = [], []
    for b in range(n_bins):
        sub = offers[offers["bin"] == b]
        per_asset = sub.groupby("asset_id").agg(
            m=("mult", "median"), cap=("eco_max", "median")
        )
        if len(per_asset) < 5:  # degenerate bin: hold the body
            ladder = [[cap_share, body_p50] for _ in qs]
        else:
            v, w = per_asset["m"].to_numpy(), per_asset["cap"].to_numpy()
            ladder = [
                [cap_share, max(body_p50, round(_wquantile(v, w, q), 3))] for q in qs
            ]
        binned_ladder.append(ladder)
        summary_rows.append(
            {
                "bin": b,
                "n_assets": len(per_asset),
                "n_rows": len(sub),
                **{f"rung{i + 1}_mult": ladder[i][1] for i in range(args.rungs)},
                **{
                    f"rung{i + 1}_usd_at_hr{base_hr:.1f}_gas3": round(
                        ladder[i][1] * base_hr * 3.0, 1
                    )
                    for i in range(args.rungs)
                },
            }
        )

    out = {
        "_provenance": {
            "source": (
                "ISO-NE ISO Express Day-Ahead Energy Market historical offer "
                "data (hbdayaheadenergyoffer daily CSVs), delivery years "
                f"{args.years}"
            ),
            "method": (
                "per-asset median top-of-curve heat-rate multiplier of the "
                "fast-start population (Claim30 >= "
                f"{FAST_START_CLAIM30_FRAC} x EcoMax, ECONOMIC/MUST_RUN), "
                "capacity-weighted equal-capacity quantile rungs within "
                "net-load-percentile bins; rungs clamped >= all-hours p50; "
                "fuel = Algonquin Citygate daily (model series), base_HR = "
                "model NEISO CT_PEAKER cap-weighted"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 ISNE Demand "
                "- WND - SUN), forward-native"
            ),
            "netload_pct_edges": list(edges),
            "peak_ladder_qs": qs,
            "base_hr_mmbtu_mwh": round(base_hr, 3),
            "body_p50_mult": round(body_p50, 3),
            "day_coverage": coverage,
            "n_day_files_parsed": len(files),
            "n_rows_unmatched_netload": n_unmatched,
            "critical_days_verified": list(CRITICAL_DAYS),
        },
        "CT_PEAKER": {
            "base_hr": round(base_hr, 3),
            "peak_p50": round(body_p50, 3),
            "binned_ladder": binned_ladder,
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=1))
    pd.DataFrame(summary_rows).to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_JSON}")
    print(f"wrote {OUT_CSV}")
    print(pd.DataFrame(summary_rows).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
