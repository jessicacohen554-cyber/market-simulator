#!/usr/bin/env python
"""Derive the SPP VRE curtailment-share driver (SPP-58).

SPP's 2-zone reduction (``SPP-North`` / ``SPP-South``, one 3,400 MW link)
collapses the *nodal* transmission that actually curtails SPP wind — the SPS /
Texas-Panhandle and western-Kansas / Oklahoma export pockets — into a single
pipe that almost never binds. The renewable bound SPP is armed with is the
delivered EIA-930 profile grossed up to an uncurtailed potential
(``renewable_bound_provenance`` = ``forecast_uncurtailed``), whose own stated
precondition is that the LP re-curtails the headroom endogenously. Measured on
the keeper ``2026-09-09-spp-52a-fossil-offer``'s committed hourly sidecars it
does not: re-curtailment is **0.26 / 0.22 / 0.17 %** in 2023 / 2024 / 2025
against a measured reference rate of 9.65 %.

This script supplies the SHAPE half of the reduced-form stand-in — the same
construction ``data/curtailment_share.py`` already carries for ERCOT's West
Texas Export corridor (WP-B), derived here from **SPP's own** market data
(rule 25 ``[R-ISO-SCOPE]``: nothing is transferred; ERCOT's table, its depths
and its corridor-zone attribution stay ERCOT's):

    ceiling_frac(t) = 1 - depth * congestion_share(net_load_decile(t),
                                                   hour_of_day(t), season(t))

1. **SHAPE** — ``data/raw/reference/spp_curtailment_share.csv``: the measured
   count of distinct SPP RTBM constraints in a BINDING state, per model hour,
   binned by within-year net-load percentile decile x hour-of-day x season and
   pooled across 2023-2025. Read from ``data/raw/spp-binding-constraints``
   (SPP's published RTBM binding-constraint archive, landed 2026-09-08). It
   reads ONLY measured binding incidence and measured net load — never a
   curtailment volume, never a price, never a backcast residual.

2. **LEVEL** — the per-tech ``depth`` coefficient, printed as a paste-ready
   block. One scalar centred on SPP's **published** measured curtailment
   quantity (``data/raw/reference/spp_wind_curtailment_annual.csv``, SPP MMU
   ASOM), exactly as ERCOT's depth is centred on its measured ``HSL -
   delivered``. ``depth = 0`` is the inert ablation.

**Why a binding COUNT and not a binding FRACTION.** The pooled union of "does
any constraint bind this interval" saturates in SPP: 91.0 % of 2024's 5-minute
intervals carry at least one binding constraint, so a fraction-of-intervals
share is nearly flat and encodes no shape. The *number* of simultaneously
binding constraints does discriminate, monotonically and with the physically
right sign — measured 2024, mean distinct binding constraints per hour by
net-load decile: 6.67 at the lowest-net-load decile falling to 4.42 at the
eighth. The count is rescaled onto [0, 1] by the table's own maximum cell,
which carries no free parameter: ``depth`` is fitted to the published
curtailment MW *after* the rescale, so any monotone rescaling of the shape is
absorbed exactly by ``depth`` and only the table's relative structure survives
into the LP.

**Clock.** The archive's ``Interval`` column is SPP local time WITH daylight
saving (the ``GMTIntervalEnd`` offset is 6 h in January and 5 h in July), while
the model dispatches on FIXED CST. Every timestamp here is therefore built from
``GMTIntervalEnd`` — interval end, so the interval START is
``GMTIntervalEnd - 5 min`` — shifted by a constant 6 h. This is the same clock
defect repaired for SPP's LMP sidecar in commit ``86e45462``; deriving off
``Interval`` would shift the whole summer half of the table by one hour.

Net-load, decile, hour-of-day and season axes are shared with the solve-time
reader (:mod:`market_sim.data.curtailment_share`) so the derived table and the
LP consumer bin identically.

Run ``python scripts/data/derive_spp_curtailment_share.py`` for the report and
to (re)write the reference CSV; ``--check`` re-derives and diffs against the
committed table without writing. Rule 23 ``[R-FROZEN-DERIVE]``: re-derive only
when the source data updates (a new RTBM archive year or a rebuilt EIA-930
frame), never because a residual moved — cite the data change in the commit.
"""

from __future__ import annotations

import argparse
import io
import logging
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config import paths as _paths  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.curtailment_share import (  # noqa: E402
    hour_axes,
    net_load_decile,
)

logger = logging.getLogger(__name__)

