"""Derive NYISO's POSITION-conditioned, SHAPE-ONLY measured offer surface (nyiso-245).

The measured object is a **within-unit, within-hour price RISE**::

    p_j  =  step_mw_j / uol_mw              own-curve POSITION, (0, 1]
    D_j  =  price_j   - price_1             own-curve RISE, $/MWh

``D`` carries no unit identity, no class, no fuel level and no market level: a
constant shift of a unit's entire submitted curve cancels **exactly**.

**Why that property is load-bearing HERE, and not merely convenient.** NYISO MIS
**P-27** is masked — no class, no fuel, no zone, no unit. nyiso-244 §4 built the
class bridge NYISO's masking allows (a cohort selected by NYISO's own published
10-Minute Non-Synchronized Reserve product) and **REFUTED it**: V1 scope passes at
0.043 but V2 MW 0.303 and V3 sorted-capacity fingerprint 1.328 fail their
pre-registered bars. A within-unit coordinate never asks what the masked gen *is*,
so masking cannot block it. This is MISO's own reasoning at
``derive_miso_offer_surface.py`` — *"Class-free by necessity, not by preference …
miso-138 built and REFUTED the offer-side class bridge"* — and nyiso-244 §4 is
NYISO's miso-138.

**And it defeats the level gap nyiso-244 §6 flagged.** The two NYISO fleets differ
by a near-constant **~9.4 GW** at the top of the curve (−9,422.6 MW in the missed
hours, −9,504.6 MW in ordinary ones): the model carries ~25.2 GW of internal
offered capacity where P-27 declares ~32.7 GW, because the model represents
renewables as LP decision variables and hydro/nuclear differently. A LEVEL
comparison between the two is therefore uninterpretable; a **within-unit rise** is
invariant to exactly that error.

**Rule 25 ``[R-ISO-SCOPE]``.** What is reused from MISO is the **method**, the
**population rules** and the mechanism family's **registered bin geometry** — never
a Δ value. Every number this script writes is measured on NYISO's own bid corpus
against NYISO's own delivered-gas series and NYISO's own measured net load.

**Rule 13 ``[R-MEASURED]``.** All three conditioning drivers exist in a forecast
year and respond to changed conditions: own-curve position, the hour's net-load
percentile **within its own year's distribution**, and the delivered-gas bin. The
surface is estimated by **POOLING 2022-2025** and applied identically to every
year — never a per-year surface, which would be a same-year measured-outcome pin.
Nothing measured here is an outcome: Δ is a **submitted offer**, not a cleared
price, a realised dispatch, or a residual.

**Rule 23 ``[R-FROZEN-DERIVE]``.** Both bin geometries are frozen in
``docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md`` §2, committed
at ``398f0437`` before any measurement, and are never re-tuned against a residual.

**Estimator.** Capacity-weighted MEDIAN of ``D`` per cell, weights = each step's
own MW width, read exactly off a weighted histogram on a 0.05 $/MWh grid — the
family's convention (median rather than mean or OLS: the caiso-153 attenuation
defect).

Usage::

    PYTHONPATH=.:src python3 scripts/data/derive_nyiso_offer_surface.py
    PYTHONPATH=.:src python3 scripts/data/derive_nyiso_offer_surface.py --self-test
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_nyiso_offer_surface")

ISO = "NYISO"
#: EIA-930 balancing-authority code for NYISO (the frame is "NYIS hourly.parquet").
BA_CODE = "NYIS"
YEARS: tuple[int, ...] = (2022, 2023, 2024, 2025)
#: P-27 publishes DAM and HAM. Only DAM is taken: it is the market whose offers
#: the model's day-ahead-like P1 pass represents, and it is the market nyiso-244
#: measured the object in.
MARKETS: tuple[str, ...] = ("DAM",)
HOURS = 8760
N_BLOCKS = 12

GENBIDS = REPO / "data" / "raw" / "nyiso-bid-data" / "genbids"
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT_DEFAULT = (
    REPO / "data" / "raw" / "_validation-source" / "nyiso_offer_surface_positional.json"
)

#: Own-curve position grid — the mechanism FAMILY's registered geometry
#: (``ScenarioConfig.miso_offer_surface_position_bins``), adopted unchanged.
#: A bin geometry is not a fitted value, and inventing NYISO's own would invite a
#: sweep. PRECOMMIT §2, frozen before measurement.
POSITION_BINS: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)
#: Registered cross-ISO net-load percentile geometry — five ISOs' surface fields
#: already carry it. NOT re-binned here.
NETLOAD_PCTS: tuple[float, ...] = (0.80, 0.90, 0.97)
#: Delivered-gas conditioning: terciles of NYISO's OWN pooled series. The one
#: NYISO-specific geometry, and it is a quantile of NYISO's own data, not a level.
GAS_QUANTILES: tuple[float, ...] = (1.0 / 3.0, 2.0 / 3.0)

#: Weighted-histogram grid for the median estimator, $/MWh.
DELTA_LO, DELTA_HI, DELTA_STEP = -500.0, 2000.0, 0.05

_MW_COLS = [f"Dispatch MW{i}" for i in range(1, N_BLOCKS + 1)]
_PX_COLS = [f"Dispatch $/MW{i}" for i in range(1, N_BLOCKS + 1)]
_SELF_COLS = [f"Self Commit MW{i}" for i in range(1, 5)]


def n_position_bins() -> int:
    """Number of own-curve position bins."""
    return len(POSITION_BINS) - 1


def n_state_bins() -> int:
    """Number of net-load state bins."""
    return len(NETLOAD_PCTS) + 1


def n_gas_bins() -> int:
    """Number of delivered-gas bins."""
    return len(GAS_QUANTILES) + 1


def n_delta_bins() -> int:
    """Number of histogram cells on the Δ grid."""
    return int(round((DELTA_HI - DELTA_LO) / DELTA_STEP))


def weighted_median_from_hist(hist: np.ndarray) -> float:
    """Capacity-weighted median Δ of one cell, read off its weighted histogram.

    Returns NaN for an empty cell. The estimate carries the declared
    :data:`DELTA_STEP` resolution.
    """
    total = float(hist.sum())
    if total <= 0.0:
        return float("nan")
    cum = np.cumsum(hist)
    idx = int(np.searchsorted(cum, total / 2.0, side="left"))
    idx = min(idx, hist.size - 1)
    return float(DELTA_LO + (idx + 0.5) * DELTA_STEP)


def net_load_by_year() -> dict[int, np.ndarray]:
    """NYISO measured net load per year, ``(8760,)`` MW, in local-hour order.

    Net load = EIA-930 metered ``Demand`` minus measured wind (``NG: WND``) and
    solar (``NG: SUN``) — all three measured drivers that exist in a forecast year
    (rule 13), never model output. Row *k* is local hour *k* of the year, the same
    clock the model's own hour index uses.
    """
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    out: dict[int, np.ndarray] = {}
    for year in YEARS:
        df = _eia_hourly_frame_filled(BA_CODE, year)
        if df is None:
            raise SystemExit(f"EIA-930 {BA_CODE} frame unavailable for {year}")
        dem = pd.to_numeric(df["Demand"], errors="coerce")
        wnd = pd.to_numeric(df.get("NG: WND", 0.0), errors="coerce").fillna(0.0)
        sun = pd.to_numeric(df.get("NG: SUN", 0.0), errors="coerce").fillna(0.0)
        nl = (dem - wnd - sun).interpolate().bfill().ffill().to_numpy(float)
        if nl.shape[0] != HOURS:
            raise SystemExit(f"{year}: net load length {nl.shape[0]} != {HOURS}")
        out[year] = nl
    return out


def gas_series_by_year() -> dict[int, np.ndarray]:
    """NYISO delivered gas per year, ``(8760,)`` $/MMBtu, in local-hour order.

    This is the KEEPER'S OWN resolved ``_gas_series`` — the identical object the
    solve-side applier passes in — cached by ``_nyiso245_fleet_cache``'s gas pass
    so the derive and the applier bin on one series and never on two independently
    built gas objects (rule 19 ``[R-ONE-MECH]`` in spirit: one gas series, one
    identification). Using the keeper's own resolution also introduces **zero new
    literals** (rules 5 / 24): no annual Henry-Hub level is written down here.
    """
    out: dict[int, np.ndarray] = {}
    for year in YEARS:
        path = CACHE / f"gas_{year}.npy"
        if not path.is_file():
            raise SystemExit(
                f"no cached delivered-gas series at {path} — run the gas pass of "
                "scripts/probes/_nyiso245_fleet_cache.py first"
            )
        out[year] = np.load(path).astype(float)
    return out


def build_state_maps() -> tuple[dict[int, np.ndarray], dict[int, np.ndarray], dict]:
    """Return per-year (state_bin, gas_bin) hour arrays plus the geometry metadata.

    The net-load percentile is taken **within each year's own distribution** — a
    relative, unit-free coordinate, so it transfers to a forecast year whose load
    level differs (and it is the same within-year ranking the solve-side applier
    performs). The gas bin uses **pooled** terciles, because a delivered gas price
    is directly comparable across years in a way a load level is not.
    """
    nl = net_load_by_year()
    gas = gas_series_by_year()

    pooled_gas = np.concatenate([gas[y] for y in YEARS])
    gas_edges = np.quantile(pooled_gas, GAS_QUANTILES)

    state_bin: dict[int, np.ndarray] = {}
    gas_bin: dict[int, np.ndarray] = {}
    for year in YEARS:
        edges = np.quantile(nl[year], NETLOAD_PCTS)
        state_bin[year] = np.searchsorted(edges, nl[year], side="right")
        gas_bin[year] = np.searchsorted(gas_edges, gas[year], side="right")

    meta = {
        "netload_source": f"EIA-930 {BA_CODE} Demand - NG:WND - NG:SUN, per year",
        "netload_percentile_basis": "WITHIN each year's own distribution",
        "gas_source": "keeper's own resolved _gas_series (cached), per year",
        "gas_bin_edges_usd_per_mmbtu": [round(float(x), 4) for x in gas_edges],
    }
    return state_bin, gas_bin, meta


def _std_hour(ts_utc: pd.DatetimeIndex, year: int) -> np.ndarray:
    """Map UTC stamps to the model's local-hour index (nyiso-243's verified map)."""
    from scripts.probes.nyiso243_offered_availability import _std_hour as _sh

    return _sh(ts_utc, year)


def read_month(year: int, month: int, market: str) -> pd.DataFrame | None:
    """Read one P-27 monthly archive, filtered to ``market``. ``None`` if absent."""
    path = GENBIDS / f"{year:04d}{month:02d}01biddata_genbids_csv.zip"
    if not path.exists():
        return None
    with zipfile.ZipFile(path) as z:
        raw = pd.read_csv(
            io.BytesIO(z.read(z.namelist()[0])), skipinitialspace=True, low_memory=False
        )
    raw.columns = [c.strip() for c in raw.columns]
    raw = raw[raw["Market"].astype(str).str.strip() == market]
    return None if raw.empty else raw


def prepare(raw: pd.DataFrame, year: int) -> tuple[pd.DataFrame, dict]:
    """Apply the family's population rules and compute ``(p, delta, w, hour)``.

    The rules are ``derive_miso_offer_surface.prepare``'s, **adopted unchanged**
    rather than re-invented: a re-invented exclusion set is a tuning channel
    (PRECOMMIT §2). Returns the surviving rows plus a census of every drop, so no
    exclusion is silent.
    """
    census = {"rows_in": int(len(raw))}

    uol = pd.to_numeric(raw["Upper Oper Limit"], errors="coerce").to_numpy(float)
    keep = uol > 0.0
    census["dropped_uol_nonpositive"] = int((~keep).sum())

    self_mw = (
        raw[_SELF_COLS].apply(pd.to_numeric, errors="coerce").fillna(0.0).max(axis=1)
    ).to_numpy(float)
    keep &= self_mw < uol
    census["dropped_fully_self_scheduled"] = int((~(self_mw < uol) & (uol > 0.0)).sum())

    ts = pd.to_datetime(
        raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S"
    )
    hour = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
    keep &= hour >= 0
    census["dropped_hour_out_of_year"] = int((hour < 0).sum())

    mw = raw[_MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    px = raw[_PX_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    emin = (
        pd.to_numeric(raw["Fixed Min Gen MW"], errors="coerce")
        .fillna(0.0)
        .clip(lower=0.0)
    ).to_numpy(float)

    mw, px, uol, emin, hour = (
        mw[keep],
        px[keep],
        uol[keep],
        emin[keep],
        hour[keep],
    )
    census["rows_after_row_filters"] = int(keep.sum())

    # Block j's predecessor MW; the first block's is the unit's own ecomin.
    prev = np.concatenate([emin[:, None], mw[:, :-1]], axis=1)
    prev = np.where(np.isfinite(prev), prev, np.nan)
    width = mw - prev
    base_px = px[:, 0][:, None]
    delta = px - base_px
    p = mw / uol[:, None]

    bad_width = np.isfinite(width) & (width < 0.0)
    census["dropped_nonincreasing_mw"] = int(bad_width.sum())
    ok = (
        np.isfinite(p)
        & (p > 0.0)
        & (p <= 1.0)
        & np.isfinite(width)
        & (width > 0.0)
        & np.isfinite(delta)
    )
    census["dropped_position_out_of_range_or_zero_width"] = int(
        (np.isfinite(mw) & ~ok).sum()
    )

    hour_col = np.repeat(hour[:, None], N_BLOCKS, axis=1)
    # The first block of every unit-hour is Delta == 0 by construction; it is
    # KEPT, exactly as the family's own population rules keep it. Its share of
    # weight is reported by :func:`single_block_census` rather than excluded here
    # (PRECOMMIT §3 G3c: reported at full magnitude, deliberately not a gate and
    # deliberately not an exclusion knob).
    out = pd.DataFrame(
        {
            "p": p[ok],
            "delta": delta[ok],
            "w": width[ok],
            "hour": hour_col[ok],
        }
    )
    census["rows_kept"] = int(len(out))
    return out, census


def single_block_census(raw: pd.DataFrame) -> dict:
    """G3c — the price-taker contamination, measured and reported, never excluded.

    P-27 is the whole NYCA internal fleet, so nuclear, run-of-river hydro and wind
    submit single-block price-taking curves whose Δ ≡ 0. Their weight can only pull
    Δ **down**, so the bias is conservative: it makes the mechanism weaker, never
    stronger. Reported so the reader can size it.
    """
    mw = raw[_MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    px = raw[_PX_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    nb = np.isfinite(mw).sum(axis=1)
    uol = pd.to_numeric(raw["Upper Oper Limit"], errors="coerce").to_numpy(float)
    flat = np.array(
        [
            bool(np.nanmax(r[np.isfinite(r)]) == np.nanmin(r[np.isfinite(r)]))
            if np.isfinite(r).any()
            else False
            for r in px
        ]
    )
    cap = np.where(np.isfinite(uol), uol, 0.0)
    tot = float(cap.sum()) or 1.0
    return {
        "unit_hours": int(len(raw)),
        "single_block_unit_hour_share": round(float((nb <= 1).mean()), 4),
        "single_block_capacity_share": round(float(cap[nb <= 1].sum() / tot), 4),
        "flat_curve_capacity_share": round(float(cap[flat].sum() / tot), 4),
    }


def accumulate(
    year: int,
    market: str,
    state_bin: np.ndarray,
    gas_bin: np.ndarray,
    hist: np.ndarray,
) -> dict:
    """Bin one (year, market) slice into ``hist`` in place; return its census."""
    census = {
        "rows_in": 0,
        "rows_kept": 0,
        "months_present": 0,
        "dropped_uol_nonpositive": 0,
        "dropped_fully_self_scheduled": 0,
        "dropped_hour_out_of_year": 0,
        "dropped_nonincreasing_mw": 0,
        "dropped_position_out_of_range_or_zero_width": 0,
    }
    contam: list[dict] = []
    pos_edges = np.asarray(POSITION_BINS, dtype=float)

    for month in range(1, 13):
        raw = read_month(year, month, market)
        if raw is None:
            continue
        census["months_present"] += 1
        contam.append(single_block_census(raw))
        rows, c = prepare(raw, year)
        for k, v in c.items():
            if k in census:
                census[k] += v
        if rows.empty:
            continue
        pb = np.clip(
            np.searchsorted(pos_edges[1:-1], rows["p"].to_numpy(float), side="right"),
            0,
            n_position_bins() - 1,
        )
        hr = rows["hour"].to_numpy(int)
        sb = state_bin[hr]
        gb = gas_bin[hr]
        db = np.clip(
            ((rows["delta"].to_numpy(float) - DELTA_LO) / DELTA_STEP).astype(int),
            0,
            n_delta_bins() - 1,
        )
        np.add.at(hist, (gb, sb, pb, db), rows["w"].to_numpy(float))

    if contam:
        uh = sum(c["unit_hours"] for c in contam) or 1
        census["contamination"] = {
            "single_block_unit_hour_share": round(
                sum(c["single_block_unit_hour_share"] * c["unit_hours"] for c in contam)
                / uh,
                4,
            ),
            "single_block_capacity_share": round(
                sum(c["single_block_capacity_share"] * c["unit_hours"] for c in contam)
                / uh,
                4,
            ),
            "flat_curve_capacity_share": round(
                sum(c["flat_curve_capacity_share"] * c["unit_hours"] for c in contam)
                / uh,
                4,
            ),
        }
    return census


def build(per_year: bool = False) -> dict:
    """Build the pooled artifact (and, for G3b only, the per-year ladders)."""
    state_bin, gas_bin, meta = build_state_maps()
    censuses: dict[str, dict] = {}
    surface: dict[str, dict] = {}
    per_year_top: dict[str, dict] = {}

    for market in MARKETS:
        hist = np.zeros(
            (n_gas_bins(), n_state_bins(), n_position_bins(), n_delta_bins()),
            dtype=float,
        )
        for year in YEARS:
            if per_year:
                yh = np.zeros_like(hist)
                censuses[f"{market}-{year}"] = accumulate(
                    year, market, state_bin[year], gas_bin[year], yh
                )
                hist += yh
                # G3b reads the TOP position bin across state bins, pooled over gas.
                per_year_top[str(year)] = {
                    "delta_by_state_bin_top_position": [
                        round(
                            weighted_median_from_hist(
                                yh[:, s, n_position_bins() - 1, :].sum(axis=0)
                            ),
                            4,
                        )
                        for s in range(n_state_bins())
                    ],
                    "weight_by_state_bin_top_position_mw": [
                        round(float(yh[:, s, n_position_bins() - 1, :].sum()), 1)
                        for s in range(n_state_bins())
                    ],
                }
            else:
                censuses[f"{market}-{year}"] = accumulate(
                    year, market, state_bin[year], gas_bin[year], hist
                )
            log.info("%s %d binned", market, year)

        surface[market] = {
            "ladder": [
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
        }

    art = {
        "_provenance": {
            "session": "nyiso-245",
            "precommit": (
                "docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md"
            ),
            "precommit_sha": "5cbf4fef",
            "precommit_sha_prerebase": "398f0437",
            "object": (
                "within-unit own-curve price RISE (Delta = price_j - price_1), "
                "SHAPE ONLY"
            ),
            "source": (
                "NYISO MIS P-27 masked SUBMITTED generator bid data "
                "(YYYYMM01biddata_genbids_csv.zip), full-year 2022-2025, DAM; "
                "cleared awards never read (rule 13)"
            ),
            "pooling": "2022-2025 POOLED; never per-year",
            "estimator": "capacity-weighted median, weights = step MW width",
            "delta_resolution_usd_per_mwh": DELTA_STEP,
            "position_bins": list(POSITION_BINS),
            "netload_pcts": list(NETLOAD_PCTS),
            "gas_quantiles": list(GAS_QUANTILES),
            **meta,
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
    if per_year:
        art["per_year_top_position"] = per_year_top
    return art


def self_test() -> None:
    """Synthetic-corpus shape self-test — run BEFORE the artifact is trusted.

    Builds a 3-unit x 48-hour corpus with a KNOWN answer, checks the binning
    machinery recovers it, then checks the **level-invariance** property the whole
    mechanism rests on: shifting every unit's entire curve by a constant must leave
    every Δ bit-identical.
    """
    rng = np.random.default_rng(0)
    base = pd.Timestamp("2022-06-01 00:00")
    recs = []
    for unit, (emin, emax, p0, slope) in enumerate(
        [(10.0, 100.0, 20.0, 40.0), (50.0, 500.0, 25.0, 10.0), (5.0, 50.0, 30.0, 80.0)]
    ):
        for h in range(48):
            row = {
                "Masked Gen ID": unit,
                "Date Time": (base + pd.Timedelta(hours=h))
                .strftime("%d%b%Y:%H:%M:%S")
                .upper(),
                "Market": "DAM",
                "Upper Oper Limit": emax,
                "Fixed Min Gen MW": emin,
            }
            for j in range(N_BLOCKS):
                if j < 4:
                    frac = (j + 1) / 4.0
                    row[f"Dispatch MW{j + 1}"] = emax * frac
                    row[f"Dispatch $/MW{j + 1}"] = p0 + slope * frac
                else:
                    row[f"Dispatch MW{j + 1}"] = np.nan
                    row[f"Dispatch $/MW{j + 1}"] = np.nan
            for j in range(4):
                row[f"Self Commit MW{j + 1}"] = np.nan
            recs.append(row)
    raw = pd.DataFrame(recs)

    rows, census = prepare(raw, 2022)
    assert census["rows_kept"] > 0, census
    # T-1: at the top of its own curve every unit's Delta is slope * (1 - 1/4).
    top = rows[rows["p"] > 0.99]
    expect = {40.0 * 0.75, 10.0 * 0.75, 80.0 * 0.75}
    got = set(np.round(top["delta"].unique(), 6))
    assert got == expect, f"T-1 top-of-curve Delta {got} != {expect}"

    # T-2: LEVEL INVARIANCE. Shift every unit's whole curve by a constant.
    shifted = raw.copy()
    for j in range(1, N_BLOCKS + 1):
        shifted[f"Dispatch $/MW{j}"] = shifted[f"Dispatch $/MW{j}"] + 137.5
    rows2, _ = prepare(shifted, 2022)
    assert np.allclose(rows["delta"].to_numpy(), rows2["delta"].to_numpy()), (
        "T-2 level invariance FAILED — Delta moved under a constant curve shift"
    )

    # T-3: a single-block price taker contributes Delta == 0 and nothing else.
    flat = raw[raw["Masked Gen ID"] == 0].copy()
    for j in range(2, N_BLOCKS + 1):
        flat[f"Dispatch MW{j}"] = np.nan
        flat[f"Dispatch $/MW{j}"] = np.nan
    flat["Dispatch MW1"] = flat["Upper Oper Limit"]
    rows3, _ = prepare(flat, 2022)
    assert np.allclose(rows3["delta"].to_numpy(), 0.0), "T-3 price taker Delta != 0"
    assert rng is not None
    log.info("self-test PASSED (T-1 recovery, T-2 level invariance, T-3 price taker)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument(
        "--per-year",
        action="store_true",
        help="also emit per-year top-position ladders (PRECOMMIT G3b only)",
    )
    args = ap.parse_args()

    if args.self_test:
        self_test()
        return

    art = build(per_year=args.per_year)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(art, indent=1) + "\n")
    log.info("wrote %s", args.out)

    lad = art["markets"]["DAM"]["ladder"]
    print("\npooled Delta ($/MWh), gas bin 2 (highest tercile):")
    print(
        f"{'state':>6s} "
        + " ".join(f"{POSITION_BINS[q]:>7.2f}" for q in range(n_position_bins()))
    )
    for s in range(n_state_bins()):
        print(
            f"{s:>6d} "
            + " ".join(f"{lad[2][s][q][1]:7.2f}" for q in range(n_position_bins()))
        )


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
