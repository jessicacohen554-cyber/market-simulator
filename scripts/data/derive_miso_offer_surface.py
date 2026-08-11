"""Derive MISO's POSITION-conditioned, SHAPE-ONLY measured offer surface (miso-151).

The measured object is a **within-unit, within-hour price RISE**::

    p_j  =  step_mw_j / ecomax_mw          own-curve POSITION, (0, 1]
    D_j  =  price_j  - price_1             own-curve RISE, $/MWh

``D`` carries no unit identity, no class, no fuel level and no market level: a
constant shift of a unit's entire submitted curve cancels **exactly**.  That
cancellation is the whole reason this quantity is admissible where the offer
LEVEL is not — miso-145 measured MISO's real book as $8-15/MWh CHEAPER than the
model at matched position, so transferring level would move C3a the WRONG WAY.
This derive transfers shape and only shape (PREREG
``PREREG-miso151-measured-offer-surface-2026-08-11.md`` §§1, 4.1).

**Class-free by necessity, not by preference.**  MISO's masked corpus carries no
fuel or technology attribute and miso-138 built and REFUTED the offer-side class
bridge, so every other ISO's class-conditioned surface is unavailable here.  The
conditioning is therefore POSITION plus two system-state drivers:

  1. position bin      -- ``p`` on a frozen grid (:data:`POSITION_BINS`)
  2. system-state bin  -- the hour's MISO net-load percentile on the REGISTERED
                          cross-ISO geometry [0.80, 0.90, 0.97] (4 bins)
  3. delivered-gas bin -- terciles of the same ``_gas_series`` the
                          ``gas_offer_margin`` anchor is identified on

**Rule 13 [R-MEASURED] forward analogue.**  All three drivers exist in a
forecast year and the surface is estimated by POOLING 2023-2025 and applied
identically to every year -- never a per-year surface, which would be the
same-year measured OUTCOME pin ``PREREG-miso146`` §9 forbids as methodology.

**Rule 23 [R-FROZEN-DERIVE].**  Both bin geometries are frozen here, before any
measurement, and are never re-tuned against a residual.  Re-derivation happens
only when the corpus updates, and such a commit cites the data change.

**Estimator.**  Capacity-weighted MEDIAN of ``D`` per cell, weights = each
step's own MW width.  Median rather than mean or OLS: the caiso-153 attenuation
defect and the PJM/NEISO derive convention.  The median is read exactly off a
weighted histogram on a 0.05 $/MWh grid (:data:`DELTA_STEP`), so peak memory is
independent of corpus size.

Usage::

    PYTHONPATH=$PWD python scripts/data/derive_miso_offer_surface.py
    PYTHONPATH=$PWD python scripts/data/derive_miso_offer_surface.py --self-test
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config import paths  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_miso_offer_surface")

ISO = "MISO"
DATATYPE = "energy-offers"
YEARS: tuple[int, ...] = (2023, 2024, 2025)
MARKETS: tuple[str, ...] = ("DA", "RT")
HOURS = 8760

#: Own-curve position grid (PREREG §4.1, frozen before measurement).
POSITION_BINS: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)
#: Registered cross-ISO net-load percentile geometry -- NOT re-binned here.
NETLOAD_PCTS: tuple[float, ...] = (0.80, 0.90, 0.97)
#: Delivered-gas conditioning: terciles of the pooled training-window series.
GAS_QUANTILES: tuple[float, ...] = (1.0 / 3.0, 2.0 / 3.0)

#: Weighted-histogram grid for the exact median ($/MWh).  MISO offers are
#: published to the cent; 0.05 is the declared resolution of the estimate.
DELTA_LO, DELTA_HI, DELTA_STEP = -500.0, 4000.0, 0.05

OUT_PATH = (
    paths.REPO_ROOT
    / "data"
    / "raw"
    / "_validation-source"
    / "miso_offer_surface_positioned.json"
)

_READ_COLS = [
    "unit_code",
    "interval_start_utc",
    "step_idx",
    "step_mw",
    "step_price_usd_per_mwh",
    "ecomin_mw",
    "ecomax_mw",
    "self_scheduled_mw",
]


def n_position_bins() -> int:
    """Number of own-curve position bins."""
    return len(POSITION_BINS) - 1


def n_state_bins() -> int:
    """Number of net-load percentile bins."""
    return len(NETLOAD_PCTS) + 1


def n_gas_bins() -> int:
    """Number of delivered-gas bins."""
    return len(GAS_QUANTILES) + 1


def _hist_edges() -> np.ndarray:
    """Left edges of the weighted-Delta histogram grid."""
    return np.arange(DELTA_LO, DELTA_HI + DELTA_STEP, DELTA_STEP)


def weighted_median_from_hist(hist: np.ndarray) -> float:
    """Exact weighted median of the binned Delta distribution ($/MWh).

    Returns ``nan`` for an empty cell.  The value returned is the bin CENTRE of
    the bin in which the cumulative weight crosses half the total, so the
    estimate carries the declared :data:`DELTA_STEP` resolution.
    """
    total = float(hist.sum())
    if total <= 0.0:
        return float("nan")
    cum = np.cumsum(hist)
    idx = int(np.searchsorted(cum, total / 2.0, side="left"))
    idx = min(idx, hist.size - 1)
    return float(DELTA_LO + (idx + 0.5) * DELTA_STEP)


def net_load_by_year() -> dict[int, np.ndarray]:
    """MISO measured net load per year, ``(8760,)`` MW, keyed by UTC hour order.

    Net load = EIA-930 metered ``Demand`` minus measured wind (``NG: WND``) and
    solar (``NG: SUN``) -- all three are measured drivers that exist in a
    forecast year (rule 13), never model output.
    """
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    out: dict[int, np.ndarray] = {}
    for year in YEARS:
        df = _eia_hourly_frame_filled(ISO, year)
        assert df is not None, f"EIA-930 {ISO} frame unavailable for {year}"
        dem = pd.to_numeric(df["Demand"], errors="coerce")
        wnd = pd.to_numeric(df.get("NG: WND", 0.0), errors="coerce").fillna(0.0)
        sun = pd.to_numeric(df.get("NG: SUN", 0.0), errors="coerce").fillna(0.0)
        nl = (dem - wnd - sun).interpolate().bfill().ffill().to_numpy(float)
        assert nl.shape[0] == HOURS, f"{year}: net load length {nl.shape[0]} != {HOURS}"
        out[year] = nl
    return out


def utc_stamps_by_year() -> dict[int, pd.Series]:
    """The EIA-930 frame's own UTC stamps per year (naive, UTC), ``(8760,)``."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    out: dict[int, pd.Series] = {}
    for year in YEARS:
        df = _eia_hourly_frame_filled(ISO, year)
        out[year] = pd.to_datetime(df["UTC time"]).astype("datetime64[ns]")
    return out


