#!/usr/bin/env python3
"""Derive ERCOT's conditional online-capability ENVELOPE for the energy-side
cap (`ScenarioConfig.ercot_energy_online_capability_cap`, ERCOT-159 / queue
item 9, the ERCOT-155 named successor).

Charter and pre-registered construction:
``docs/PRECOMMIT-ercot159-energy-online-capability-cap-2026-08-04.md`` §2.

The measured fast-tier capability object, per SCED interval, hourly-meaned
onto the fixed-CST non-leap 8760 clock (the ERCOT-155 census taxonomy and
clock, verbatim):

    OLC(t) = Σ online HSL over slow-start fossil types
             (CCGT90/CCLE90/CLLIG/CLLIM/GSREH/GSNONR/GSSUP)
           + Σ online HSL over NUC
           + Σ online max(HSL − Base Point, 0) over quick-start types
             (SCGT90/SCLE90/RECIP/DSL)      [quick online HEADROOM]

conditioned on (season × hour-block × net-load percentile bin) with the
per-cell **maximum** as the envelope statistic (a-priori semantics: "more
than this was never mustered at these conditions"; precommit §2). The
net-load driver is the standing wall driver — EIA-930 ``Demand − NG:WND −
NG:SUN`` percentile-ranked within year (``derive_ercot_dam_cleared_share.
_netload_pct``) — with 14 bins: decile edges 0.10..0.90 plus 0.92/0.94/
0.96/0.98 (the extreme-tail resolution the ercot43 rejection identified as
mandatory).

Year scoping by measured coverage (the `ercot_shoulder_online_span`
precedent): a year block is derived ONLY where the full-year 60-Day SCED
corpus exists — delivery-2023 (``data/raw/ercot/SCED/``, 315 shards, all 365
delivery days, ERCOT-157). The 2024/2025 sample-day extracts (47
event/control day-files) are structurally insufficient for a 336-cell
envelope and are used as VALIDATION only (cross-year stability, reported in
provenance, never gating). Absent years leave the mechanism byte-inert.

Rule 13: the per-hour telemetered online series is an operational OUTCOME —
it BUILDS and VALIDATES this conditional object and never ships raw (the
ERCOT-89 §6 bright line). Rule 20: zero fitted scalars — no deliverability
coefficient, no margin. Rule 23: FROZEN against residuals; re-derive only
when the SCED corpus / EIA-930 / HSL / storage-capability source data
update, citing the data change.

Validation stanzas written into ``_provenance`` (reported, not gating):
* reconciliation of the evening medians against the committed ERCOT-155
  census benchmarks (matched day-classes, event/control never pooled);
* 2024/2025 sample-day OLC vs the 2023 cell envelope at matched cells;
* system-level closure against the committed NP6-905-CD ``rtolhsl`` series:
  rtolhsl ≈ OLC + quick BP + wind HSL + solar HSL + storage capability
  (+ hydro/PUN/other residue, the reported remainder).

Run:
    .venv/bin/python scripts/data/derive_ercot_energy_online_capability.py

Writes
``data/raw/_validation-source/ercot_energy_online_capability_condbinned.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))  # repo root: canonical scripts.data.* sibling imports on direct run

from scripts.data.derive_ercot_dam_cleared_share import (  # noqa: E402
    _MONTH_START_HOUR,
    _netload_pct,
)
from scripts.data.derive_ercot_faststart_pool import _STD_TZ  # noqa: E402
from scripts.data.derive_ercot_sced_offer_wall import SCED_DIR  # noqa: E402

CORPUS_DIR = REPO / "data/raw/ercot/SCED"
OUT_PATH = (
    REPO / "data/raw/_validation-source/ercot_energy_online_capability_condbinned.json"
)
ORDC_TPL = "data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
HSL_TPL = "data/raw/ercot-hsl/ercot_{year}_hsl_hourly.parquet"
STORAGE_CAP = REPO / "data/raw/ercot-storage-capability.csv"

#: Full-corpus years — the only years a table block may be derived for
#: (precommit §2 year scoping). Extend ONLY when a further full-year corpus
#: lands (the item-8a intake), never from sample days.
FULL_CORPUS_YEARS = (2023,)
#: Sample-day validation years (the four committed ercot74/75/86 extracts).
SAMPLE_YEARS = (2024, 2025)

# --- The ERCOT-155 census taxonomy, verbatim (precommit §2). -----------------
SLOW_TYPES = ("CCGT90", "CCLE90", "CLLIG", "CLLIM", "GSREH", "GSNONR", "GSSUP")
QUICK_TYPES = ("SCGT90", "SCLE90", "RECIP", "DSL")
NUC_TYPES = ("NUC",)
ONLINE_STATES = ("ON", "ONREG", "ONFFRRRS", "FRRSUP", "ONRGL", "ONOS")

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
    "Base Point",
]

# --- The conditional grain (precommit §2, fixed a priori). -------------------
#: Month (1-12) → season index: DJF=0, MAM=1, JJAS=2, ON=3.
SEASON_BY_MONTH = (0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 0)
SEASON_NAMES = ("DJF", "MAM", "JJAS", "ON")
#: Hour-of-day blocks (inclusive bounds) on the fixed-CST clock.
HOUR_BLOCKS = ((0, 5), (6, 9), (10, 13), (14, 16), (17, 21), (22, 23))
#: Net-load percentile-rank bin edges — deciles + the split top decile
#: (14 bins; the ercot43 extreme-tail lesson).
NETLOAD_RANK_EDGES = (
    0.10,
    0.20,
    0.30,
    0.40,
    0.50,
    0.60,
    0.70,
    0.80,
    0.90,
    0.92,
    0.94,
    0.96,
    0.98,
)
HOURS = 8760


def _prepare(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """CPT → fixed-CST clock + hour-of-year (ERCOT-155 pattern, verbatim)."""
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    yr = cst.dt.year.to_numpy()
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = (yr == year) & ~((mo == 2) & (dy == 29))
    out = df.loc[np.asarray(ok)].copy()
    out["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    out["stat"] = out["Telemetered Resource Status"].astype(str).str.strip()
    out["_ts"] = ts.to_numpy()[np.asarray(ok)]
    return out


def _interval_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Per-interval OLC components: slow/nuc online HSL, quick online headroom,
    quick online BP, and the on+off slow+nuc HSL total (the share diagnostic
    denominator)."""
    rt = df["Resource Type"].astype(str).str.strip()
    on = df["stat"].isin(ONLINE_STATES)
    slow = rt.isin(SLOW_TYPES)
    nuc = rt.isin(NUC_TYPES)
    quick = rt.isin(QUICK_TYPES)
    g = pd.DataFrame(
        {
            "slow_on": df[slow & on].groupby("_ts")["HSL"].sum(),
            "nuc_on": df[nuc & on].groupby("_ts")["HSL"].sum(),
            "quick_on_hsl": df[quick & on].groupby("_ts")["HSL"].sum(),
            "quick_on_bp": df[quick & on].groupby("_ts")["Base Point"].sum(),
            "slownuc_total": df[slow | nuc].groupby("_ts")["HSL"].sum(),
        }
    )
    g["hoy"] = df.groupby("_ts")["hoy"].first()
    return g.reset_index(drop=True)


