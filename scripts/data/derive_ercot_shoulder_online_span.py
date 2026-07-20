"""Derive the ERCOT conditional merchant online-span table (ERCOT-89 step 2).

The apply artifact for ``ScenarioConfig.ercot_shoulder_online_span`` — the
shoulder-hour online-capability mechanism of
``docs/handoffs/ercot-shoulder-online-envelope-2026-07.md`` (§6 shape (a),
owner-authorized step-2 design round 2026-07-19). The §8 measurement confirmed
the model's availability basis hands the LP the full non-OUT merchant
capability as base/wall-priced ONLINE headroom every hour, while reality ran
the residual band hours on a ~0.4-0.5 GW online margin (8-10x wedge, H1) and
the thin-margin state carries a conditional signature beyond net load (H2).
This derive promotes that CONDITIONAL structure — never the per-hour ON series
(rule 13's bright line: the hourly series is an operational outcome; only its
conditional distribution regenerates for a forward year) — to a model input:

* Per (year x class CC/CT), the mean telemetered **ON share of non-OUT
  capability** (interval-summed HSL, hourly means — the §4 probe convention;
  the non-OUT denominator is the measured DAM availability's only-OUT-is-out
  basis, so the share maps onto exactly the capacity the availability overlay
  leaves in the LP) per conditioning cell.
* Cells: **net-load percentile bin x season x 4-hour block**, resolved
  hierarchically — a cell below the coverage floor falls back to
  (bin x block), then (bin x season), then (bin) — and emitted as a fully
  RESOLVED (n_bins x 4 x 6) table plus the level + observation count per
  cell, so the apply seam does no fitting and coverage is disclosed, never
  silently capped. Bins with zero corpus coverage stay null (the apply seam
  keeps those hours byte-identical — no measured conditional, no mechanism).
* Drivers are forward-native only: the year's own net-load percentile
  (EIA-930 demand - wind - solar, the wall derives' shared axis), calendar
  season, hour-of-day block. NO residual, price, or model-output enters.

Provenance / admissibility (CLAUDE.md rules 12/13/14): every quantity is a
telemetered status share; zero fitted scalars; the coverage floor
(``MIN_CELL_HOURS``) is a disclosure threshold, not a tuned value. The
artifact is **YEAR-SCOPED**: no pooled fallback — a year absent from the
artifact gets NO span mechanism (the ERCOT-86 full-span wall geometry is
retained byte-identical); a 2024/2025-derived table is barred from 2023's
post-Uri conservative-ops regime (the RT wall's own bar).

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits
must cite the data change.

Usage::

    python scripts/data/derive_ercot_shoulder_online_span.py \
        [--years 2024 2025] \
        [--out data/raw/_validation-source/ercot_shoulder_online_span_condbinned.json]
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
    HOURS,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _netload_pct,
)
from derive_ercot_sced_offer_wall import CLASS_OF_RESTYPE, SCED_DIR  # noqa: E402

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_shoulder_online_span_condbinned.json"
)

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

# Meteorological seasons on the fixed-CST month: DJF=0, MAM=1, JJA=2, SON=3.
# Index by (month - 1). The season axis separates the shoulder commitment
# regimes (Apr/May vs Jul vs Oct/Dec) the §8.2 H2 conditional lives across.
SEASON_OF_MONTH: tuple[int, ...] = (0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0)

# 4-hour hour-of-day blocks (6/day) — the ERCOT-73 commitment-loading state
# artifact's block convention, reused so the two conditional overlays share
# one intra-day grain.
HOUR_BLOCK_H = 4

# Coverage floor per conditioning cell before falling back one hierarchy
# level: a cell mean over fewer sample-day hours than this is noise, not a
# measured conditional (the corpus is ~35-40 scoped sample days/year).
# Disclosure threshold (every cell's n and level are emitted), never tuned.
MIN_CELL_HOURS = 6

_READ_COLS = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HSL",
]


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ALL-status merchant CC/CT SCED rows for ``year`` (status + HSL)."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        frames.append(df[df["Resource Type"].isin(CLASS_OF_RESTYPE)].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


def _hourly_on_share(df: pd.DataFrame) -> pd.DataFrame:
    """Per (hoy, cls): hourly-mean ON HSL / hourly-mean non-OUT HSL.

    Interval sums per (interval, cls, family), averaged within the hour —
    the §4 probe's corpus convention (`ercot89_shoulder_online_measure`).
    """
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
    df["_ts"] = pd.to_datetime(df["SCED Time Stamp"]).to_numpy()[np.asarray(ok)]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    stat = df["Telemetered Resource Status"].astype(str).str.strip()
    df["is_on"] = stat.str.startswith("ON").to_numpy()
    df["is_nonout"] = (stat != "OUT").to_numpy()

    per_iv = (
        df.groupby(["_ts", "hoy", "cls"], observed=True)
        .apply(
            lambda g: pd.Series(
                {
                    "on": g.loc[g["is_on"], "HSL"].sum(),
                    "nonout": g.loc[g["is_nonout"], "HSL"].sum(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )
    hourly = (
        per_iv.groupby(["hoy", "cls"], observed=True)[["on", "nonout"]]
        .mean()
        .reset_index()
    )
    hourly = hourly[hourly["nonout"] > 0.0].copy()
    hourly["on_share"] = (hourly["on"] / hourly["nonout"]).clip(0.0, 1.0)
    return hourly


def _resolve_cells(
    share: np.ndarray, hour_bin: np.ndarray, season: np.ndarray, block: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hierarchically resolved (n_bins, 4, 6) span table + level + n.

    Level 0 = bin x season x block, 1 = bin x block, 2 = bin x season,
    3 = bin. A cell resolves at the deepest level with >= MIN_CELL_HOURS
    covered corpus hours (level 3 accepts any n >= 1). Unresolved cells
    (bin never sampled) stay NaN.
    """
    n_bins = len(NETLOAD_PCT_EDGES) + 1
    n_seasons, n_blocks = 4, 24 // HOUR_BLOCK_H
    cov = np.isfinite(share)
    idx = np.flatnonzero(cov)
    vals = share[idx]
    b_, s_, k_ = hour_bin[idx], season[idx], block[idx]

    def cell_means(keys: list[np.ndarray]) -> tuple[dict, dict]:
        key = np.stack(keys, axis=1)
        cells, inv = np.unique(key, axis=0, return_inverse=True)
        sums = np.bincount(inv, weights=vals)
        cnts = np.bincount(inv)
        return (
            {tuple(c): sums[i] / cnts[i] for i, c in enumerate(cells)},
            {tuple(c): int(cnts[i]) for i, c in enumerate(cells)},
        )

    m0, n0 = cell_means([b_, s_, k_])
    m1, n1 = cell_means([b_, k_])
    m2, n2 = cell_means([b_, s_])
    m3, n3 = cell_means([b_])

    span = np.full((n_bins, n_seasons, n_blocks), np.nan)
    level = np.full((n_bins, n_seasons, n_blocks), -1, dtype=int)
    n_obs = np.zeros((n_bins, n_seasons, n_blocks), dtype=int)
    for b in range(n_bins):
        for s in range(n_seasons):
            for k in range(n_blocks):
                for lv, (m, n, key) in enumerate(
                    (
                        (m0, n0, (b, s, k)),
                        (m1, n1, (b, k)),
                        (m2, n2, (b, s)),
                        (m3, n3, (b,)),
                    )
                ):
                    cnt = n.get(key, 0)
                    if cnt >= (MIN_CELL_HOURS if lv < 3 else 1):
                        span[b, s, k] = m[key]
                        level[b, s, k] = lv
                        n_obs[b, s, k] = cnt
                        break
    return span, level, n_obs