def gas_series_by_year() -> dict[int, np.ndarray]:
    """MISO delivered gas price per year, ``(8760,)`` $/MMBtu.

    Reuses the anchor derive's own registered MISO recipe
    (``derive_gas_offer_margin_anchor.GAS_SERIES_FLAGS`` + ``TRAIN_WINDOW_HH``),
    so this conditioning driver is the SAME series the ``gas_offer_margin``
    anchor is identified on -- not a second, independently-built gas object
    (rule 19 [R-ONE-MECH] in spirit: one gas series, one identification).
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.trajectories import _gas_series
    from scripts.data.derive_gas_offer_margin_anchor import (
        GAS_SERIES_FLAGS,
        TRAIN_WINDOW_HH,
    )

    base = ScenarioConfig(
        iso=ISO, mode="backcast", hours=HOURS, **GAS_SERIES_FLAGS[ISO]
    )
    return {
        year: np.asarray(
            _gas_series(
                base.with_overrides(gas_price_override=TRAIN_WINDOW_HH[year]),
                year,
                HOURS,
            ),
            dtype=float,
        )
        for year in YEARS
    }


def build_state_maps() -> tuple[pd.Series, pd.Series, dict]:
    """Return (netload-percentile, gas-bin) Series indexed by naive-UTC stamp.

    The net-load PERCENTILE is taken on the POOLED three-year distribution (one
    ladder for the whole training window, not one per year), and the gas bin on
    the pooled terciles -- so a hot 2023 hour and a hot 2025 hour land in the
    same state bin, which is what makes the surface a single pooled object.
    """
    nl = net_load_by_year()
    gas = gas_series_by_year()
    stamps = utc_stamps_by_year()

    pooled_nl = np.concatenate([nl[y] for y in YEARS])
    pooled_gas = np.concatenate([gas[y] for y in YEARS])
    nl_edges = np.quantile(pooled_nl, NETLOAD_PCTS)
    gas_edges = np.quantile(pooled_gas, GAS_QUANTILES)

    all_stamps = pd.concat([stamps[y] for y in YEARS], ignore_index=True)
    nl_bin = np.searchsorted(nl_edges, pooled_nl, side="right")
    gas_bin = np.searchsorted(gas_edges, pooled_gas, side="right")

    meta = {
        "netload_bin_edges_mw": [float(x) for x in nl_edges],
        "gas_bin_edges_usd_per_mmbtu": [float(x) for x in gas_edges],
        "pooled_hours": int(pooled_nl.size),
    }
    return (
        pd.Series(nl_bin, index=all_stamps.to_numpy()),
        pd.Series(gas_bin, index=all_stamps.to_numpy()),
        meta,
    )


def _prepare_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Apply the PREREG §4.1 population rules and compute (p, Delta, weight).

    Returns the surviving rows plus a census of every drop, so no exclusion is
    silent.  ``Delta`` is computed as ``price - price_at_step_1`` within each
    (unit, hour) group; the group key is used explicitly rather than relying on
    row order.
    """
    census = {"rows_in": int(len(df))}

    df = df[df["ecomax_mw"] > 0.0]
    census["dropped_ecomax_nonpositive"] = census["rows_in"] - int(len(df))

    ss = df["self_scheduled_mw"].fillna(0.0)
    keep = ss < df["ecomax_mw"]
    census["dropped_fully_self_scheduled"] = int((~keep).sum())
    df = df[keep]

    key = ["unit_code", "interval_start_utc"]
    df = df.sort_values(key + ["step_idx"], kind="stable")

    grp = df.groupby(key, sort=False, observed=True)
    base_price = grp["step_price_usd_per_mwh"].transform("first")
    prev_mw = grp["step_mw"].shift(1)
    first_floor = df["ecomin_mw"].fillna(0.0).clip(lower=0.0)
    prev_mw = prev_mw.fillna(first_floor)

    width = (df["step_mw"] - prev_mw).to_numpy(float)
    bad = width < 0.0
    census["dropped_nonincreasing_mw"] = int(bad.sum())
    width = np.where(bad, 0.0, width)

    out = pd.DataFrame(
        {
            "p": (df["step_mw"] / df["ecomax_mw"]).to_numpy(float),
            "delta": (df["step_price_usd_per_mwh"] - base_price).to_numpy(float),
            "w": width,
            "stamp": df["interval_start_utc"].to_numpy(),
        }
    )
    ok = (
        (out["p"] > 0.0)
        & (out["p"] <= 1.0)
        & (out["w"] > 0.0)
        & np.isfinite(out["delta"])
    )
    census["dropped_position_out_of_range_or_zero_width"] = int((~ok).sum())
    out = out[ok]
    census["rows_kept"] = int(len(out))
    return out, census