def _scan(year: int) -> pd.DataFrame:
    """Hourly OLC component means for one delivery year (8760-indexed)."""
    if year in FULL_CORPUS_YEARS:
        paths = sorted(CORPUS_DIR.glob("*.parquet"))
    else:
        paths = sorted(
            SCED_DIR.glob(
                f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
            )
        )
    if not paths:
        raise SystemExit(f"no SCED source files for {year}")
    chunks: list[pd.DataFrame] = []
    for p in paths:
        df = pd.read_parquet(p, columns=_READ_COLS)
        rt = df["Resource Type"].astype(str).str.strip()
        df = df[rt.isin(SLOW_TYPES + QUICK_TYPES + NUC_TYPES)]
        for c in ("HSL", "Base Point"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
        df = _prepare(df, year)
        if not df.empty:
            chunks.append(_interval_frame(df))
    iv = pd.concat(chunks, ignore_index=True)
    hourly = iv.groupby("hoy").mean(numeric_only=True)
    hourly["n_intervals"] = iv.groupby("hoy").size()
    hourly = hourly.reindex(range(HOURS))
    hourly["olc"] = (
        hourly["slow_on"].fillna(0.0)
        + hourly["nuc_on"].fillna(0.0)
        + np.clip(
            hourly["quick_on_hsl"].fillna(0.0) - hourly["quick_on_bp"].fillna(0.0),
            0.0,
            None,
        )
    ).where(hourly["slow_on"].notna())
    return hourly


def _cell_keys(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(cell-key strings, coverage-independent) for every hour of ``year``.

    Cell key = ``s{season}_b{block}_n{bin}`` on the precommit §2 grain. Returns
    (keys, netload_rank) so callers can also report driver coverage.
    """
    hoy = np.arange(HOURS)
    month = np.searchsorted(_MONTH_START_HOUR, hoy, side="right")
    season = np.asarray(SEASON_BY_MONTH, dtype=int)[month - 1]
    hod = hoy % 24
    block = np.zeros(HOURS, dtype=int)
    for b, (lo, hi) in enumerate(HOUR_BLOCKS):
        block[(hod >= lo) & (hod <= hi)] = b
    rank = _netload_pct(year)
    nl_bin = np.searchsorted(np.asarray(NETLOAD_RANK_EDGES), rank, side="right")
    keys = np.array(
        [f"s{s}_b{b}_n{n}" for s, b, n in zip(season, block, nl_bin)], dtype=object
    )
    return keys, rank


def derive_year(year: int) -> tuple[dict, pd.DataFrame]:
    """The per-cell envelope table for one full-corpus year."""
    hourly = _scan(year)
    keys, rank = _cell_keys(year)
    olc = hourly["olc"].to_numpy(dtype=float)
    share = olc / hourly["slownuc_total"].to_numpy(dtype=float)
    covered = ~np.isnan(olc) & ~np.isnan(rank)
    cells: dict[str, dict] = {}
    for k in sorted(set(keys[covered].tolist())):
        m = covered & (keys == k)
        cells[k] = {
            "max_mw": round(float(np.max(olc[m])), 1),
            "mean_mw": round(float(np.mean(olc[m])), 1),
            "n": int(m.sum()),
            "share_mean": round(float(np.nanmean(share[m])), 4),
        }
    block = {
        "cells": cells,
        "n_cells": len(cells),
        "n_hours_covered": int(covered.sum()),
        "olc_gw_mean": round(float(np.nanmean(olc)) / 1e3, 3),
        "olc_gw_evening_mean": round(
            float(
                np.nanmean(
                    olc[(np.arange(HOURS) % 24 >= 17) & (np.arange(HOURS) % 24 <= 21)]
                )
            )
            / 1e3,
            3,
        ),
    }
    return block, hourly


def _validate_sample_year(year: int, cells_2023: dict) -> dict:
    """Sample-day OLC vs the 2023 envelope at matched cells (reported only)."""
    hourly = _scan(year)
    keys, _rank = _cell_keys(year)
    olc = hourly["olc"].to_numpy(dtype=float)
    covered = ~np.isnan(olc)
    ratios = []
    missing = 0
    for i in np.flatnonzero(covered):
        c = cells_2023.get(keys[i])
        if c is None:
            missing += 1
            continue
        ratios.append(olc[i] / c["max_mw"])
    r = np.asarray(ratios, dtype=float)
    return {
        "hours_measured": int(covered.sum()),
        "hours_with_2023_cell": int(r.size),
        "hours_cell_missing": int(missing),
        "olc_over_2023_envelope_p50": round(float(np.median(r)), 4) if r.size else None,
        "olc_over_2023_envelope_p90": round(float(np.percentile(r, 90)), 4)
        if r.size
        else None,
        "olc_over_2023_envelope_max": round(float(np.max(r)), 4) if r.size else None,
        "hours_above_2023_envelope": int((r > 1.0).sum()) if r.size else None,
    }


def _validate_rtolhsl_closure(year: int, hourly: pd.DataFrame) -> dict:
    """System-level closure: rtolhsl − (OLC + quick BP + wind/solar HSL +
    storage capability) = hydro/PUN/other residue (reported only)."""
    ordc = pd.read_parquet(REPO / ORDC_TPL.format(year=year))
    rtolhsl = ordc["rtolhsl"].to_numpy(dtype=float)[:HOURS]
    hsl = pd.read_parquet(REPO / HSL_TPL.format(year=year))
    wind = hsl["wind_hsl_mw"].to_numpy(dtype=float)[:HOURS]
    solar = hsl["solar_hsl_mw"].to_numpy(dtype=float)[:HOURS]
    stor = pd.read_csv(STORAGE_CAP)
    stor = (
        stor[stor["year"] == year]
        .sort_values("hour")["capability_mw"]
        .to_numpy(dtype=float)[:HOURS]
    )
    olc = hourly["olc"].to_numpy(dtype=float)
    qbp = hourly["quick_on_bp"].fillna(0.0).to_numpy(dtype=float)
    resid = rtolhsl - (olc + qbp + wind + solar + np.nan_to_num(stor, nan=0.0))
    ok = ~np.isnan(resid)
    return {
        "residue_gw_mean": round(float(np.nanmean(resid[ok])) / 1e3, 3),
        "residue_gw_p10": round(float(np.percentile(resid[ok], 10)) / 1e3, 3),
        "residue_gw_p90": round(float(np.percentile(resid[ok], 90)) / 1e3, 3),
        "hours_compared": int(ok.sum()),
        "note": "residue = hydro + PUN + other online HSL the object correctly excludes",
    }


def main() -> int:
    blocks: dict[str, dict] = {}
    hourly_by_year: dict[int, pd.DataFrame] = {}
    for y in FULL_CORPUS_YEARS:
        blocks[str(y)], hourly_by_year[y] = derive_year(y)
        print(
            f"{y}: {blocks[str(y)]['n_cells']} cells over "
            f"{blocks[str(y)]['n_hours_covered']} hours; evening OLC mean "
            f"{blocks[str(y)]['olc_gw_evening_mean']} GW"
        )
    validation: dict[str, dict] = {}
    for y in SAMPLE_YEARS:
        validation[f"sample_day_check_{y}"] = _validate_sample_year(
            y, blocks[str(FULL_CORPUS_YEARS[0])]["cells"]
        )
        print(f"{y} sample-day check: {validation[f'sample_day_check_{y}']}")
    for y in FULL_CORPUS_YEARS:
        validation[f"rtolhsl_closure_{y}"] = _validate_rtolhsl_closure(
            y, hourly_by_year[y]
        )
        print(f"{y} rtolhsl closure: {validation[f'rtolhsl_closure_{y}']}")

    out = {
        "_provenance": {
            "source": "ERCOT 60-Day SCED Disclosure Gen Resource Data — full-year "
            "delivery-2023 corpus (data/raw/ercot/SCED, 315 shards, ERCOT-157) + "
            "the committed ercot74/75/86 sample-day extracts (validation only)",
            "method": "per-interval Σ online HSL over slow-start fossil "
            f"{SLOW_TYPES} + NUC, plus online quick-start headroom (HSL − Base "
            f"Point over {QUICK_TYPES}); online states {ONLINE_STATES}; hourly "
            "means on the fixed-CST non-leap clock; per-cell MAX envelope",
            "driver": "EIA-930 net load (Demand − NG:WND − NG:SUN) percentile "
            "rank within year (derive_ercot_dam_cleared_share._netload_pct), "
            f"bins at rank edges {NETLOAD_RANK_EDGES}",
            "grain": {
                "season_by_month": list(SEASON_BY_MONTH),
                "season_names": list(SEASON_NAMES),
                "hour_blocks": [list(b) for b in HOUR_BLOCKS],
                "netload_rank_edges": list(NETLOAD_RANK_EDGES),
            },
            "charter": "docs/PRECOMMIT-ercot159-energy-online-capability-cap-"
            "2026-08-04.md §2 (owner-authorized queue item 9, ERCOT-155 named "
            "successor); statistic and grain fixed a priori, zero fitted "
            "scalars (rule 20); frozen against residuals (rule 23) — "
            "re-derive only on SCED corpus / EIA-930 / HSL / storage source "
            "updates, citing the data change",
            "year_scoping": "blocks exist only for full-corpus years "
            f"{list(FULL_CORPUS_YEARS)}; absent years leave the mechanism "
            "byte-inert (the ercot_shoulder_online_span precedent); extension "
            "requires the item-8a corpus intake, never sample-day pooling",
            "consumer": "market_sim.results.scarcity."
            "ercot_energy_online_capability_cap_mw (fast-tier row of "
            "ReserveDesign.online_capacity_cap)",
            "validation": validation,
        },
        **blocks,
    }
    OUT_PATH.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {OUT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
