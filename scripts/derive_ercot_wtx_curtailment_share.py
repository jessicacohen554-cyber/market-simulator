#!/usr/bin/env python
"""Derive the ERCOT West Texas Export corridor VRE curtailment-share driver.

Two products, from strictly separated sources:

1. **SHAPE** — ``data/raw/reference/ercot_wtx_curtailment_share.csv``: the measured
   West-corridor SCED congestion fraction (``data/clean/ercot-wtx-congestion``,
   curated by scripts/curate_ercot_wtx_congestion.py) binned by within-year
   net-load percentile decile x hour-of-day x season, pooled across the in-sample
   years. Reads ONLY measured congestion incidence and net-load — never the
   reported curtailment volume. Reproduces the measured binding-frequency
   distribution leave-one-year-out (the anti-residual gate / rule #23).

2. **LEVEL** — the per-tech depth coefficients printed as a paste-ready block for
   ``constants``/``ScenarioConfig``. A single scalar per tech converting congestion
   incidence into curtailed fraction, centred on the measured curtailment MW
   quantity (``HSL - delivered`` from data/raw/ercot-hsl) exactly as the
   RTOLCAP-forward ``deliv`` coefficient is centred on the measured reserve MW
   quantity. This is the ONE coefficient that reads the reported-curtailment
   aggregate; it is a stable structural constant (LOYO-validated below), not a
   per-year residual knob, and ``depth = 0`` is the zero-forcing ablation.

Net-load axis and season/hour-of-day axes are shared with the solve-time reader
(market_sim.data.curtailment_share) so the derived table and the LP consumer bin
identically.

Run ``python scripts/derive_ercot_wtx_curtailment_share.py`` for the report +
LOYO validation and to (re)write the reference CSV. Rule #23: re-derive only when
the source data updates (a new NP6-86 year or a rebuilt HSL parquet), never
because a price/backcast residual moved — cite the data change in the commit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402
from market_sim.data.curtailment_share import (  # noqa: E402
    SHARE_TABLE_NAME,
    hour_axes,
    net_load_decile,
)
from scripts.lib.clean_io import read_clean  # noqa: E402

IN_SAMPLE_YEARS = (2023, 2024, 2025)  # 2022 / H1-2026 are held-out (rule #22)
_SHARE_KEY = ["net_load_decile", "hour_of_day", "season"]


def _measured_net_load(year: int) -> np.ndarray:
    """System net-load (T,) = EIA-930 ERCOT demand - wind_hsl - solar_hsl.

    The SAME potential-based net-load convention the LP applies at solve time
    (fleet.apply_netload_drag_floors); only the RANK (decile) is consumed, so the
    measured vs model level offset is immaterial.
    """
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    dem = pd.read_parquet(
        paths.RAW_DIR / "eia-930-hourly" / "ERCO hourly.parquet",
        columns=["Local date", "Hour", "Demand"],
    )
    dem["ld"] = pd.to_datetime(dem["Local date"])
    dem = dem[
        (dem["ld"].dt.year == year)
        & ~((dem["ld"].dt.month == 2) & (dem["ld"].dt.day == 29))
    ].sort_values(["ld", "Hour"])
    demand = dem["Demand"].to_numpy()[:8760]
    if len(demand) < 8760:  # pad a short archive tail with the annual mean
        demand = np.pad(
            demand, (0, 8760 - len(demand)), constant_values=float(np.nanmean(demand))
        )
    return demand - hsl["wind_hsl_mw"].to_numpy() - hsl["solar_hsl_mw"].to_numpy()


def _reported_curtailment(year: int) -> dict[str, np.ndarray]:
    """Measured HSL potential and delivered wind/solar (the LEVEL anchor only)."""
    hsl = pd.read_parquet(
        paths.RAW_DIR / "ercot-hsl" / f"ercot_{year}_hsl_hourly.parquet"
    ).set_index("hour")
    return {
        "wind_hsl": hsl["wind_hsl_mw"].to_numpy(),
        "wind_gen": hsl["wind_gen_mw"].to_numpy(),
        "solar_hsl": hsl["solar_hsl_mw"].to_numpy(),
        "solar_gen": hsl["solar_gen_mw"].to_numpy(),
    }


def _year_frame(year: int) -> pd.DataFrame:
    """Per-hour (decile, hour_of_day, season, congestion_share) for one year."""
    cong = read_clean("ercot-wtx-congestion", iso="ERCOT", year=year)
    cong = cong.sort_values("hour")
    share = cong["congestion_frac"].to_numpy()
    nl = _measured_net_load(year)
    hod, season = hour_axes(len(share))
    return pd.DataFrame(
        {
            "net_load_decile": net_load_decile(nl),
            "hour_of_day": hod,
            "season": season,
            "congestion_share": share,
        }
    )


def build_share_table(years) -> pd.DataFrame:
    """Pool the given years into the (decile x hour x season) congestion table."""
    frames = [_year_frame(y) for y in years]
    pooled = pd.concat(frames, ignore_index=True)
    return (
        pooled.groupby(_SHARE_KEY)["congestion_share"]
        .mean()
        .reset_index()
        .sort_values(_SHARE_KEY, ignore_index=True)
    )


def _apply_table(table: pd.DataFrame, year: int) -> np.ndarray:
    """Look up each hour's congestion share from ``table`` for ``year``."""
    nl = _measured_net_load(year)
    hod, season = hour_axes(len(nl))
    key = pd.DataFrame(
        {"net_load_decile": net_load_decile(nl), "hour_of_day": hod, "season": season}
    )
    merged = key.merge(table, on=_SHARE_KEY, how="left")
    return np.nan_to_num(merged["congestion_share"].to_numpy(dtype=float), nan=0.0)