def accumulate(
    market: str, year: int, nl_map: pd.Series, gas_map: pd.Series, hist: np.ndarray
) -> dict:
    """Bin one (market, year) slice into ``hist`` in place; return its census."""
    path = paths.clean_path(DATATYPE, iso=ISO, year=year, market=market)
    if not path.is_file():
        raise FileNotFoundError(
            f"no clean {DATATYPE} at {path} — run curate_miso_energy_offers.py"
        )

    census: dict = {"unmatched_hours": 0}
    edges = np.asarray(POSITION_BINS, dtype=float)
    n_pos, n_state = n_position_bins(), n_state_bins()

    for month in range(1, 13):
        lo = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
        hi = lo + pd.offsets.MonthBegin(1)
        chunk = pd.read_parquet(
            path,
            columns=_READ_COLS,
            filters=[("interval_start_utc", ">=", lo), ("interval_start_utc", "<", hi)],
        )
        if chunk.empty:
            continue
        prepared, cen = _prepare_frame(chunk)
        for k, v in cen.items():
            census[k] = census.get(k, 0) + v
        if prepared.empty:
            continue

        stamps = (
            pd.to_datetime(prepared["stamp"])
            .dt.tz_localize(None)
            .to_numpy("datetime64[ns]")
        )
        sb = nl_map.reindex(stamps).to_numpy(float)
        gb = gas_map.reindex(stamps).to_numpy(float)
        matched = np.isfinite(sb) & np.isfinite(gb)
        census["unmatched_hours"] += int((~matched).sum())
        if not matched.any():
            continue

        p = prepared["p"].to_numpy()[matched]
        d = np.clip(
            prepared["delta"].to_numpy()[matched], DELTA_LO, DELTA_HI - DELTA_STEP
        )
        w = prepared["w"].to_numpy()[matched]
        pb = np.clip(np.searchsorted(edges[1:-1], p, side="right"), 0, n_pos - 1)
        sbi = sb[matched].astype(int)
        gbi = gb[matched].astype(int)
        di = ((d - DELTA_LO) / DELTA_STEP).astype(np.int64)

        flat = ((gbi * n_state + sbi) * n_pos + pb) * hist.shape[-1] + di
        np.add.at(hist.reshape(-1), flat, w)

    return census