def derive_year(year: int) -> tuple[dict, dict, list[str]]:
    """Return ``({cls: table-dict}, coverage, files)`` for one year."""
    df, files = _load_year(year)
    if df.empty:
        return {}, {}, files
    hourly = _hourly_on_share(df)

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    month = (
        np.searchsorted(
            np.append(_MONTH_START_HOUR[1:], HOURS), np.arange(HOURS), side="right"
        )
        + 1
    )
    season = np.array([SEASON_OF_MONTH[m - 1] for m in month])
    block = (np.arange(HOURS) % 24) // HOUR_BLOCK_H

    out: dict = {}
    coverage: dict = {}
    for cls in ("CC", "CT"):
        c = hourly[hourly["cls"] == cls]
        share = np.full(HOURS, np.nan)
        hoys = c["hoy"].to_numpy(int)
        keep = hoys < HOURS
        share[hoys[keep]] = c["on_share"].to_numpy(float)[keep]
        span, level, n_obs = _resolve_cells(share, hour_bin, season, block)
        out[cls] = {
            "span": [
                [
                    [None if not np.isfinite(v) else round(float(v), 4) for v in row]
                    for row in mat
                ]
                for mat in span
            ],
            "level": level.tolist(),
            "n_obs": n_obs.tolist(),
        }
        coverage[cls] = {
            "covered_hours": int(np.isfinite(share).sum()),
            "cells_by_level": [int((level == lv).sum()) for lv in range(4)],
            "cells_unresolved": int((level == -1).sum()),
            "share_mean": round(float(np.nanmean(share)), 4),
        }
    return out, coverage, files


