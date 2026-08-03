"""ERCOT-154 Phase 1 — measure the ESR RT discharge-offer surface (no LP).

The ercot-153 chartered arm. ERCOT-153 decomposed the model's diurnal price
amplitude deficit (`results/calibration/ercot153_amplitude.json`): ~80 % of it
is PEAK-HALF, it collapses exactly where the reserve co-opt is silent (2024
summer 0.264, 2025 0.38-0.49 of actual hour-of-day amplitude with reserve
price ~$0 at h17-21), and the everyday evening-ramp premium ($20-66/MWh of
actual peak excess) has no former in the model. The model's storage discharges
at the epsilon tiebreaker plus a FLAT residual-identified
``battery_dispatch_adder`` ($10/MWh on the ERCOT keeper; DOF-ledger
``identification: residual``) with perfect foresight -- which flattens exactly
that peak. Real ERCOT batteries offer their discharge at opportunity-cost
levels that move with system conditions.

Phase 1 measures that offer surface from the committed sample-day corpus and
tests whether it is IDENTIFIED well enough to arm. Nothing here builds an LP,
arms a flag, or writes a model input: it writes one JSON record.

Construction (the ERCOT-86/87 wall + ERCOT-88 pool family, imported so the
edges/quantiles/clock cannot drift):

* Population: ``Resource Type == PWRSTR`` rows telemetered ONLINE
  (``ON``/``ONREG``/``ONFFRRRS``/``FRRSUP``). ``ONTEST`` is EXCLUDED (a unit
  under commissioning test is not offering commercially) and its share is
  disclosed; ``OUT``/``OFF``/``NA`` never enter.
* Increment: per interval-resource, the SCED2 (as-dispatched) curve segmented
  between ``max(LSL, 0)`` and ``min(step MW, HASL)``. The HASL cap is what
  makes this rule-19 clean against the measured-AS stack: HASL is HSL net of
  the resource's AS responsibility, so the ladder prices exactly the energy
  headroom that ``ercot_storage_as_reserve``/``_product_credit``/
  ``_deployment`` leave to energy, never the AS-reserved MW.
* Cells: (net-load-percentile bin x hour block), on the imported
  ``NETLOAD_PCT_EDGES`` and the CPT -> fixed-CST clock of the pool derive.
  The hour blocks isolate the evening ramp that is the measured object.
* Ladder: MW-weighted quantiles of segment price, in TWO bases --
  absolute $/MWh, and the wall's gas-day multiple (price / delivered gas).
  Reporting both is the identification test, not a menu: ERCOT-147 refused
  the CT band re-identification because NEITHER zero-parameter form was
  stable across the year pair, and the same bar applies here.

Identification is REPORTED, never asserted: per-cell interval/day/resource
counts, cross-day stability (relative IQR of the day-level MW-weighted p50
within a cell) and the 2024-vs-2025 ratio per cell in each basis. Thin cells
are disclosed, never silently pooled away.

Year scope: 2024/2025 only. No 2023 SCED corpus exists on disk (the NP3-965
full-year upload was purged by the 2026-07-22 history rewrite; the re-upload
is OWNER-DECLINED as of 2026-08-02), so 2023 can carry no measured ladder --
rule 13 bars back-casting a 2024/25 surface onto 2023's regime.

Usage::

    python scripts/probes/ercot154_storage_offer_surface.py \
        [--out results/calibration/ercot154_storage_offer_surface.json]
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
from derive_ercot_faststart_pool import _STD_TZ  # noqa: E402
from derive_ercot_sced_offer_wall import SCED_DIR  # noqa: E402

DEFAULT_OUT = REPO / "results/calibration/ercot154_storage_offer_surface.json"

# MW-share thresholds ($/MWh). The quantile ladder saturates at HCAP in the
# upper rungs (2024's p70/p90 pin at $5,000), so the share of offered MW below
# a price is the robust read on the same conduct -- the ERCOT-138 §2.3
# construction, which is what made the CC below-cost block legible.
SHARE_THRESHOLDS_USD = (20.0, 30.0, 50.0, 75.0, 100.0, 200.0)

# A cell enters the pooled cross-year rung summary only with at least this
# many SCED intervals in BOTH years. Thin cells stay in the per-cell record
# (disclosure, not deletion) but must not drive the identification verdict.
MIN_INTERVALS_FOR_STABILITY = 40

# ERCOT models grid batteries as PWRSTR Gen Resources; the 60-Day SCED Gen
# Resource disclosure carries their DISCHARGE offer curve (the charge side
# lives on the paired Load Resource and is out of scope here).
ESR_RESTYPE = "PWRSTR"

# Online, commercially-offering telemetry states (Nodal Protocols §3.9.1).
# ONTEST is excluded and disclosed; OUT/OFF/NA/ONHOLD never enter.
ONLINE_STATES = ("ON", "ONREG", "ONFFRRRS", "FRRSUP")
EXCLUDED_STATES = ("ONTEST",)

# Hour blocks on the fixed-CST clock, chosen from the ERCOT-153 measurement
# (peak-half deficit; actual RT peak hour h18, model h19-20) so the evening
# ramp is its own cell rather than being averaged into the afternoon.
HOUR_BLOCKS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("overnight_h0_5", tuple(range(0, 6))),
    ("morning_h6_10", tuple(range(6, 11))),
    ("midday_h11_15", tuple(range(11, 16))),
    ("evening_h16_21", tuple(range(16, 22))),
    ("late_h22_23", (22, 23)),
)

_S2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_S2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "HASL",
    "LSL",
    "Base Point",
] + [c for pair in zip(_S2_MW, _S2_PR) for c in pair]


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ALL-status PWRSTR SCED rows for ``year`` + the source file names."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        rt = df["Resource Type"].astype(str).str.strip()
        frames.append(df[rt == ESR_RESTYPE].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


def _discharge_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Above-LSL, AS-net discharge segments of the SCED2 offer curves.

    One row per (interval-resource, curve step) slice in
    ``(max(prev_step, LSL, 0), min(step MW, HASL)]`` at the step's price
    (clipped to HCAP) -- the ERCOT-86/87/88 segment construction, with the
    lower bound at ``max(LSL, 0)`` so a charging-range curve bottom can never
    enter and the upper bound at HASL so AS-reserved MW never enter.
    """
    MW = df[_S2_MW].to_numpy(float)
    PR = df[_S2_PR].to_numpy(float)
    lsl = np.maximum(np.nan_to_num(df["LSL"].to_numpy(float), nan=0.0), 0.0)
    hasl = np.nan_to_num(df["HASL"].to_numpy(float), nan=0.0)
    cols = {
        "hoy": df["hoy"].to_numpy(int),
        "hod": df["hod"].to_numpy(int),
        "ts": df["_ts"].to_numpy(),
        "day": df["_day"].to_numpy(),
        "gas": df["gas_day"].to_numpy(float),
        "res": df["Resource Name"].to_numpy(),
    }

    seg: dict[str, list[np.ndarray]] = {k: [] for k in (*cols, "mw", "pr")}
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
            for name, arr in cols.items():
                seg[name].append(arr[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    if not seg["mw"]:
        return pd.DataFrame(
            columns=["hoy", "hod", "mw", "price", "ts", "day", "gas_day", "res"]
        )
    return pd.DataFrame(
        {
            "hoy": np.concatenate(seg["hoy"]),
            "hod": np.concatenate(seg["hod"]),
            "mw": np.concatenate(seg["mw"]),
            "price": np.concatenate(seg["pr"]),
            "ts": np.concatenate(seg["ts"]),
            "day": np.concatenate(seg["day"]),
            "gas_day": np.concatenate(seg["gas"]),
            "res": np.concatenate(seg["res"]),
        }
    )


def _prepare(df: pd.DataFrame, gas_day: pd.Series) -> pd.DataFrame:
    """Attach the CPT -> fixed-CST clock, hour-of-day, gas day and status."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    out = df.loc[np.asarray(ok)].copy()
    out["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    out["hod"] = hh[ok]
    day = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)]
    out["_day"] = day.to_numpy()
    out["_ts"] = ts.to_numpy()[np.asarray(ok)]
    out["stat"] = out["Telemetered Resource Status"].astype(str).str.strip()
    out["gas_day"] = gas_day.reindex(pd.DatetimeIndex(out["_day"])).to_numpy(float)
    return out[out["gas_day"] > 0].copy()


def _rel_iqr(x: np.ndarray) -> float:
    """Relative inter-quartile range (IQR / median) of a day-level sample."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan")
    med = float(np.median(x))
    if abs(med) < 1e-9:
        return float("nan")
    return float((np.percentile(x, 75) - np.percentile(x, 25)) / med)


def measure_year(year: int, gas_day: pd.Series) -> tuple[dict, list[str], dict]:
    """Measure one year's ESR discharge-offer surface + its identification."""
    raw, files = _load_year(year)
    if raw.empty:
        return {}, files, {}
    df = _prepare(raw, gas_day)

    total_rows = len(df)
    status_share = (
        df.groupby("stat")["HSL"].agg(["size", "sum"]).rename(columns={"size": "rows"})
    )
    census = {
        "rows_all_status": int(total_rows),
        "resources_all_status": int(df["Resource Name"].nunique()),
        "rows_by_status": {k: int(v) for k, v in status_share["rows"].items()},
        "hsl_mw_share_by_status": {
            k: round(float(v) / max(float(status_share["sum"].sum()), 1e-9), 4)
            for k, v in status_share["sum"].items()
        },
        "excluded_states": list(EXCLUDED_STATES),
    }

    # Corpus hour-of-day reach. Three of the four committed extracts are
    # HOUR-TRUNCATED to ~h10-h22 CST; only the 2025 ercot86 tail-days file
    # carries full 24-hour days. This bounds which hour blocks can carry a
    # measured cell at all and is disclosed, never inferred away.
    census["hours_present_cst"] = sorted(int(h) for h in df["hod"].unique())
    census["days"] = int(pd.Series(df["_day"]).nunique())

    online = df[df["stat"].isin(ONLINE_STATES)].copy()
    census["rows_online"] = int(len(online))
    census["resources_online"] = int(online["Resource Name"].nunique())
    census["mean_online_hsl_mw"] = round(
        float(online.groupby("_ts")["HSL"].sum().mean()), 1
    )
    census["mean_online_hasl_mw"] = round(
        float(online.groupby("_ts")["HASL"].sum().mean()), 1
    )
    # How much of the online power cap the AS stack already holds back -- the
    # rule-19 boundary between this surface and the measured AS-award family.
    census["as_reserved_share_of_hsl"] = round(
        1.0 - census["mean_online_hasl_mw"] / max(census["mean_online_hsl_mw"], 1e-9), 4
    )

    seg = _discharge_segments(online)
    if not len(seg):
        return {"census": census}, files, {}

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1
    seg["bin"] = hour_bin[np.minimum(seg["hoy"].to_numpy(int), HOURS - 1)]
    seg["mult"] = seg["price"] / seg["gas_day"]
    block_of_hod = {h: name for name, hrs in HOUR_BLOCKS for h in hrs}
    seg["block"] = seg["hod"].map(block_of_hod)

    cells: dict[str, dict] = {}
    for block_name, _hrs in HOUR_BLOCKS:
        for b in range(n_bins):
            gb = seg[(seg["block"] == block_name) & (seg["bin"] == b)]
            key = f"{block_name}|bin{b}"
            if not len(gb):
                cells[key] = {
                    "intervals": 0,
                    "days": 0,
                    "resources": 0,
                    "mw_per_interval": 0.0,
                    "usd": [float("nan")] * len(LADDER_QUANTILES),
                    "gasmult": [float("nan")] * len(LADDER_QUANTILES),
                    "day_p50_rel_iqr_usd": float("nan"),
                    "day_p50_rel_iqr_gasmult": float("nan"),
                }
                continue
            n_iv = int(gb["ts"].nunique())
            mw = gb["mw"].to_numpy(float)
            usd = _weighted_quantiles(gb["price"].to_numpy(float), mw, LADDER_QUANTILES)
            mult = _weighted_quantiles(gb["mult"].to_numpy(float), mw, LADDER_QUANTILES)
            # Cross-day stability: the MW-weighted p50 recomputed within each
            # calendar day of the cell, then its relative IQR across days.
            day_p50_usd, day_p50_mult = [], []
            for _d, gd in gb.groupby("day"):
                w = gd["mw"].to_numpy(float)
                day_p50_usd.append(
                    _weighted_quantiles(gd["price"].to_numpy(float), w, (0.5,))[0]
                )
                day_p50_mult.append(
                    _weighted_quantiles(gd["mult"].to_numpy(float), w, (0.5,))[0]
                )
            price = gb["price"].to_numpy(float)
            tot = float(mw.sum())
            cells[key] = {
                "intervals": n_iv,
                "days": int(gb["day"].nunique()),
                "resources": int(gb["res"].nunique()),
                "mw_per_interval": round(tot / max(n_iv, 1), 1),
                "usd": [round(v, 2) for v in usd],
                "gasmult": [round(v, 3) for v in mult],
                "mw_share_below": {
                    str(int(t)): round(float(mw[price <= t].sum()) / max(tot, 1e-9), 4)
                    for t in SHARE_THRESHOLDS_USD
                },
                "day_p50_rel_iqr_usd": round(_rel_iqr(np.array(day_p50_usd)), 3),
                "day_p50_rel_iqr_gasmult": round(_rel_iqr(np.array(day_p50_mult)), 3),
            }

    # Hour-of-day profile of the fleet's MW-weighted p50 offer -- the direct
    # read on whether the measured surface carries an evening premium at all.
    hod_profile = {}
    for h in range(24):
        gh = seg[seg["hod"] == h]
        if not len(gh):
            hod_profile[str(h)] = None
            continue
        w = gh["mw"].to_numpy(float)
        hod_profile[str(h)] = {
            "p50_usd": round(
                _weighted_quantiles(gh["price"].to_numpy(float), w, (0.5,))[0], 2
            ),
            "p50_gasmult": round(
                _weighted_quantiles(gh["mult"].to_numpy(float), w, (0.5,))[0], 3
            ),
            "mw_per_interval": round(
                float(w.sum()) / max(int(gh["ts"].nunique()), 1), 1
            ),
        }

    census["gas_day_mean_usd_mmbtu"] = round(float(seg["gas_day"].mean()), 3)
    return {"census": census, "cells": cells, "hod_profile": hod_profile}, files, {}


def main() -> None:
    """Measure the surface for 2024/2025 and write the Phase 1 record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    per_year: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        res, files, _ = measure_year(y, gas_day)
        per_year[str(y)] = res
        sources[str(y)] = files
        if res:
            c = res["census"]
            print(
                f"{y}: online rows {c['rows_online']:,} / {c['resources_online']} "
                f"resources; mean online HSL {c['mean_online_hsl_mw']} MW, "
                f"HASL {c['mean_online_hasl_mw']} MW "
                f"(AS holds {c['as_reserved_share_of_hsl']:.1%})"
            )

    # Cross-year stability (the ERCOT-147 bar): the 2025/2024 ratio of each
    # ladder rung in each basis. A form is identified only where its ratio is
    # near 1 across the cells BOTH years populate; ERCOT-147 refused the CT
    # band because neither zero-parameter form cleared this.
    stability: dict[str, dict] = {}
    rung_summary: dict[str, dict] = {}
    ys = [str(y) for y in args.years]
    if len(ys) == 2 and all(per_year.get(y, {}).get("cells") for y in ys):
        a, b = per_year[ys[0]]["cells"], per_year[ys[1]]["cells"]
        nan5 = [float("nan")] * len(LADDER_QUANTILES)
        pooled: dict[str, dict[str, list[float]]] = {
            basis: {f"p{int(q * 100)}": [] for q in LADDER_QUANTILES}
            for basis in ("usd", "gasmult")
        }
        for key in a:
            ca, cb = a[key], b.get(key, {})
            min_iv = int(min(ca["intervals"], cb.get("intervals", 0)))
            row: dict = {"min_intervals": min_iv}
            for basis in ("usd", "gasmult"):
                va, vb = ca[basis], cb.get(basis, nan5)
                ratios = []
                for i, q in enumerate(LADDER_QUANTILES):
                    ok = np.isfinite(va[i]) and np.isfinite(vb[i]) and va[i] > 0
                    r = round(vb[i] / va[i], 3) if ok else None
                    ratios.append(r)
                    # THIN CELLS ARE EXCLUDED FROM THE SUMMARY, NOT DROPPED
                    # from the record: the per-cell row above keeps them.
                    if r is not None and min_iv >= MIN_INTERVALS_FOR_STABILITY:
                        pooled[basis][f"p{int(q * 100)}"].append(r)
                row[f"{basis}_2024"] = va
                row[f"{basis}_2025"] = vb
                row[f"ratio_{basis}"] = ratios
            stability[key] = row
        for basis, rungs in pooled.items():
            rung_summary[basis] = {}
            for name, vals in rungs.items():
                arr = np.array(vals, dtype=float)
                if not len(arr):
                    rung_summary[basis][name] = {"n": 0}
                    continue
                med = float(np.median(arr))
                rung_summary[basis][name] = {
                    "n": int(len(arr)),
                    "median_ratio": round(med, 3),
                    "min_ratio": round(float(arr.min()), 3),
                    "max_ratio": round(float(arr.max()), 3),
                    "rel_iqr_of_ratio": round(
                        float((np.percentile(arr, 75) - np.percentile(arr, 25)) / med),
                        3,
                    )
                    if abs(med) > 1e-9
                    else None,
                }

    result = {
        "_provenance": {
            "session": "ERCOT-154 Phase 1 (measurement only; no LP built, no year solved)",
            "charter": (
                "ercot-153 chartered arm -- the measured storage evening "
                "discharge-offer surface; evidence base "
                "results/calibration/ercot153_amplitude.json"
            ),
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data, scoped sample "
                "days (ERCOT-74/75/86 intake), PWRSTR rows, delivery years "
                + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "per-interval above-LSL discharge segments (max(LSL,0) -> "
                "min(step MW, HASL)) of the SCED2 offer curve of ONLINE "
                "(ON/ONREG/ONFFRRRS/FRRSUP) PWRSTR resources; MW-weighted "
                "quantile ladders of segment price in TWO bases (absolute "
                "$/MWh and the wall's gas-day multiple), within "
                "(net-load-percentile bin x hour block)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar), forward-native -- the wall/pool driver"
            ),
            "rule19_boundary": (
                "the HASL cap excludes AS-responsibility MW, so this surface "
                "prices only the energy headroom the measured AS-award stack "
                "(ercot_storage_as_reserve / _product_credit / _deployment) "
                "leaves to energy; the incumbent occupant of the DISCHARGE "
                "PRICE row is the flat residual-identified "
                "battery_dispatch_adder ($10/MWh on the ERCOT keeper), which "
                "any arm must REPLACE, never stack on"
            ),
            "year_scope": (
                "2024/2025 only -- no 2023 SCED corpus is on disk (NP3-965 "
                "full-year upload purged 2026-07-22; re-upload OWNER-DECLINED "
                "2026-08-02), and rule 13 bars back-casting a 2024/25 surface "
                "onto 2023's regime"
            ),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "share_thresholds_usd": list(SHARE_THRESHOLDS_USD),
            "min_intervals_for_stability": MIN_INTERVALS_FOR_STABILITY,
            "hour_blocks": {name: list(hrs) for name, hrs in HOUR_BLOCKS},
            "hcap_usd_mwh": HCAP_USD_MWH,
            "online_states": list(ONLINE_STATES),
            "excluded_states": list(EXCLUDED_STATES),
            "iso": "ERCOT",
            "sample_day_files": sources,
            "corpus_caveat": (
                "scoped sample days: coverage is DISCLOSED per cell "
                "(intervals/days/resources), never silently pooled"
            ),
        },
        "years": per_year,
        "cross_year_stability": stability,
        "cross_year_rung_summary": rung_summary,
    }
    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