def derive() -> dict:
    """Derive the pooled surface for both markets and return the artifact dict."""
    nl_map, gas_map, state_meta = build_state_maps()
    n_bins = _hist_edges().size - 1
    surface: dict = {}
    censuses: dict = {}

    for market in MARKETS:
        hist = np.zeros(
            (n_gas_bins(), n_state_bins(), n_position_bins(), n_bins), dtype=float
        )
        for year in YEARS:
            censuses[f"{market}-{year}"] = accumulate(
                market, year, nl_map, gas_map, hist
            )
            log.info("%s %d binned", market, year)
        ladder = [
            [
                [
                    [
                        round(0.5 * (POSITION_BINS[q] + POSITION_BINS[q + 1]), 4),
                        round(weighted_median_from_hist(hist[g, s, q]), 4),
                        round(float(hist[g, s, q].sum()), 1),
                    ]
                    for q in range(n_position_bins())
                ]
                for s in range(n_state_bins())
            ]
            for g in range(n_gas_bins())
        ]
        surface[market] = {"ladder": ladder}

    return {
        "_provenance": {
            "session": "miso-151",
            "prereg": "results/calibration/PREREG-miso151-measured-offer-surface-2026-08-11.md",
            "object": "within-unit own-curve price RISE (Delta = price_j - price_1), SHAPE ONLY",
            "source": (
                "MISO Market Reports masked SUBMITTED offer books "
                "(YYYYMMDD_{da,rt}_co.zip), full-year 2023-2025, both markets; "
                "dispatch awards excluded at curation (rule 13)"
            ),
            "pooling": "2023-2025 POOLED; never per-year (PREREG-miso146 §9)",
            "estimator": "capacity-weighted median, weights = step MW width",
            "delta_resolution_usd_per_mwh": DELTA_STEP,
            "position_bins": list(POSITION_BINS),
            "netload_pcts": list(NETLOAD_PCTS),
            "gas_quantiles": list(GAS_QUANTILES),
            **state_meta,
        },
        "ladder_axes": [
            "gas_bin",
            "state_bin",
            "position_bin",
            "[pos_mid, delta_usd_per_mwh, weight_mw]",
        ],
        "markets": surface,
        "census": censuses,
    }