def main() -> None:
    """Derive and write the conditional online-span JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    per_year: dict[int, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], coverage[str(y)], sources[str(y)] = derive_year(y)
        for cls, cov in coverage[str(y)].items():
            print(
                f"{y} {cls}: {cov['covered_hours']} corpus hours, "
                f"cells by level {cov['cells_by_level']} "
                f"(unresolved {cov['cells_unresolved']}), "
                f"mean ON share {cov['share_mean']}"
            )

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data, scoped sample "
                "days, delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "per-hour ON share of non-OUT capability per merchant class "
                "(interval-summed HSL, hourly means; ON = telemetered ON*, "
                "non-OUT = every status except OUT — the measured DAM "
                "availability's only-OUT-is-out basis), aggregated to "
                "hierarchical conditional cell means (net-load percentile "
                "bin x season x 4h block, coverage-gated fallback to "
                "bin x block, bin x season, bin)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar, the wall artifacts' shared axis) x calendar "
                "season x hour-of-day block — forward-native only; the "
                "per-hour ON series enters ONLY through these conditional "
                "means (rule 13 bright line, charter §6)"
            ),
            "charter": (
                "docs/handoffs/ercot-shoulder-online-envelope-2026-07.md "
                "§6 shape (a) / §8 measurement; ERCOT-89 step 2"
            ),
            "merchant_scope": dict(CLASS_OF_RESTYPE),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "season_of_month": list(SEASON_OF_MONTH),
            "hour_block_hours": HOUR_BLOCK_H,
            "min_cell_hours": MIN_CELL_HOURS,
            "iso": "ERCOT",
            "year_scoped": (
                "NO pooled fallback by design (rule 13): a year absent from "
                "this artifact gets NO span mechanism (the ERCOT-86 full-span "
                "wall geometry is retained byte-identical); a 2024/2025-"
                "derived table is barred from 2023's post-Uri conservative-"
                "operations regime (the RT wall's own bar)"
            ),
            "sample_day_files": sources,
            "coverage": coverage,
            "corpus_caveat": (
                "scoped sample days (ERCOT-74/75/86 intake): non-random day "
                "selection (tail + control days oversampled by design) is "
                "mitigated by the net-load-bin conditioning and disclosed "
                "here; the Jan-2024 winter-morning mid-band cluster is NOT "
                "in the corpus (charter §8). The conditional structure "
                "carries ~half the measured residual-vs-control ON-share "
                "separation in 2024 and ~a third in 2025 (leave-one-out "
                "cell-mean gap +0.14 / +0.05-0.07 vs measured +0.27 / "
                "+0.18) — the remainder is day-of commitment information "
                "with no forward analogue, deliberately NOT encoded"
            ),
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved"
            ),
        },
    }
    for cls in ("CC", "CT"):
        result[cls] = {
            "years": {
                str(y): per_year[y][cls]
                for y in args.years
                if per_year[y] and cls in per_year[y]
            }
        }

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
