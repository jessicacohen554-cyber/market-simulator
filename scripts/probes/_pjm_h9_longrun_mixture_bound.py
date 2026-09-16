"""pjm-h9 phase 0 — is PJM's LONG_RUN offer comparator biased by its gas-steam admixture?

ZERO LP. Rule 29 ``[R-SCREEN]`` clause 0, rule 32 ``[R-SHARD]`` (a): the parent runs no LP.
Pre-registration: ``docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md``.

THE QUESTION (``docs/RESULT-pjm-h8-minload-measured-offer-screen-2026-09-16.md`` §5, route b).
h8 priced PJM coal's min-load rungs at PJM's OWN published offers and the model's coal fell to
**12.70 TWh below** what PJM's coal actually generated. One of the two surviving readings is
that the comparator is not exact: the measured ``LONG_RUN`` segment is coal **plus** gas-steam
(216 units, median ``min_runtime`` > 16 h) and gas-steam bids dearer, so a coal-only comparison
against a blended ladder is biased HIGH.

WHY THIS IS NOT THE COAL-ONLY RE-DERIVE THE HANDOFF ASKED FOR. It cannot be: PJM's
``energy_market_offers`` feed publishes a MASKED ``unit_code`` and **no fuel column**, which is
why the whole derive family states its population rule as "Segments are selected by unit
PHYSICS, never fuel labels" (``derive_pjm_offer_surface.py`` L15). A coal-only ladder BY LABEL
is not obtainable from this source at any data cost.

WHAT THIS PROBE DOES INSTEAD — an EXACT bound that classifies nothing. The ladder value is the
capacity-weighted MEDIAN of the implied-gas-HR distribution. Writing the blended CDF as a
mixture with gas-steam capacity weight ``w``::

    F_blend = (1 - w) * F_coal + w * F_gas

and using only route (b)'s own premise that the admixture is ONE-SIDED (gas-steam bids dearer),
the coal-only median is bounded **exactly**::

    Q_blend(0.5 * (1 - w))  <=  median_coal  <=  Q_blend(0.5 * (1 + w))

``Q_blend`` comes from the SAME histogram the frozen derive already builds — the only change is
emitting the quantile function instead of only ``p = 0.5``. No unit is classified, no fuel is
inferred, and nothing is constructed here.

G-REPRO IS A HARD STOP (PRECOMMIT §5). This probe replicates the frozen derive's two passes
rather than refactoring it, so its ``p = 0.5`` column MUST reproduce the committed
``pjm_offer_midcurve_condbinned.json`` at every (segment, year, bin, share) cell to the
artifact's own 3-decimal rounding. If it does not, the replication or the corpus is wrong, the
quantiles are not trustworthy, and the probe FAILS rather than "adjusting" anything
(rule 23 ``[R-FROZEN-DERIVE]``).

Reports MULTIPLIERS ONLY, never prices — the PJM DataMiner2 redistribution restriction
(``docs/data-licensing.md`` §4), the same convention the derive itself follows.

Run: ``python3 scripts/probes/_pjm_h9_longrun_mixture_bound.py [--years 2023 2024 2025]``
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

from scripts.data.derive_pjm_offer_midcurve import (  # noqa: E402
    MULT_GRID,
    SHARES,
    _segments,
    _unit_physics,
)
from scripts.data.derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _month_files,
    _netload_pct,
    _pjm_fuel_daily,
)

FROZEN = CALIBRATION_DIR / "pjm_offer_midcurve_condbinned.json"
OUT = REPO / "results/calibration/_pjm_h9_longrun_mixture_bound.json"

#: Quantile grid the bound is read on. Dense enough that w is resolved to ~0.002
#: without interpolating between stored quantiles.
PGRID = np.round(np.arange(0.005, 0.9951, 0.005), 4)


def build_hist(years: list[int], edges: tuple[float, ...]) -> tuple:
    """Replicate the frozen derive's passes 1-2 and return the raw histogram.

    Verbatim replication of ``derive_pjm_offer_midcurve.main`` up to the point it
    collapses the histogram to a median — same population, same segments, same
    weights, same grid. G-REPRO proves the replication rather than assuming it.
    """
    files, coverage = _month_files(years)
    print(f"pass 1: unit physics over {len(files)} month files ...", flush=True)
    per_unit = _unit_physics(files)
    segments = _segments(per_unit)
    unit_seg = pd.Series("", index=per_unit.index, dtype=object)
    seg_cap = {}
    for seg, idx in segments.items():
        unit_seg.loc[idx] = seg
        seg_cap[seg] = {
            "n_units": int(len(idx)),
            "gw_union_of_medians": round(
                float(per_unit.loc[idx, "ecomax"].sum() / 1e3), 1
            ),
        }
        print(f"  segment {seg}: {seg_cap[seg]}")

    nl = _netload_pct(years, "within-year")
    fuel = _pjm_fuel_daily()
    n_bins = len(edges) + 1
    seg_names = sorted(segments)
    n_cells = len(MULT_GRID) + 1
    hist = np.zeros(
        (len(seg_names), len(years), n_bins, len(SHARES), n_cells), dtype=float
    )
    seg_pos = {s: i for i, s in enumerate(seg_names)}
    year_pos = {y: i for i, y in enumerate(years)}

    print("pass 2: mid-curve sampling ...", flush=True)
    for p in files:
        df = pd.read_parquet(
            p,
            columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
            + _BID_COLS
            + _MW_COLS,
        )
        df = df[df["avg_ecomax"] > 0.0]
        if df.empty:
            continue
        seg = df["unit_code"].astype(str).map(unit_seg).fillna("")
        df = df[seg != ""]
        seg = seg[seg != ""]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        day = ts.dt.normalize()
        he = (ts.dt.hour + 1).astype("int16")
        key = pd.DataFrame({"day": day.to_numpy(), "he": he.to_numpy()})
        q = key.merge(nl, on=["day", "he"], how="left")["q"].to_numpy(float)
        gas = fuel.reindex(pd.DatetimeIndex(day)).to_numpy(float)
        hbin = np.searchsorted(np.asarray(edges), q, side="right")
        year = ts.dt.year.to_numpy()

        mws = df[_MW_COLS].to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        w = df["avg_ecomax"].to_numpy(float)
        ok = np.isfinite(q) & np.isfinite(gas) & (gas > 0.0)
        mw_max = np.nanmax(mws, axis=1)
        ok &= mw_max > 0.0
        rows = np.where(ok)[0]
        if rows.size == 0:
            continue
        mws_r = mws[rows]
        bids_r = bids[rows]
        share_curve = mws_r / mw_max[rows][:, None]
        share_sorted = np.where(np.isfinite(share_curve), share_curve, np.inf)
        gas_r = gas[rows]
        seg_idx = seg.iloc[rows].map(seg_pos).to_numpy()
        yr_idx = np.array([year_pos.get(int(y), -1) for y in year[rows]])
        bin_r = hbin[rows]
        w_r = w[rows]
        keep = yr_idx >= 0
        for si, s in enumerate(SHARES):
            pos = (share_sorted < s).sum(axis=1)
            pos = np.minimum(pos, np.isfinite(share_curve).sum(axis=1) - 1)
            price = bids_r[np.arange(len(rows)), pos]
            mult = price / gas_r
            cell = np.searchsorted(MULT_GRID, mult, side="right")
            m = keep & np.isfinite(mult)
            np.add.at(hist, (seg_idx[m], yr_idx[m], bin_r[m], si, cell[m]), w_r[m])
        print(f"  [pass2] {p.name}: {rows.size} rows", flush=True)

    return hist, seg_names, seg_cap, coverage


#: The derive's own grid-midpoint convention, copied verbatim.
GRID_MID = np.concatenate([MULT_GRID - 0.025, [MULT_GRID[-1] + 0.025]])


def quantile(h: np.ndarray, p: float) -> float:
    """Cap-weighted quantile of one histogram cell — the derive's ``_median`` at p=0.5."""
    tot = h.sum()
    if tot <= 0.0:
        return float("nan")
    cw = np.cumsum(h)
    return float(GRID_MID[int(np.searchsorted(cw, p * tot))])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    args = ap.parse_args(argv)
    t0 = time.time()

    edges = tuple(args.edges)
    hist, seg_names, seg_cap, coverage = build_hist(args.years, edges)
    n_bins = len(edges) + 1

    # ---- G-REPRO: the frozen artifact must be reproduced at every cell -------
    frozen = json.loads(FROZEN.read_text())
    mismatches = []
    checked = 0
    for s, seg in enumerate(seg_names):
        entry = frozen.get(seg)
        if not entry:
            continue
        for y, yr in enumerate(args.years):
            lad = entry.get("years", {}).get(str(yr))
            if not lad:
                continue
            for b in range(n_bins):
                for si, share in enumerate(SHARES):
                    want = lad[b][si][1]
                    got = round(quantile(hist[s, y, b, si], 0.5), 3)
                    checked += 1
                    a = float("nan") if want is None else float(want)
                    if not ((np.isnan(a) and np.isnan(got)) or abs(a - got) <= 1e-9):
                        mismatches.append(
                            {
                                "segment": seg,
                                "year": yr,
                                "bin": b,
                                "share": round(float(share), 3),
                                "frozen": want,
                                "reproduced": got,
                            }
                        )
    print(
        f"\nG-REPRO: {checked} cells checked against the frozen artifact, "
        f"{len(mismatches)} mismatches"
    )
    if mismatches:
        for m in mismatches[:15]:
            print("   MISMATCH", m)
        print(
            "\nG-REPRO FAILED — the replication or the corpus does not match the frozen\n"
            "surface, so the quantiles are NOT trustworthy. Stopping (PRECOMMIT §5)."
        )
        OUT.write_text(
            json.dumps(
                {
                    "g_repro": {
                        "pass": False,
                        "cells_checked": checked,
                        "mismatches": mismatches[:200],
                    }
                },
                indent=1,
            )
        )
        return 1

    # ---- the quantile function, per cell ------------------------------------
    out: dict = {
        "what": (
            "cap-weighted quantile function of the implied-gas-HR offer distribution "
            "per (segment, delivery year, net-load bin, within-unit share); the frozen "
            "derive's ladder is the p=0.5 column. MULTIPLIERS ONLY (PJM DataMiner2 "
            "redistribution restriction)."
        ),
        "precommit": "docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md",
        "g_repro": {"pass": True, "cells_checked": checked, "mismatches": 0},
        "segment_capacity": seg_cap,
        "month_coverage": coverage,
        "netload_pct_edges": list(edges),
        "shares": [round(float(x), 3) for x in SHARES],
        "pgrid": [float(p) for p in PGRID],
        "quantiles": {},
    }
    for s, seg in enumerate(seg_names):
        per_year: dict = {}
        for y, yr in enumerate(args.years):
            bins = []
            for b in range(n_bins):
                bins.append(
                    [
                        [round(float(quantile(hist[s, y, b, si], p)), 4) for p in PGRID]
                        for si in range(len(SHARES))
                    ]
                )
            per_year[str(yr)] = bins
        out["quantiles"][seg] = per_year

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