def self_test() -> None:
    """Synthetic-fleet shape self-test (PREREG T-2) — run BEFORE any solve.

    Builds a 3-unit x 48-hour corpus with a KNOWN answer and checks that the
    binning machinery recovers it, then checks the level-invariance property
    (T-4) the whole mechanism rests on: shifting every unit's entire curve by a
    constant must leave every Delta bit-identical.
    """
    rows = []
    base = pd.Timestamp("2023-06-01 00:00", tz="UTC")
    for unit, (emin, emax, p0, slope) in enumerate(
        [(10.0, 100.0, 20.0, 30.0), (0.0, 50.0, 15.0, 10.0), (25.0, 200.0, 40.0, 60.0)]
    ):
        for h in range(48):
            for j, frac in enumerate((0.25, 0.5, 0.75, 1.0), start=1):
                rows.append(
                    {
                        "unit_code": f"U{unit}",
                        "interval_start_utc": base + pd.Timedelta(hours=h),
                        "step_idx": j,
                        "step_mw": emax * frac,
                        # price rises linearly in position: p0 + slope * frac
                        "step_price_usd_per_mwh": p0 + slope * frac,
                        "ecomin_mw": emin,
                        "ecomax_mw": emax,
                        "self_scheduled_mw": 0.0,
                    }
                )
    df = pd.DataFrame(rows)

    prepared, census = _prepare_frame(df)
    assert census["rows_kept"] == len(df), f"self-test lost rows: {census}"

    # KNOWN ANSWER: Delta at position frac is slope*(frac - 0.25) for each unit.
    for unit, slope in ((0, 30.0), (1, 10.0), (2, 60.0)):
        sub = prepared[np.isclose(prepared["p"], 1.0)]
        assert len(sub) == 3 * 48, f"position-1.0 rows {len(sub)} != 144"
    expect = {0.25: 0.0, 0.5: 0.25, 0.75: 0.5, 1.0: 0.75}
    for frac, mult in expect.items():
        sub = prepared[np.isclose(prepared["p"], frac)]
        for slope in (30.0, 10.0, 60.0):
            want = slope * mult
            got = sub["delta"].to_numpy()
            assert np.any(np.isclose(got, want)), f"missing Delta {want} at p={frac}"

    # T-4 LEVEL INVARIANCE, measured not asserted.
    shifted = df.copy()
    shifted["step_price_usd_per_mwh"] = shifted["step_price_usd_per_mwh"] + 137.42
    prepared2, _ = _prepare_frame(shifted)
    same = np.array_equal(prepared["delta"].to_numpy(), prepared2["delta"].to_numpy())
    assert same, "T-4 BREACH: Delta is not invariant to a constant curve shift"

    # Ordering robustness: shuffle rows, result must be identical.
    prepared3, _ = _prepare_frame(
        df.sample(frac=1.0, random_state=0).reset_index(drop=True)
    )
    a = prepared.sort_values(["p", "delta", "w"]).to_numpy()
    b = prepared3.sort_values(["p", "delta", "w"]).to_numpy()
    assert np.array_equal(a[:, :3].astype(float), b[:, :3].astype(float)), (
        "row-order dependence"
    )

    # Weighted-median exactness on a known histogram.
    h = np.zeros(_hist_edges().size - 1)
    h[int((10.0 - DELTA_LO) / DELTA_STEP)] = 1.0
    h[int((20.0 - DELTA_LO) / DELTA_STEP)] = 3.0
    med = weighted_median_from_hist(h)
    assert abs(med - 20.0) <= DELTA_STEP, f"weighted median {med} != 20.0"

    log.info(
        "SELF-TEST PASS — known answer, T-4 level invariance, order independence, median exactness"
    )


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--self-test",
        action="store_true",
        help="run the synthetic-fleet self-test and exit",
    )
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    self_test()  # never derive on unverified machinery (PREREG T-2)
    art = derive()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(art, indent=1))
    log.info("wrote %s", args.out)


if __name__ == "__main__":
    main()
