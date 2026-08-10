"""Derive the ERCOT offline fast-start pool offer ladder + pool share.

The ERCOT-88 apply artifact for the §6.2 mechanism of
``docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md`` (charter §9)
— ``ScenarioConfig.ercot_faststart_pool_offer``. The ERCOT-87 measurement
adjudicated that the actual $150-500 moderate-tightness band prices on the
**offline startable CT pool** (``Telemetered Resource Status`` OFFQS/OFFNS:
full SCED curves disclosed, SCED-startable intra-hour), not on any online
spare or unmitigated-CC surface. This derive promotes that measurement to a
model input, from the NP3-965 60-Day SCED Gen Resource parquets on disk —
per year, the full-year publication-month corpus when it majority-covers the
delivery year (2023, via the wall derive's ``_sced_source_files``), else the
legacy sample-day extracts (2024/2025):

* Pool rows: resources of the block's class telemetered OFFQS or OFFNS —
  ``CT`` (SCGT90/SCLE90, the ERCOT-88 fast-start pool) and, since ERCOT-176,
  ``CC`` (CCGT90/CCLE90, the SLOW-START tier of the offline-increment
  re-pricing, ``ScenarioConfig.ercot_offline_commit_offer``). Each class is
  measured on its own conduct against its own live capability; the
  construction is otherwise identical, so the CT blocks are byte-identical
  across the CC extension. ST_GAS is deliberately excluded (rule 19 + the
  ERCOT-151 §3 condition: the steam lane is `R` from ERCOT-91).
* **Above-LSL startable increment only** (charter §8.2 caveat c): per
  interval-resource, segment the SCED2 (as-dispatched) curve between
  ``max(LSL, 0)`` and ``min(step MW, HASL)`` — the below-LSL min-gen curve
  bottoms (negative prices) never enter the ladder.
* Per (year x net-load-percentile bin), on the SAME bin edges as the DAM/RT
  wall artifacts (imported; the apply seam asserts agreement):
  - ``ladder``: MW-weighted quantiles of segment price as effective-HR
    multiplier (price / delivered-gas day, clipped to HCAP) — the wall
    convention, so the apply-time target = mult x gas_day.
  - ``pool_frac``: interval-mean of (pool above-LSL startable MW / CT-class
    live capability MW), where live = sum of HSL over non-OUT CT rows — the
    same only-OUT-is-out convention as the measured DAM availability
    (``derive_ercot_thermal_dam_availability.py``), so the share maps onto
    exactly the capacity the availability overlay leaves in the LP. The apply
    seam offers the TOP ``pool_frac`` of the class curve at the ladder
    (boundary ``1 - pool_frac`` in within-plant share coordinates).

Provenance / admissibility (CLAUDE.md rules 12/13/14): every quantity is an
ex-ante posted offer or a telemetered status; the driver is the year's own
net-load percentile (forward-native); zero fitted scalars; the eligibility
gate at apply time is unit physics (min-down <= 2 h), never a class tuple.
The artifact is **YEAR-SCOPED**: no pooled fallback — a year absent from the
artifact gets NO pool leg (the wall basis is retained byte-identical), and a
2024/2025-derived ladder remains barred from 2023's post-Uri conservative-ops
regime (the RT wall's own bar): 2023 gets its OWN block from its own conduct
(the ERCOT-105 owner authorization + the ERCOT-151 §4 corpus re-upload of
2026-08-03).

Coverage is DISCLOSED, never silently capped: per-(year x bin) interval/day
counts and mean pool MW are recorded, so a thin bin (2024/2025 are scoped
sample days; the Jan-2024 winter cluster is not in that basis) is visible at
the artifact level.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits
must cite the data change.

Usage::

    python scripts/data/derive_ercot_faststart_pool.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_faststart_pool_condbinned.json]
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    HOURS,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
)

DEFAULT_OUT = CALIBRATION_DIR / "ercot_faststart_pool_condbinned.json"

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

# The offline startable pool (ERCOT-87 §8.2): OFFQS = offline quick start
# (SCED-startable within the operating hour); OFFNS = offline carrying a
# Non-Spin responsibility (startable via NSRS deployment). Plain OFF is NOT
# startable intra-hour and never enters. Nodal Protocols §3.9.1 telemetry.
OFFLINE_POOL = ("OFFQS", "OFFNS")

# CT-class SCED Resource Types (the wall derive's merchant CT scope — the
# measured pool is entirely CT; the apply-time ELIGIBILITY gate is unit
# physics min-down <= 2 h, rule 12, this map is only the measured-data key).
CT_RESTYPES = ("SCGT90", "SCLE90")

# CC-class SCED Resource Types (the wall derive's CLASS_OF_RESTYPE "CC" scope)
# — the SLOW-START tier of the offline-increment re-pricing (ERCOT-176,
# ScenarioConfig.ercot_offline_commit_offer). Same construction as the CT
# pool above, measured on this class's own OFFQS/OFFNS conduct; the
# apply-time ELIGIBILITY gate is unit physics (min-down 4-8 h AND min-run
# <= 12 h — the within-day start-and-run band, rule 12/18), never a class
# tuple, and this map is only the measured-data key.
#
# ST_GAS is deliberately EXCLUDED (rule 19 and the ERCOT-151 §3 condition):
# the steam class's own lane was REJECTED at ERCOT-91 on the ERCOT-89
# zero-spurious/C3a guards — the trip is intrinsic to the DAM-basis ST
# ladder in cold-snap hours — so its cell is `R` and re-testing it here
# would breach DO-NOT-REDO. The wall derive excludes it for the same reason.
CC_RESTYPES = ("CCGT90", "CCLE90")

# Measured-data key per derived pool class. The CT block is the ERCOT-88
# artifact (unchanged, byte-identical across this extension); CC is the
# ERCOT-176 slow-start tier.
POOL_CLASS_RESTYPES: dict[str, tuple[str, ...]] = {
    "CT": CT_RESTYPES,
    "CC": CC_RESTYPES,
}

_S2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_S2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_READ_COLS = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "HSL",
    "LSL",
] + [c for pair in zip(_S2_MW, _S2_PR) for c in pair]


# The live-capability sum + interval->hoy map need only these columns for
# every CT row; the 70 SCED2 curve columns are kept ONLY for the rare
# OFFQS/OFFNS pool rows (the whole-year corpus holds ~10M CT rows — a
# full-column concat OOMs, the wall derive's own streaming lesson).
_LIVE_COLS = ["SCED Time Stamp", "Telemetered Resource Status", "HSL"]


def _load_year(
    year: int, restypes: tuple[str, ...] = CT_RESTYPES
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """``(live_df, pool_df, files)`` of ``restypes``-class SCED rows for ``year``.

    ``live_df`` carries ALL CT rows at ``_LIVE_COLS`` (for the non-OUT live
    HSL sum and the interval->hoy map); ``pool_df`` carries the OFFQS/OFFNS
    rows at full ``_READ_COLS`` (status stripped before matching — the same
    normalization ``derive_year`` applies).

    Sources via the wall derive's ``_sced_source_files``: the full-year
    publication-month corpus when it majority-covers the delivery year (the
    2023 block, per the ERCOT-151 §4 re-upload), else the legacy
    delivery-labeled sample-day extracts (2024/2025 — the corpus for those
    years was purged 2026-07-22, so their blocks stay on the sample-day
    basis, byte-identical). Corpus shards are a string-typed raw copy with
    ~60-day-lagged delivery, so rows are delivery-year-filtered
    (``_delivery_year_rows``, rule 22) and numerics coerced
    (``_coerce_sced_numeric``); both are no-ops on the already-typed,
    delivery-labeled legacy extracts. Streams one shard at a time.
    """
    files = _sced_source_files(year)
    live_frames: list[pd.DataFrame] = []
    pool_frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(restypes)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        live_frames.append(_coerce_sced_numeric(df[_LIVE_COLS].copy()))
        pool_frames.append(_coerce_sced_numeric(df[stat.isin(OFFLINE_POOL)].copy()))
    if not live_frames:
        empty = pd.DataFrame(columns=_READ_COLS)
        return empty, empty, []
    # Drop zero-row shard slices before concat: an empty slice keeps its
    # pre-coercion string dtype (pandas-3 default for parquet strings) and
    # would promote the whole concat back to object, undoing the coercion.
    live = [f for f in live_frames if len(f)]
    pools = [f for f in pool_frames if len(f)]
    return (
        pd.concat(live, ignore_index=True)
        if live
        else pd.DataFrame(columns=_LIVE_COLS),
        pd.concat(pools, ignore_index=True)
        if pools
        else pd.DataFrame(columns=_READ_COLS),
        [p.name for p in files],
    )


def _pool_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Above-LSL startable segments of the pool rows' SCED2 curves.

    One row per (interval-resource, curve step) slice in
    ``(max(prev_step, LSL), min(step_MW, HASL)]`` at the step's price
    (clipped to HCAP) — the ERCOT-86/87 segment construction with the lower
    bound at LSL so the below-LSL min-gen curve bottom is excluded (charter
    §8.2 caveat c / §9.2).
    """
    MW = df[_S2_MW].to_numpy(float)
    PR = df[_S2_PR].to_numpy(float)
    lsl = np.maximum(np.nan_to_num(df["LSL"].to_numpy(float), nan=0.0), 0.0)
    hasl = df["HASL"].to_numpy(float)
    hoy = df["hoy"].to_numpy(int)
    ts = df["_ts"].to_numpy()
    gas = df["gas_day"].to_numpy(float)

    seg: dict[str, list[np.ndarray]] = {k: [] for k in ("mw", "pr", "hoy", "ts", "gas")}
    prev = lsl.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, hasl)
        mw = np.where(valid, np.maximum(hi - np.maximum(prev, lsl), 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg["mw"].append(mw[take])
            seg["pr"].append(np.minimum(p[take], HCAP_USD_MWH))
            seg["hoy"].append(hoy[take])
            seg["ts"].append(ts[take])
            seg["gas"].append(gas[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not seg["mw"]:
        return pd.DataFrame(columns=["hoy", "mw", "price", "ts", "gas_day"])
    return pd.DataFrame(
        {
            "hoy": np.concatenate(seg["hoy"]),
            "mw": np.concatenate(seg["mw"]),
            "price": np.concatenate(seg["pr"]),
            "ts": np.concatenate(seg["ts"]),
            "gas_day": np.concatenate(seg["gas"]),
        }
    )


def _prep_clock_gas(df: pd.DataFrame, gas_day: pd.Series) -> pd.DataFrame:
    """CPT -> fixed CST -> non-leap hour-of-year + gas-day join (wall clock).

    Adds ``hoy``/``_date``/``_ts``/``stat``/``gas_day`` and drops Feb-29 and
    gasless days — the exact row-level prep the pool construction has always
    applied, factored out so the light live frame and the full-column pool
    frame are prepped identically (the streaming split of ``_load_year``).

    Every derived column is taken from the PRE-filter clock arrays
    (``ts``/``cst``/``mo``/``dy``/``hh``) masked by ``ok``, never re-read off
    the already-filtered frame: mixing the two indexes the post-filter frame
    with the pre-filter mask and raises ``IndexError`` the moment a leap-year
    basis actually carries Feb-29 rows (ERCOT-187 / ERCOT-183).
    """
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    ts_pre = ts.to_numpy()
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()
    df["_ts"] = ts_pre[np.asarray(ok)]
    df["stat"] = df["Telemetered Resource Status"].astype(str).str.strip()
    df["gas_day"] = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    return df[df["gas_day"] > 0].copy()


def derive_year(
    year: int,
    gas_day: pd.Series,
    restypes: tuple[str, ...] = CT_RESTYPES,
    edges_override: "tuple[float, ...] | None" = None,
    position_tail: bool = False,
) -> tuple[dict, list[dict], list[str]]:
    """Return ``({"pool_frac": [...], "ladder": [...]}, coverage, files)``.

    ``restypes`` selects the measured pool class (CT = the ERCOT-88 fast-start
    pool; CC = the ERCOT-176 slow-start tier). The construction is identical
    for every class — only the row scope of both the pool numerator and the
    live-capability denominator changes, so each class's share is measured
    against its OWN live capability.
    """
    live_df, pool_df, files = _load_year(year, restypes)
    if live_df.empty:
        return {}, [], files

    live_all = _prep_clock_gas(live_df, gas_day)
    pool = _prep_clock_gas(pool_df, gas_day)
    segments = _pool_segments(pool)

    # Per-interval pool share of the class's LIVE capability: pool above-LSL
    # startable MW / sum HSL over the class's non-OUT rows (only-OUT-is-out —
    # the measured DAM availability's own convention, so the share maps onto
    # the capacity that overlay leaves in the LP).
    live = live_all[live_all["stat"] != "OUT"]
    live_mw = live.groupby("_ts")["HSL"].sum()
    pool_startable = (
        segments.groupby("ts")["mw"].sum() if len(segments) else pd.Series(dtype=float)
    )
    frac_iv = (pool_startable / live_mw.reindex(pool_startable.index)).dropna()
    frac_iv = frac_iv.clip(0.0, 1.0)
    hoy_of_ts = dict(zip(live_all["_ts"], live_all["hoy"]))

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES if edges_override is None else edges_override)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1
    if len(segments):
        segments["bin"] = hour_bin[np.minimum(segments["hoy"].to_numpy(int), HOURS - 1)]
        segments["mult"] = segments["price"] / segments["gas_day"]
    frac_bin_of = (
        pd.Series(
            hour_bin[
                np.minimum(
                    np.array([hoy_of_ts[t] for t in frac_iv.index], dtype=int),
                    HOURS - 1,
                )
            ],
            index=frac_iv.index,
        )
        if len(frac_iv)
        else pd.Series(dtype=int)
    )

    ladders: list[list[list[float]]] = []
    pool_frac: list[float] = []
    coverage: list[dict] = []
    tails: list[list[list[float]]] = []
    for b in range(n_bins):
        gb = segments[segments["bin"] == b] if len(segments) else segments
        n_iv = int(gb["ts"].nunique()) if len(gb) else 0
        n_days = int(pd.Series(gb["hoy"] // 24).nunique()) if len(gb) else 0
        qs = (
            _weighted_quantiles(
                gb["mult"].to_numpy(float),
                gb["mw"].to_numpy(float),
                LADDER_QUANTILES,
            )
            if len(gb)
            else [float("nan")] * len(LADDER_QUANTILES)
        )
        if position_tail:
            from lib.positiontail import tail_support

            tails.append(
                tail_support(gb["mult"].to_numpy(float), gb["mw"].to_numpy(float))
                if len(gb)
                else []
            )
        ladders.append([[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)])
        fb = frac_iv[frac_bin_of == b] if len(frac_iv) else frac_iv
        pool_frac.append(round(float(fb.mean()), 4) if len(fb) else float("nan"))
        coverage.append(
            {
                "intervals": n_iv,
                "days": n_days,
                "mean_pool_mw": round(float(gb["mw"].sum()) / max(n_iv, 1), 1)
                if len(gb)
                else 0.0,
            }
        )
    out = {"pool_frac": pool_frac, "ladder": ladders}
    if position_tail:
        out["tail"] = tails
    return out, coverage, files


def derive_year_continuous(
    year: int, gas_day: pd.Series, restypes: tuple[str, ...]
) -> tuple[dict, dict, list[str]]:
    """Per-hour-node pool share + ladder for one year/class (ERCOT-178).

    The IDENTICAL statistics :func:`derive_year` computes per net-load bin —
    interval-mean ``pool_frac`` and the MW-weighted :data:`LADDER_QUANTILES`
    of above-LSL startable segment multipliers — keyed per corpus hour node
    at the hour's within-year net-load percentile rank
    (PRECOMMIT-ercot178 §2). Rank-tied hours pool their intervals/segments.
    Zero new parameters; year-scoped, no pooled fallback.
    """
    live_df, pool_df, files = _load_year(year, restypes)
    if live_df.empty:
        return {}, {}, files

    live_all = _prep_clock_gas(live_df, gas_day)
    pool = _prep_clock_gas(pool_df, gas_day)
    segments = _pool_segments(pool)

    live = live_all[live_all["stat"] != "OUT"]
    live_mw = live.groupby("_ts")["HSL"].sum()
    pool_startable = (
        segments.groupby("ts")["mw"].sum() if len(segments) else pd.Series(dtype=float)
    )
    frac_iv = (pool_startable / live_mw.reindex(pool_startable.index)).dropna()
    frac_iv = frac_iv.clip(0.0, 1.0)
    hoy_of_ts = dict(zip(live_all["_ts"], live_all["hoy"]))

    pct = _netload_pct(year)
    frac_x = (
        pd.Series(
            pct[
                np.minimum(
                    np.array([hoy_of_ts[t] for t in frac_iv.index], dtype=int),
                    HOURS - 1,
                )
            ],
            index=frac_iv.index,
        )
        if len(frac_iv)
        else pd.Series(dtype=float)
    )
    frac_nodes = (
        frac_iv.groupby(frac_x).mean().sort_index()
        if len(frac_iv)
        else pd.Series(dtype=float)
    )

    pct_nodes: list[float] = []
    ladders: list[list[float]] = []
    n_iv_total = 0
    if len(segments):
        segments = segments.copy()
        segments["x"] = pct[np.minimum(segments["hoy"].to_numpy(int), HOURS - 1)]
        segments["mult"] = segments["price"] / segments["gas_day"]
        for x, gb in segments.groupby("x", sort=True):
            qs = _weighted_quantiles(
                gb["mult"].to_numpy(float), gb["mw"].to_numpy(float), LADDER_QUANTILES
            )
            if not all(np.isfinite(q) for q in qs):
                continue
            pct_nodes.append(round(float(x), 6))
            ladders.append([round(float(m), 3) for m in qs])
            n_iv_total += int(gb["ts"].nunique())

    out = {
        "frac_pct": [round(float(x), 6) for x in frac_nodes.index],
        "pool_frac": [round(float(v), 4) for v in frac_nodes.to_numpy()],
        "pct": pct_nodes,
        "ladder": ladders,
        "n_frac_nodes": int(len(frac_nodes)),
        "n_ladder_nodes": len(pct_nodes),
    }
    coverage = {
        "frac_nodes": int(len(frac_nodes)),
        "ladder_nodes": len(pct_nodes),
        "intervals": n_iv_total,
    }
    return out, coverage, files


def _main_position_tail(args) -> None:
    """ERCOT-181: write the position-tail vintage (PRECOMMIT-ercot181 §3).

    The frozen stepped artifact is loaded and COPIED VERBATIM; the CT pool's
    per (year, bin) tail is derived fresh with the identical population
    construction, and the re-computed ladder + pool_frac must REPRODUCE the
    frozen artifact's exactly — a corpus drifted since the frozen derive
    would make the appended tail inconsistent with its p90 anchor, so a
    mismatch is stop-the-line. CC blocks are copied untouched (the archived
    slow-start tier's scope; the positiontail vintage arms the CT pool only).
    """
    from lib.positiontail import POSITIONTAIL_TAG

    frozen = json.loads(DEFAULT_OUT.read_text())
    gas_day = _gas_day_series()
    result = json.loads(json.dumps(frozen))  # deep copy via round-trip
    tail_cov: dict[str, list[int]] = {}
    for y in args.years:
        per_year, _cov, _files = derive_year(
            y, gas_day, CT_RESTYPES, position_tail=True
        )
        frozen_tbl = frozen.get("CT", {}).get("years", {}).get(str(y))
        if not frozen_tbl:
            raise SystemExit(
                f"--position-tail: frozen pool artifact has no CT year {y} "
                "block to anchor a tail on"
            )
        if not per_year:
            raise SystemExit(f"--position-tail: no CT pool rows derived for {y}")
        if (
            per_year["ladder"] != frozen_tbl["ladder"]
            or per_year["pool_frac"] != frozen_tbl["pool_frac"]
        ):
            raise SystemExit(
                f"--position-tail: re-derived CT {y} ladder/pool_frac does "
                "not reproduce the frozen artifact's — the corpus has "
                "drifted since the frozen derive; STOP (rule 23)"
            )
        result["CT"]["years"][str(y)]["tail"] = per_year["tail"]
        tail_cov[str(y)] = [len(t) for t in per_year["tail"]]
        print(f"{y} CT pool: tail points by bin = {[len(t) for t in per_year['tail']]}")
    prov = result.setdefault("_provenance", {})
    prov["conditioning"] = POSITIONTAIL_TAG
    prov["positiontail"] = {
        "precommit": "docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md",
        "statistic": (
            "per (CT, year, bin): the MW-weighted empirical quantile "
            "function of the SAME offline above-LSL startable segment "
            "population the frozen ladder measured, at its own distinct "
            "step points above the p90 grid point "
            "(lib/positiontail.tail_support; multipliers HCAP-clipped by "
            "the parent segment construction, round(3); x = cumulative-MW "
            "fraction, round(6), strictly increasing). Sub-p90 ladders and "
            "pool_frac are the frozen artifact's blocks byte-verbatim; an "
            "empty tail keeps the frozen p90 end-clamp byte-identical "
            "(zero-support rule). CC blocks copied untouched (not armed)"
        ),
        "tail_years": [int(y) for y in args.years],
        "tail_points_per_bin": tail_cov,
        "frozen_source": DEFAULT_OUT.name,
    }
    out = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_faststart_pool_positiontail.json"
    )
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out} (frozen artifact untouched)")


def main() -> None:
    """Derive and write the fast-start pool ladder + share JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--classes",
        nargs="+",
        default=list(POOL_CLASS_RESTYPES),
        choices=list(POOL_CLASS_RESTYPES),
        help="measured pool classes to derive (CT = ERCOT-88 fast-start pool, "
        "CC = ERCOT-176 slow-start tier)",
    )
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--continuous",
        action="store_true",
        help="ERCOT-178: write the continuous-node vintage "
        "(ercot_faststart_pool_contpct.json) instead of the stepped bins — "
        "the frozen stepped artifact is never touched by this mode",
    )
    ap.add_argument(
        "--top-scoped",
        action="store_true",
        help="ERCOT-180: write the top-scoped vintage "
        "(ercot_faststart_pool_topscoped.json) — frozen stepped values below "
        "p97, conduct-identified stepped sub-bins above, ULP-pair "
        "step-encoded (PRECOMMIT-ercot180 §3); neither frozen artifact is "
        "touched",
    )
    ap.add_argument(
        "--position-tail",
        action="store_true",
        help="ERCOT-181: write the position-tail vintage "
        "(ercot_faststart_pool_positiontail.json) — the frozen stepped "
        "ladders byte-verbatim plus the CT pool's measured tail step points "
        "above p90 per (year, bin) (PRECOMMIT-ercot181 §3); the frozen "
        "artifact is never touched",
    )
    args = ap.parse_args()
    if sum([args.continuous, args.top_scoped, args.position_tail]) > 1:
        raise SystemExit(
            "--continuous, --top-scoped and --position-tail are mutually exclusive"
        )
    if args.position_tail:
        _main_position_tail(args)
        return
    if args.top_scoped:
        _main_topscoped(args)
        return
    if args.continuous:
        _main_continuous(args)
        return

    gas_day = _gas_day_series()
    per_class: dict[str, dict[int, dict]] = {}
    coverage: dict[str, dict[str, list[dict]]] = {}
    sources: dict[str, dict[str, list[str]]] = {}
    for cls in args.classes:
        per_year: dict[int, dict] = {}
        cls_cov: dict[str, list[dict]] = {}
        cls_src: dict[str, list[str]] = {}
        for y in args.years:
            per_year[y], cov, files = derive_year(y, gas_day, POOL_CLASS_RESTYPES[cls])
            cls_cov[str(y)] = cov
            cls_src[str(y)] = files
            if per_year[y]:
                p70 = [lad[3][1] for lad in per_year[y]["ladder"]]
                print(f"{y} {cls} pool: p70 mult by bin  = {p70}")
                print(f"          pool_frac by bin   = {per_year[y]['pool_frac']}")
                print(f"          intervals by bin   = {[c['intervals'] for c in cov]}")
        per_class[cls] = per_year
        coverage[cls] = cls_cov
        sources[cls] = cls_src

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965), "
                "delivery years " + "-".join(str(y) for y in args.years) + "; "
                "per-year basis as disclosed in source_files — the full-year "
                "publication-month corpus where it majority-covers the "
                "delivery year (2023: the 2026-08-03 re-upload under "
                "data/raw/ercot/SCED/, rows delivery-year-filtered), else the "
                "scoped sample-day extracts (2024/2025)"
            ),
            "method": (
                "per-interval above-LSL startable segments (max(LSL,0) -> "
                "min(step MW, HASL)) of the SCED2 offer curve of OFFQS/OFFNS "
                "resources of the block's own class; MW-weighted quantile "
                "ladder of segment prices as effective-HR multipliers (price "
                "/ HH-daily+ERCOT-basis gas); pool_frac = interval-mean pool "
                "startable MW / sum HSL of that class's non-OUT rows "
                "(only-OUT-is-out, the measured DAM availability convention); "
                "derived within net-load-percentile bins. IDENTICAL "
                "construction for every class block — only the row scope of "
                "both numerator and denominator changes"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar), forward-native"
            ),
            "apply_gate": (
                "unit physics, never a class tuple (rule 12/18). CT block: "
                "min_down_hours <= 2 h (constants.FASTSTART_POOL_MIN_DOWN_"
                "HOURS) — charter §9 (ercot-residual-midband-formation-lane). "
                "CC block: 4 h <= min_down_hours <= 8 h AND min_run_hours "
                "<= 12 h (constants.RA_BRIDGE_ECON_MIN_DOWN_HOURS / "
                "OFFLINE_COMMIT_MIN_DOWN_HOURS_MAX / OFFLINE_COMMIT_MIN_RUN_"
                "HOURS_MAX) — the within-day start-and-run band, ERCOT-176 "
                "(docs/PRECOMMIT-ercot176-offline-increment-2026-08-07.md §1)"
            ),
            "offline_pool_statuses": list(OFFLINE_POOL),
            "class_restypes": {k: list(v) for k, v in POOL_CLASS_RESTYPES.items()},
            "ct_restypes": list(CT_RESTYPES),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "year_scoped": (
                "NO pooled fallback by design (rule 13): a year absent from "
                "this artifact gets NO pool leg (the wall basis is retained "
                "byte-identical), and each year's ladder derives only from "
                "that year's own posted conduct — a 2024/2025-derived ladder "
                "remains barred from 2023's post-Uri conservative-operations "
                "regime. 2023 now carries its OWN measured block: the owner "
                "authorized the SCED-basis extension to 2023 (ERCOT-105) and "
                "the 2026-08-03 corpus re-upload (ERCOT-151 §4) supplies "
                "complete delivery-2023 coverage"
            ),
            "source_files": sources,
            "coverage": coverage,
            "corpus_caveat": (
                "2024/2025 remain on scoped sample days (ERCOT-74/75/86 "
                "intake): the Jan-2024 winter-morning mid-band cluster is NOT "
                "in that basis — disclosed unmeasured (charter §8). 2023 "
                "derives from the full-year publication-month corpus "
                "(complete delivery-year coverage, all 365 days)"
            ),
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved. The CC block was "
                "added at ERCOT-176 under a source-data change (the "
                "ERCOT-157 delivery-2023 corpus) plus a NEW class scope; the "
                "CT blocks are byte-identical across that extension"
            ),
        },
    }
    for cls in args.classes:
        result[cls] = {
            "years": {
                str(y): per_class[cls][y] for y in args.years if per_class[cls][y]
            }
        }

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


def _main_continuous(args) -> None:
    """Write the ERCOT-178 continuous-node vintage (``--continuous``).

    A NEW artifact (`ercot_faststart_pool_contpct.json` unless ``--out``
    overrides) for the pre-registered `ercot_offer_surface_continuous` gate —
    the frozen stepped artifact is never modified (PRECOMMIT-ercot178 §2).
    Year-scoped, no pooled fallback, exactly as the stepped vintage. The CT
    class is the armed consumer; the CC block is carried for parity with the
    stepped artifact's class inventory.
    """
    out_path = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_faststart_pool_contpct.json"
    )
    gas_day = _gas_day_series()
    per_class: dict[str, dict[int, dict]] = {}
    coverage: dict[str, dict[str, dict]] = {}
    sources: dict[str, dict[str, list[str]]] = {}
    for cls in args.classes:
        per_year: dict[int, dict] = {}
        cls_cov: dict[str, dict] = {}
        cls_src: dict[str, list[str]] = {}
        for y in args.years:
            per_year[y], cov, files = derive_year_continuous(
                y, gas_day, POOL_CLASS_RESTYPES[cls]
            )
            cls_cov[str(y)] = cov
            cls_src[str(y)] = files
            if per_year[y]:
                print(
                    f"{y} {cls} pool: {per_year[y]['n_frac_nodes']} frac nodes, "
                    f"{per_year[y]['n_ladder_nodes']} ladder nodes"
                )
        per_class[cls] = per_year
        coverage[cls] = cls_cov
        sources[cls] = cls_src

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965), "
                "delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "IDENTICAL statistics to the stepped vintage (interval-mean "
                "offline-startable pool share of class live capability + "
                "MW-weighted quantile ladder of above-LSL startable segment "
                "multipliers), keyed per corpus HOUR NODE at the hour's "
                "within-year net-load percentile rank instead of per bin; "
                "rank-tied hours pool their intervals/segments "
                "(PRECOMMIT-ercot178 §2, zero new parameters)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar), forward-native"
            ),
            "conditioning": "continuous-netload-pct",
            "offline_pool_statuses": list(OFFLINE_POOL),
            "class_restypes": {k: list(v) for k, v in POOL_CLASS_RESTYPES.items()},
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "year_scoped": (
                "NO pooled fallback by design (rule 13), exactly as the "
                "stepped vintage: a year absent from this artifact gets NO "
                "pool leg"
            ),
            "source_files": sources,
            "coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved; the stepped artifact "
                "is untouched by this vintage"
            ),
        },
    }
    for cls in args.classes:
        result[cls] = {
            "years": {
                str(y): per_class[cls][y] for y in args.years if per_class[cls][y]
            }
        }

    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


def _main_topscoped(args) -> None:
    """Write the ercot-180 TOP-SCOPED vintage (``--top-scoped``), CT block only.

    PRECOMMIT-ercot180 §1/§3: below p97 the FROZEN stepped artifact's own
    per-bin ``pool_frac`` and ladders are byte-copied; the former p97-p100 top
    bin is split at the conduct-identified edges, each sub-bin computed by the
    IDENTICAL stepped statistics on the sub-bin's own rows; zero-support
    sub-bins inherit the frozen parent values (frac and ladder independently).
    ULP-pair step-encoded; year-scoped CT block only (the armed
    ``ercot_faststart_pool_offer`` reads CT alone; the CC slow-start block is
    the adjudicated-inert ercot-176 tier and is NOT reproduced). Neither
    frozen artifact is touched.
    """
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from scripts.lib.topscoped_encode import (
        TOPSCOPED_TAG,
        encode_step_nodes,
        load_identified_edges,
        rows_from_pairs,
        split_top_bin,
    )

    out_path = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_faststart_pool_topscoped.json"
    )
    frozen = json.loads(DEFAULT_OUT.read_text())
    legacy_edges = [float(x) for x in frozen["_provenance"]["netload_pct_edges"]]
    new_edges = load_identified_edges()
    edges_ext = tuple(legacy_edges + new_edges)
    n_legacy = len(legacy_edges)
    n_sub = len(new_edges) + 1

    gas_day = _gas_day_series()
    years_entry: dict[str, dict] = {}
    coverage: dict[str, list[dict]] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        fro_tbl = frozen.get("CT", {}).get("years", {}).get(str(y))
        if not fro_tbl:
            continue  # year-scoped: absent years stay absent
        ext, cov, files = derive_year(y, gas_day, CT_RESTYPES, edges_override=edges_ext)
        sources[str(y)] = files
        if not ext:
            continue
        sub_fr: list = []
        sub_ld: list = []
        disc: list[dict] = []
        for k in range(n_sub):
            b = n_legacy + k
            fr = float(ext["pool_frac"][b])
            lad = rows_from_pairs([ext["ladder"][b]])[0]
            ok_f = bool(np.isfinite(fr))
            ok_l = all(np.isfinite(v) for v in lad)
            sub_fr.append([fr] if ok_f else None)
            sub_ld.append(lad if ok_l else None)
            cov_b = cov[b] if b < len(cov) else {}
            disc.append(
                {
                    "frac_computed": ok_f,
                    "ladder_computed": ok_l,
                    **{k2: cov_b.get(k2) for k2 in ("intervals", "days")},
                }
            )
        e_fr, r_fr = split_top_bin(
            legacy_edges,
            [[float(s)] for s in fro_tbl["pool_frac"]],
            new_edges,
            sub_fr,
        )
        xs_f, ys_f = encode_step_nodes(e_fr, r_fr)
        e_ld, r_ld = split_top_bin(
            legacy_edges, rows_from_pairs(fro_tbl["ladder"]), new_edges, sub_ld
        )
        xs_l, ys_l = encode_step_nodes(e_ld, r_ld)
        years_entry[str(y)] = {
            "frac_pct": xs_f,
            "pool_frac": [r[0] for r in ys_f],
            "pct": xs_l,
            "ladder": ys_l,
        }
        coverage[str(y)] = disc
        print(f"{y} CT pool: sub-bins {[d['ladder_computed'] for d in disc]}")

    result: dict = {
        "_provenance": {
            "source": frozen["_provenance"].get("source"),
            "method": (
                "TOP-SCOPED (ercot-180, form b): frozen stepped per-bin "
                "pool_frac/ladders byte-copied below p97; the p97-p100 bin "
                "split at the conduct-identified edges with the IDENTICAL "
                "statistics per sub-bin; zero-support sub-bins inherit the "
                "frozen parent values; ULP-pair step-encoded "
                "(PRECOMMIT-ercot180 §1/§3, zero fitted scalars)"
            ),
            "driver": frozen["_provenance"].get("driver"),
            "conditioning": TOPSCOPED_TAG,
            "netload_pct_edges": list(edges_ext),
            "new_edges": list(new_edges),
            "edge_identification": "results/calibration/"
            "ercot180_edge_identification.json",
            "ladder_quantiles": list(LADDER_QUANTILES),
            "apply_gate": frozen["_provenance"].get("apply_gate"),
            "offline_pool_statuses": frozen["_provenance"].get("offline_pool_statuses"),
            "ct_restypes": list(CT_RESTYPES),
            "iso": "ERCOT",
            "year_scoped": (
                "Per-year CT node tables, NO pooled fallback (rule 13), "
                "exactly as the frozen stepped vintage; training years only"
            ),
            "source_files": sources,
            "topscoped_sub_bin_coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update or a re-identified edge record, never because a "
                "residual moved; neither frozen artifact is touched"
            ),
        },
        "CT": {"years": years_entry},
    }
    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