def _depth(table: pd.DataFrame, years, tech: str) -> float:
    """Level coefficient: reported curt fraction / potential-weighted mean share.

    Pooled over ``years``: ``depth = sum_y(HSL-GEN) / sum_y(HSL * share_hat)`` so a
    single scalar centres the driver on the measured curtailment MW quantity.
    """
    num = 0.0
    den = 0.0
    for y in years:
        rep = _reported_curtailment(y)
        share = _apply_table(table, y)
        hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
        num += float(np.clip(hsl - gen, 0, None).sum())
        den += float((hsl * share).sum())
    return num / den if den > 0 else 0.0


def _report() -> pd.DataFrame:
    print("=== SHAPE: measured West-corridor congestion frequency (rule #23) ===")
    full = build_share_table(IN_SAMPLE_YEARS)
    for tech in ("wind", "solar"):
        d = _depth(full, IN_SAMPLE_YEARS, tech)
        print(f"  pooled depth[{tech}] = {d:.4f}")

    print("\n=== LEAVE-ONE-YEAR-OUT validation ===")
    print("  (a) frequency-shape: train-table congestion_share vs held-out actual")
    print("  (b) curtailment-level: train depth x train share vs held-out reported")
    for hold in IN_SAMPLE_YEARS:
        train = [y for y in IN_SAMPLE_YEARS if y != hold]
        table = build_share_table(train)
        # (a) shape: correlate predicted vs actual per-hour congestion share
        pred_share = _apply_table(table, hold)
        actual = _year_frame(hold)["congestion_share"].to_numpy()
        shape_corr = np.corrcoef(pred_share, actual)[0, 1]
        shape_bias = pred_share.mean() - actual.mean()
        # (b) level, per tech
        line = []
        for tech in ("wind", "solar"):
            d = _depth(table, train, tech)
            rep = _reported_curtailment(hold)
            hsl, gen = rep[f"{tech}_hsl"], rep[f"{tech}_gen"]
            pred = d * (hsl * pred_share).sum() / hsl.sum()
            act = np.clip(hsl - gen, 0, None).sum() / hsl.sum()
            line.append(f"{tech}: pred={pred:.4f} act={act:.4f} (d_train={d:.4f})")
        print(
            f"  hold {hold}: shape corr={shape_corr:+.3f} bias={shape_bias:+.3f} | "
            + " | ".join(line)
        )
    return full


def main() -> None:
    """CLI: report + LOYO validation, and (re)write the reference share table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="Report + validate only; do not (re)write the reference CSV.",
    )
    args = ap.parse_args()
    full = _report()
    if args.no_write:
        return
    out = paths.RAW_DIR / "reference" / SHARE_TABLE_NAME
    full.to_csv(out, index=False)
    print(f"\nwrote {len(full)} (decile x hour x season) rows -> {out}")


if __name__ == "__main__":
    main()