#: Source archive (SPP RTBM binding constraints, 5-minute).
ARCHIVE_DIR = _paths.RAW_DIR / "spp-binding-constraints"

#: Derived table written under ``data/raw/reference``.
SHARE_TABLE_NAME = "spp_curtailment_share.csv"

#: Years the archive covers completely.
DERIVE_YEARS = (2023, 2024, 2025)

#: The constraint states that count as congestion. ``ACTIVATED`` is a watch
#: state carrying no shadow price and is NOT congestion; ``BREACHED`` is
#: excluded because it is a violation state whose incidence is dominated by
#: modelling artefacts rather than by delivered curtailment.
BINDING_STATE = "BINDING"

#: Fixed-CST offset from GMT. SPP's market clock observes DST; the model does
#: not, so every timestamp is rebuilt from the GMT column at this constant.
CST_OFFSET_HOURS = 6

_TABLE_KEY = ["net_load_decile", "hour_of_day", "season"]


def _archive_members(year: int) -> list[Path]:
    """Return the archive zips covering ``year``, yearly file preferred."""
    yearly = ARCHIVE_DIR / f"RTBM-BC-YEARLY-{year}.csv.zip"
    if yearly.is_file():
        return [yearly]
    monthly = sorted(ARCHIVE_DIR.glob(f"RTBM-BC-MONTHLY-{year}??.csv.zip"))
    return list(monthly)


