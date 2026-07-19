"""Derive the ERCOT offline fast-start pool offer ladder + pool share.

The ERCOT-88 apply artifact for the §6.2 mechanism of
``docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md`` (charter §9)
— ``ScenarioConfig.ercot_faststart_pool_offer``. The ERCOT-87 measurement
adjudicated that the actual $150-500 moderate-tightness band prices on the
**offline startable CT pool** (``Telemetered Resource Status`` OFFQS/OFFNS:
full SCED curves disclosed, SCED-startable intra-hour), not on any online
spare or unmitigated-CC surface. This derive promotes that measurement to a
model input, from the same NP3-965 60-Day SCED sample-day parquets on disk:

* Pool rows: CT-class resources (SCGT90/SCLE90) telemetered OFFQS or OFFNS.
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
artifact gets NO pool leg (the wall basis is retained byte-identical); a
2024/2025-derived ladder is barred from 2023's post-Uri conservative-ops
regime (the RT wall's own bar).

Coverage is DISCLOSED, never silently capped: per-(year x bin) interval/day
counts and mean pool MW are recorded, so a thin bin (the corpus is scoped
sample days; the Jan-2024 winter cluster is not in it) is visible at the
artifact level.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits
must cite the data change.

Usage::

    python scripts/data/derive_ercot_faststart_pool.py \
        [--years 2024 2025] \
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
from derive_ercot_sced_offer_wall import SCED_DIR  # noqa: E402

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_faststart_pool_condbinned.json"
)

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


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ALL-status CT-class SCED rows for ``year`` + source file names."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        frames.append(df[df["Resource Type"].isin(CT_RESTYPES)].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


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


def derive_year(year: int, gas_day: pd.Series) -> tuple[dict, list[dict], list[str]]:
    """Return ``({"pool_frac": [...], "ladder": [...]}, coverage, files)``."""
    df, files = _load_year(year)
    if df.empty:
        return {}, [], files

    # CPT -> fixed CST -> non-leap hour-of-year (the wall derive's clock).
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()
    df["_ts"] = pd.to_datetime(df["SCED Time Stamp"]).to_numpy()[np.asarray(ok)]
    df["stat"] = df["Telemetered Resource Status"].astype(str).str.strip()
    df["gas_day"] = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    df = df[df["gas_day"] > 0].copy()

    pool = df[df["stat"].isin(OFFLINE_POOL)].copy()
    segments = _pool_segments(pool)

    # Per-interval pool share of the class's LIVE capability: pool above-LSL
    # startable MW / sum HSL over non-OUT CT rows (only-OUT-is-out — the
    # measured DAM availability's own convention, so the share maps onto the
    # capacity that overlay leaves in the LP).
    live = df[df["stat"] != "OUT"]
    live_mw = live.groupby("_ts")["HSL"].sum()
    pool_startable = (
        segments.groupby("ts")["mw"].sum() if len(segments) else pd.Series(dtype=float)
    )
    frac_iv = (pool_startable / live_mw.reindex(pool_startable.index)).dropna()
    frac_iv = frac_iv.clip(0.0, 1.0)
    hoy_of_ts = dict(zip(df["_ts"], df["hoy"]))

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
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
    return {"pool_frac": pool_frac, "ladder": ladders}, coverage, files


def main() -> None:
    """Derive and write the fast-start pool ladder + share JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    coverage: dict[str, list[dict]] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], cov, files = derive_year(y, gas_day)
        coverage[str(y)] = cov
        sources[str(y)] = files
        if per_year[y]:
            p70 = [lad[3][1] for lad in per_year[y]["ladder"]]
            print(f"{y} CT pool: p70 mult by bin  = {p70}")
            print(f"          pool_frac by bin   = {per_year[y]['pool_frac']}")
            print(f"          intervals by bin   = {[c['intervals'] for c in cov]}")

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data, scoped sample "
                "days, delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "per-interval above-LSL startable segments (max(LSL,0) -> "
                "min(step MW, HASL)) of the SCED2 offer curve of OFFQS/OFFNS "
                "CT-class resources; MW-weighted quantile ladder of segment "
                "prices as effective-HR multipliers (price / HH-daily+ERCOT-"
                "basis gas); pool_frac = interval-mean pool startable MW / "
                "sum HSL of non-OUT CT rows (only-OUT-is-out, the measured "
                "DAM availability convention); derived within net-load-"
                "percentile bins"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar), forward-native"
            ),
            "apply_gate": (
                "unit physics min_down_hours <= 2 (rule 12), never a class "
                "tuple; charter §9 (ercot-residual-midband-formation-lane)"
            ),
            "offline_pool_statuses": list(OFFLINE_POOL),
            "ct_restypes": list(CT_RESTYPES),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "year_scoped": (
                "NO pooled fallback by design (rule 13): a year absent from "
                "this artifact gets NO pool leg (the wall basis is retained "
                "byte-identical); a 2024/2025-derived ladder is barred from "
                "2023's post-Uri conservative-operations regime"
            ),
            "sample_day_files": sources,
            "coverage": coverage,
            "corpus_caveat": (
                "scoped sample days (ERCOT-74/75/86 intake): the Jan-2024 "
                "winter-morning mid-band cluster is NOT in the corpus — "
                "disclosed unmeasured (charter §8)"
            ),
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved"
            ),
        },
        "CT": {"years": {str(y): per_year[y] for y in args.years if per_year[y]}},
    }

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
