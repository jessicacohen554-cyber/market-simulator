"""Derive the ERCOT conditional online-span table — STEAM (ST_GAS) leg.

The ST_GAS analogue of ``scripts/data/derive_ercot_shoulder_online_span.py``
(ERCOT-89 CC/CT), built for the ERCOT-93 telemetered-status lane
(``docs/handoffs/ercot-stgas-shoulder-2026-07.md`` §9.4 design question (ii):
"whether the state weight ALSO moves to the SCED-basis hour-grain
conditional"). The ERCOT-90/92 measure-first work pinned the open ST_GAS
shoulder residual as a COMMITMENT-STATE miss: the LP clears the whole
DAM-available steam fleet at its cheap committed/econ offers in shoulder hours
where reality had only a fraction of that base telemetered ONLINE facing the
real $150-500 band. The model's availability basis is class-day only-OUT-is-out
(``ercot_thermal_dam_availability``), which hands the LP the full non-OUT
merchant steam capability as base/wall-priced online headroom in EVERY hour of
a covered day — including the low-net-load shoulder hours where reality ran the
steam fleet on a thin online margin.

This derive promotes that CONDITIONAL online structure — never the per-hour ON
series (rule 13's bright line, mirrored from the CC/CT derive: the hourly
series is an operational outcome; only its conditional distribution regenerates
for a forward year) — to a model input for the ST_GAS steam-offer seam:

* Per delivery year, the mean telemetered **ON share of non-OUT capability**
  (interval-summed HSL, hourly means) for the model's own ST_GAS fleet, per
  conditioning cell. The non-OUT denominator is the measured DAM availability's
  only-OUT-is-out basis, so the share maps onto exactly the capacity the
  availability overlay leaves in the LP (identical mapping to the CC/CT span).
* Cells: **net-load percentile bin x season x 4-hour block**, resolved
  hierarchically (bin x season x block -> bin x block -> bin x season -> bin)
  with the shared coverage floor (``MIN_CELL_HOURS``); emitted as a fully
  RESOLVED (n_bins x 4 x 6) table plus the level + observation count per cell,
  so the apply seam does no fitting and coverage is disclosed.
* Drivers are forward-native only: the year's own net-load percentile (EIA-930
  demand - wind - solar, the wall derives' shared axis), calendar season,
  hour-of-day block. NO residual, price, Base Point, or model output enters.

Fleet scope (rule 19, ST_GAS steam-owner seam): the model's own 17-plant
ST_GAS fleet via the exact resource-name map ``FLEET_PLANT_OF_RESOURCE``
(shared byte-for-byte with ``derive_ercot_sced_offer_wall_steam`` — the RT
steam wall this span co-anchors); the non-fleet industrial/municipal CHP steam
resources are excluded and disclosed, and an unmapped corpus name is a hard
error (``_scope_fleet``), so a source update forces a map review.

Full-year corpus (2026-07-21 NP3-965 intake): reads the publication-month
shards (``data/raw/ercot/YYYY-MM.part*.parquet``) via the offer-wall derive's
own ``_sced_source_files`` / ``_delivery_year_rows``, so 2023-2025 are all
present (the CC/CT span still reads the sample-day subset — this steam leg is
built on the full year from the start). Rows are delivery-year-filtered, so the
2022 validation holdout and 2026 locked-test rows carried in adjacent
publication files never enter a training-year table.

Provenance / admissibility (CLAUDE.md rules 12/13/14): every quantity is a
telemetered status share; zero fitted scalars; the coverage floor is a
disclosure threshold, not a tuned value. The artifact is **YEAR-SCOPED**: no
pooled fallback — a year absent from the artifact gets NO span mechanism (the
full-span wall geometry is retained byte-identical).

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits must
cite the data change.

Usage::

    python scripts/data/derive_ercot_shoulder_online_span_steam.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_shoulder_online_span_steam_condbinned.json]
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
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _STD_TZ,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
)
from derive_ercot_sced_offer_wall_steam import (  # noqa: E402
    ST_RESTYPES,
    _merge_excluded,
    _scope_fleet,
)
from derive_ercot_shoulder_online_span import (  # noqa: E402
    HOUR_BLOCK_H,
    MIN_CELL_HOURS,
    SEASON_OF_MONTH,
    _resolve_cells,
)

DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_shoulder_online_span_steam_condbinned.json"
)

# `_scope_fleet` reads Resource Name / status / HASL / HSL / Base Point (it
# computes the excluded-resource disclosure from HASL+Base Point); the span
# itself needs only status + HSL. Read the union so `_scope_fleet` is reused
# verbatim (its unmapped-name hard error is the rule-23 hygiene we want).
_READ_COLS = [
    "SCED Time Stamp",
    "Resource Name",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "HSL",
    "Base Point",
]


def _accumulate_year(
    year: int,
) -> tuple[np.ndarray, np.ndarray, dict, dict[str, int], list[str]]:
    """Stream the year's shards into per-hour ON / non-OUT HSL sums.

    Returns ``(on_sum, nonout_sum, excluded, status_rows, files)`` where
    ``on_sum`` / ``nonout_sum`` are ``(HOURS,)`` HSL sums over every
    fleet resource-interval landing in each hour-of-year. The hourly ON share
    is ``on_sum / nonout_sum`` (the per-interval hourly-mean of the CC/CT
    derive reduces to this ratio exactly — mean(on)/mean(nonout) over the same
    intervals = sum(on)/sum(nonout)).
    """
    files = _sced_source_files(year)
    on_sum = np.zeros(HOURS)
    nonout_sum = np.zeros(HOURS)
    excluded: dict = {}
    status_rows: dict[str, int] = {}
    for path in files:
        chunk = pd.read_parquet(path, columns=_READ_COLS)
        chunk = _delivery_year_rows(chunk, year)
        chunk = chunk[chunk["Resource Type"].isin(ST_RESTYPES)]
        if chunk.empty:
            continue
        chunk = _coerce_sced_numeric(chunk)
        fleet, exc = _scope_fleet(chunk)
        _merge_excluded(excluded, exc)
        del chunk
        if fleet.empty:
            continue
        # CPT -> fixed CST -> non-leap hour-of-year (Feb 29 dropped to match the
        # model's 8760 clock and _netload_pct), the offer-wall derive's clock.
        ts = pd.to_datetime(fleet["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert(_STD_TZ)
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        f = fleet.loc[np.asarray(ok)].copy()
        if f.empty:
            continue
        hoy = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        stat = f["Telemetered Resource Status"].astype(str).str.strip()
        hsl = np.nan_to_num(f["HSL"].to_numpy(float), nan=0.0)
        is_on = stat.str.startswith("ON").to_numpy()
        is_nonout = (stat != "OUT").to_numpy()
        valid = (hoy >= 0) & (hoy < HOURS)
        np.add.at(on_sum, hoy[valid & is_on], hsl[valid & is_on])
        np.add.at(nonout_sum, hoy[valid & is_nonout], hsl[valid & is_nonout])
        for st, n in stat.value_counts().to_dict().items():
            status_rows[st] = status_rows.get(st, 0) + int(n)
        del f, fleet
    return on_sum, nonout_sum, excluded, status_rows, [p.name for p in files]


def derive_year(year: int) -> tuple[dict, dict, list[str]]:
    """Return ``({"ST": table-dict}, coverage, files)`` for one year."""
    on_sum, nonout_sum, excluded, status_rows, files = _accumulate_year(year)
    if not np.any(nonout_sum > 0.0):
        return {}, {}, files

    share = np.full(HOURS, np.nan)
    covered = nonout_sum > 0.0
    share[covered] = np.clip(on_sum[covered] / nonout_sum[covered], 0.0, 1.0)

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

    span, level, n_obs = _resolve_cells(share, hour_bin, season, block)
    out = {
        "ST": {
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
    }
    coverage = {
        "ST": {
            "covered_hours": int(covered.sum()),
            "cells_by_level": [int((level == lv).sum()) for lv in range(4)],
            "cells_unresolved": int((level == -1).sum()),
            "share_mean": round(float(np.nanmean(share)), 4),
            "share_p10_p50_p90": [
                round(float(np.nanpercentile(share, q)), 4) for q in (10, 50, 90)
            ],
        },
        "status_rows": status_rows,
        "excluded_non_fleet": excluded,
    }
    return out, coverage, files


def main() -> None:
    """Derive and write the ST_GAS conditional online-span JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    per_year: dict[int, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], coverage[str(y)], sources[str(y)] = derive_year(y)
        cov = coverage[str(y)].get("ST")
        if cov:
            span = np.array(
                [
                    [[np.nan if v is None else v for v in row] for row in mat]
                    for mat in per_year[y]["ST"]["span"]
                ],
                dtype=float,
            )
            bin_share = np.nanmean(span.reshape(span.shape[0], -1), axis=1)
            print(
                f"{y} ST: {cov['covered_hours']} corpus hours, cells by level "
                f"{cov['cells_by_level']} (unresolved {cov['cells_unresolved']}), "
                f"mean ON share {cov['share_mean']} "
                f"(p10/50/90 {cov['share_p10_p50_p90']})"
            )
            print(
                "        ON share by net-load bin (b0..b6): "
                + str(
                    [round(float(v), 3) if np.isfinite(v) else None for v in bin_share]
                )
            )

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965), "
                "full-year publication-month corpus (data/raw/ercot/"
                "YYYY-MM.part*.parquet), rows filtered to delivery years "
                + "-".join(str(y) for y in args.years)
                + "; publication files carry ~60-day-lagged delivery, so rows "
                "are delivery-year-filtered (2022 validation + 2026 locked-test "
                "rows carried in adjacent publication files excluded)"
            ),
            "method": (
                "per-hour ON share of non-OUT capability for the model's ST_GAS "
                "fleet (interval-summed HSL, hourly means; ON = telemetered "
                "ON*, non-OUT = every status except OUT — the measured DAM "
                "availability's only-OUT-is-out basis), aggregated to "
                "hierarchical conditional cell means (net-load percentile bin x "
                "season x 4h block, coverage-gated fallback to bin x block, "
                "bin x season, bin)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - wind "
                "- solar, the wall artifacts' shared axis) x calendar season x "
                "hour-of-day block — forward-native only; the per-hour ON "
                "series enters ONLY through these conditional means (rule 13 "
                "bright line)"
            ),
            "charter": (
                "docs/handoffs/ercot-stgas-shoulder-2026-07.md §9.4 design (ii) "
                "(the SCED-basis hour-grain state conditional for ST_GAS); the "
                "steam analogue of docs/handoffs/ercot-shoulder-online-"
                "envelope-2026-07.md (ERCOT-89 CC/CT span)"
            ),
            "fleet_scope": (
                "the model's own 17-plant ST_GAS fleet via the exact "
                "resource-name map shared with derive_ercot_sced_offer_wall_"
                "steam (36 corpus resources -> 16 plants; CFB absent, non-fleet "
                "CHP excluded and disclosed; an unmapped corpus name is a hard "
                "error, rule 23 hygiene)"
            ),
            "classes": {"ST": list(ST_RESTYPES)},
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "season_of_month": list(SEASON_OF_MONTH),
            "hour_block_hours": HOUR_BLOCK_H,
            "min_cell_hours": MIN_CELL_HOURS,
            "iso": "ERCOT",
            "year_scoped": (
                "NO pooled fallback by design (rule 13): a year absent from "
                "this artifact gets NO span mechanism (the full-span wall "
                "geometry is retained byte-identical). 2023-2025 all present "
                "from the full-year NP3-965 intake (2026-07-21); each year's "
                "table is derived only from that year's own telemetered status"
            ),
            "source_files": sources,
            "coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved"
            ),
        },
    }
    for y in args.years:
        if per_year[y] and "ST" in per_year[y]:
            result.setdefault("ST", {"years": {}})["years"][str(y)] = per_year[y]["ST"]

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