def _model_hour(gmt_end: pd.Series, year: int) -> np.ndarray:
    """Map GMT interval-END timestamps to the model's fixed-CST hour index.

    The model clock is 8,760 fixed-CST hours starting ``year-01-01 00:00``,
    with 29 February DROPPED in a leap year (the repo's non-leap convention).
    Returns an int array with ``-1`` for any interval outside the model year.
    """
    start_cst = gmt_end - pd.Timedelta(minutes=5) - pd.Timedelta(hours=CST_OFFSET_HOURS)
    year0 = pd.Timestamp(year=year, month=1, day=1)
    raw = ((start_cst - year0).dt.total_seconds() // 3600).astype("int64")
    # Drop 29 February: every hour at or after it shifts back 24.
    is_leap = (year % 4 == 0 and year % 100 != 0) or year % 400 == 0
    if is_leap:
        feb29 = int(
            (pd.Timestamp(year=year, month=2, day=29) - year0).total_seconds() // 3600
        )
        on_feb29 = (raw >= feb29) & (raw < feb29 + 24)
        raw = np.where(raw >= feb29 + 24, raw - 24, raw)
        raw = np.where(on_feb29, -1, raw)
    raw = np.asarray(raw, dtype="int64")
    return np.where((raw >= 0) & (raw < 8760), raw, -1)


def binding_count_by_hour(year: int) -> np.ndarray:
    """Distinct BINDING constraints per model hour for ``year``, shape ``(8760,)``.

    Counts constraint *instances* with a non-zero shadow price across the
    twelve 5-minute intervals in each model hour, so an hour in which three
    constraints bind for the whole hour scores 36 and an hour in which one
    binds for five minutes scores 1. Purely measured incidence.
    """
    members = _archive_members(year)
    if not members:
        raise SystemExit(f"SPP {year}: no archive member under {ARCHIVE_DIR}")
    counts = np.zeros(8760, dtype="float64")
    for member in members:
        with zipfile.ZipFile(member) as zf:
            for name in zf.namelist():
                if not name.lower().endswith(".csv"):
                    continue
                frame = pd.read_csv(
                    io.BytesIO(zf.read(name)),
                    usecols=["GMTIntervalEnd", "State", "Shadow Price"],
                    low_memory=False,
                )
                frame = frame[frame["State"].astype(str).str.strip() == BINDING_STATE]
                sp = pd.to_numeric(frame["Shadow Price"], errors="coerce").fillna(0.0)
                frame = frame[sp.abs() > 0.0]
                if frame.empty:
                    continue
                gmt = pd.to_datetime(
                    frame["GMTIntervalEnd"], format="%m/%d/%Y %H:%M:%S"
                )
                hours = _model_hour(gmt, year)
                hours = hours[hours >= 0]
                np.add.at(counts, hours, 1.0)
    return counts


def spp_net_load(year: int) -> np.ndarray:
    """SPP measured system net load ``(8760,)`` — the driver's own axis.

    ``demand - delivered wind - delivered solar``, all three off the ISO's own
    EIA-930 frame, the same clock the dispatch runs on. Uses DELIVERED variable
    generation (not the grossed-up potential) because the axis must be a
    property of the measured system, independent of any model configuration.
    """
    from market_sim.data.eia930.demand import load_demand
    from market_sim.data.renewables import load_eia_hourly_renewable_gen

    iso_config = get_iso_config("SPP")
    demand = load_demand("SPP", year, iso_config)
    net_load = np.asarray(demand, dtype=float).sum(axis=0)
    gen = load_eia_hourly_renewable_gen("SPP", year) or {}
    for fuel in ("wind", "solar"):
        series = gen.get(fuel)
        if series is not None and np.shape(series) == (8760,):
            net_load = net_load - np.asarray(series, dtype=float)
    return net_load


def build_share_table(years: tuple[int, ...] = DERIVE_YEARS) -> pd.DataFrame:
    """Build the pooled ``(decile, hour_of_day, season)`` congestion-share table.

    Each year contributes its own within-year net-load decile mapping (so the
    axis regenerates for a forward year rather than encoding a fixed MW level),
    the per-hour binding counts are pooled across years, and the pooled cell
    means are rescaled by the table's own maximum onto ``(0, 1]``.
    """
    frames = []
    for year in years:
        counts = binding_count_by_hour(year)
        net_load = spp_net_load(year)
        hod, season = hour_axes(8760)
        frames.append(
            pd.DataFrame(
                {
                    "year": year,
                    "net_load_decile": net_load_decile(net_load),
                    "hour_of_day": hod,
                    "season": season,
                    "binding_count": counts,
                }
            )
        )
    pooled = pd.concat(frames, ignore_index=True)
    table = (
        pooled.groupby(_TABLE_KEY, as_index=False)
        .agg(
            binding_count_mean=("binding_count", "mean"),
            n_hours=("binding_count", "size"),
        )
        .sort_values(_TABLE_KEY)
        .reset_index(drop=True)
    )
    peak = float(table["binding_count_mean"].max())
    if peak <= 0.0:
        raise SystemExit("SPP curtailment share: no binding incidence in the archive")
    table["congestion_share"] = table["binding_count_mean"] / peak
    return table[_TABLE_KEY + ["congestion_share", "binding_count_mean", "n_hours"]]


def report(table: pd.DataFrame) -> None:
    """Print the derived table's structure — the shape claim, measured."""
    print("\n=== SPP congestion share: mean by net-load decile ===")
    by_dec = table.groupby("net_load_decile").apply(
        lambda g: np.average(g["congestion_share"], weights=g["n_hours"]),
        include_groups=False,
    )
    for dec, val in by_dec.items():
        print(f"  decile {dec}: {val:.4f}")
    print(
        f"  monotone-decreasing in net load: "
        f"{bool(np.all(np.diff(by_dec.to_numpy()[:9]) < 0))} (deciles 0-8)"
    )
    print("\n=== SPP congestion share: mean by hour of day ===")
    by_hod = table.groupby("hour_of_day").apply(
        lambda g: np.average(g["congestion_share"], weights=g["n_hours"]),
        include_groups=False,
    )
    print("  " + " ".join(f"{v:.2f}" for v in by_hod))
    print(
        f"\n  cells: {len(table)} of {10 * 24 * 4} possible; "
        f"share range {table['congestion_share'].min():.4f} - "
        f"{table['congestion_share'].max():.4f}"
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: derive, report and write (or ``--check``) the table."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="re-derive and diff against the committed table; write nothing",
    )
    parser.add_argument("--years", type=int, nargs="+", default=list(DERIVE_YEARS))
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    table = build_share_table(tuple(args.years))
    report(table)

    out = _paths.REFERENCE_DIR / SHARE_TABLE_NAME
    if args.check:
        if not out.is_file():
            print(f"\n--check: {out} does not exist")
            return 1
        committed = pd.read_csv(out)
        merged = committed.merge(
            table, on=_TABLE_KEY, how="outer", suffixes=("_committed", "_derived")
        )
        delta = (
            merged["congestion_share_committed"] - merged["congestion_share_derived"]
        ).abs()
        worst = float(np.nanmax(delta.to_numpy())) if len(delta) else 0.0
        print(f"\n--check: {len(merged)} cells, max |delta| = {worst:.10f}")
        return 0 if worst < 1e-9 and not delta.isna().any() else 1

    out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(out, index=False)
    print(f"\nwrote {out} ({len(table)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
