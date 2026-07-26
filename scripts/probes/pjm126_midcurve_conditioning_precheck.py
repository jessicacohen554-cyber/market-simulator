"""pjm-126 no-LP diagnostic: is the mid-curve surface's tightest-bin inversion REAL, or an artifact of the derive's conditioning?

Frontier Lane 2 (`docs/handoffs/pjm-frontier-path-2026-07.md` §3). The measured
PJM mid-curve offer surface
(``data/raw/_validation-source/pjm_offer_midcurve_condbinned.json``) prices
EVERY physics segment cheapest — or near-cheapest — in its TIGHTEST net-load
bin (2025 tables, x delivered gas, edges [0.80, 0.90, 0.97]):

    segment              bin0        bin1        bin2      bin3 (tightest)
    CT_FAST (s05-85)  26.5-30.9   32.0-33.9   32.7-34.5      22.5-25.2
    CC_LIKE  (body)    ~4.9-5.1   5.17-5.42   5.08-5.53       4.83-4.92
    LONG_RUN  (top)    8.57-8.97   8.28-8.62   8.18-8.62       8.07-8.47

pjm-123 concluded from this that ANY mechanism handing a class its measured
conditional level inherits the inversion and COMPRESSES top-end dispersion
instead of widening it — closing the whole measured-offer-surface family as
PJM's dispersion lever. It is not a gas artifact: bin3's own mean delivered gas
is the LOWEST of the four ($4.03 vs $4.53 in bin1), so a constant dollar offer
would read as a HIGHER multiplier there, not a lower one.

THE HYPOTHESIS UNDER TEST (handoff §3, stated there as a hypothesis, not a
claim): within-**year** net-load percentile puts winter evening peaks and
summer scarcity into the SAME bin3, and the units offering in those hours are
largely already committed — so the offers SUBMITTED in bin3 come from a
different population than the offers that SET the price. If so, the inversion
is a property of the conditioning, not of PJM's offers.

WHAT THIS PROBE DOES AND DOES NOT DO. It recomputes the ladder under
ALTERNATIVE conditionings and compares. It **writes no surface, re-derives
nothing, and touches no keeper**. Rule 20 binds: derive scripts are frozen
against residuals, and a re-derivation commit must cite a data or
conditioning-DEFINITION change, never a residual movement. A season split or a
committed/uncommitted split IS a definitional change and would be admissible on
that basis alone — but making it is a SEPARATE, owner-authorized step requiring
its own admissibility memo. This probe only measures whether the conditioning
is load-bearing.

THE THREE ARMS, all on one corpus, one segmentation, one gas series:

  A_frozen   the committed method: net-load percentile ranked WITHIN YEAR.
             Doubles as the fidelity guard — it must reproduce the committed
             JSON's own ladders, or nothing downstream means anything.
  B_season   percentile ranked WITHIN SEASON (PJM's own seasonal convention:
             summer Jun-Sep, winter Dec-Mar, shoulder Apr/May/Oct/Nov), same
             edges. Tests the season-MIXING half of the hypothesis: if bin3's
             cheapness comes from pooling winter and summer peaks, ranking
             inside each season removes it.
  C_fixedpop the frozen conditioning, restricted to units that offer in ALL
             FOUR bins. Tests the POPULATION half: if bin3 looks cheap because
             a different set of units offers there, holding the population
             fixed removes it.

THE INVERSION GAP, per segment, is measured on that segment's own diagnostic
share band (the band the pjm-123 table quoted):

    gap = median(bin2 ladder) - median(bin3 ladder)   [positive = inversion]
    CT_FAST / CC_LIKE  -> shares 0.05..0.85 (the body)
    LONG_RUN           -> shares 0.85..0.99 (the top)

PRE-REGISTERED DECISION CRITERIA (written and committed BEFORE the probe was
run, and before any arm was inspected):

  ARTIFACT — the inversion is a conditioning artifact if, in **at least 2 of 3
     segments**, arm B **or** arm C either FLIPS the gap's sign (bin3 no longer
     cheaper than bin2) or NARROWS it by >= 50% versus arm A.
     Consequence: pjm-123 §3's generalization narrows to "the surface AS
     CONDITIONED in the 2026-07 vintage", the measured surface becomes a live
     candidate dispersion lever again, and **Lane 2 stays OPEN** — a frontier
     declaration would be premature.

  REAL — the inversion is a property of PJM's offers if, in **at least 2 of 3
     segments**, BOTH arm B and arm C preserve the gap's sign AND narrow it by
     < 50%.
     Consequence: pjm-123 §3 stands as written, the measured-offer-surface
     family stays closed as a dispersion lever, and **Lane 2 CLOSES**.

  INDETERMINATE — anything else (the arms disagree, or the segments split
     without a 2-of-3 majority). Reported as such and escalated to the owner.
     **No re-derive, and Lane 2 does NOT close on an indeterminate result.**

  FIDELITY GUARD (hard stop) — arm A must reproduce the committed JSON's
     ladders for every solved year to within one histogram cell (0.05 on the
     mult). A reconstruction that does not reproduce the frozen surface is not
     measuring the frozen surface, and the run aborts rather than reporting.

Note on direction: this probe is run by a session that has an interest in the
REAL outcome (it would close Lane 2 and complete the frontier ledger). The
criteria above are therefore symmetric, quantitative, and were committed to git
before the first arm was computed; the ARTIFACT branch is spelled out with the
same specificity as the REAL branch precisely so it cannot be talked past.

Pure diagnostic, no LP, no writes outside ``--json-out``. Usage:

    python scripts/probes/pjm126_midcurve_conditioning_precheck.py \
        --years 2023 2024 2025 \
        --json-out results/calibration/pjm126_conditioning_precheck.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_pjm_offer_midcurve import (  # noqa: E402
    MULT_GRID,
    OUT_JSON,
    SHARES,
    _segments,
    _unit_physics,
)
from derive_pjm_offer_surface import (  # noqa: E402
    _BID_COLS,
    _MW_COLS,
    _month_files,
    _netload_pct,
    _pjm_fuel_daily,
)

#: Arm names, in report order.
ARMS = ("A_frozen", "B_season", "C_fixedpop")

#: Seasonal conditioning for arm B — PJM's own convention (summer delivery
#: period Jun-Sep; winter Dec-Mar; the rest shoulder). A DEFINITIONAL choice
#: fixed before the run, never tuned against any result.
SEASON_OF_MONTH = {
    1: "winter",
    2: "winter",
    3: "winter",
    12: "winter",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "summer",
    4: "shoulder",
    5: "shoulder",
    10: "shoulder",
    11: "shoulder",
}

#: Per-segment diagnostic share band (the band the pjm-123 table quoted).
SEGMENT_BAND = {
    "CT_FAST": (0.05, 0.85),
    "CC_LIKE": (0.05, 0.85),
    "LONG_RUN": (0.85, 0.99),
}

#: Pre-registered decision thresholds.
GAP_NARROW_FRAC = 0.50  # >= this narrowing (or a sign flip) reads as ARTIFACT
MIN_SEGMENTS = 2  # of 3, for either verdict
FIDELITY_TOL = 0.05  # one histogram cell on the mult


def season_netload_pct(years: list[int]) -> pd.DataFrame:
    """Return ``(day, he) -> within-SEASON net-load percentile`` for arm B.

    Identical construction to
    :func:`derive_pjm_offer_surface._netload_pct` — same EIA-930 PJM series,
    same gap-bridged frame, same ``Demand - WND - SUN`` definition, same DST
    fall-back handling — except the percentile rank is taken **within
    (year, season)** instead of within year.

    Args:
        years: Delivery years to rank.

    Returns:
        Frame with columns ``day``, ``he``, ``q``.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    frames = []
    for year in years:
        df = _eia_hourly_frame_filled("PJM", year)
        if df is None:
            raise SystemExit(f"EIA-930 PJM {year}: no clean 8760 frame")
        net = (
            pd.to_numeric(df["Demand"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: WND"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
            - pd.to_numeric(df["NG: SUN"], errors="coerce")
            .interpolate(limit_direction="both")
            .to_numpy(float)
        )
        local = pd.DatetimeIndex(df["Local time"])
        # NA-safe month map: a NaT "Local time" row (the 2023 fall-back day)
        # carries no (day, he) merge key and is dropped from every arm at the
        # finite-q filter; mapping its month through NaN reproduces arm A's
        # behaviour instead of crashing on an int cast. Mechanical fix only —
        # the season definition is untouched.
        season = pd.Series(local.month).map(SEASON_OF_MONTH)
        q = pd.Series(net).groupby(season.to_numpy()).rank(pct=True).to_numpy()
        frames.append(
            pd.DataFrame({"day": local.normalize(), "he": local.hour + 1, "q": q})
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(["day", "he"], as_index=False).agg(q=("q", "mean"))


def bin_presence(files, unit_seg, nl, edges, hours_years):
    """Return ``{unit: bitmask of bins it offers in}`` under the frozen conditioning.

    Cheap pre-pass for arm C: reads three columns per month file and records,
    per unit, which net-load bins it ever submits an offer in.

    Args:
        files: Monthly raw offer parquets.
        unit_seg: ``unit -> segment`` mapping (non-segment units excluded).
        nl: Frozen ``(day, he) -> q`` conditioning frame.
        edges: Bin edges.
        hours_years: Set of delivery years in scope.

    Returns:
        Dict of ``unit_code -> int`` bitmask over bin indices.
    """
    seen: dict[str, int] = {}
    for p in files:
        df = pd.read_parquet(
            p, columns=["bid_datetime_beginning_ept", "unit_code", "avg_ecomax"]
        )
        df = df[df["avg_ecomax"] > 0.0]
        if df.empty:
            continue
        seg = df["unit_code"].astype(str).map(unit_seg).fillna("")
        df = df[seg != ""]
        if df.empty:
            continue
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        keep = ts.dt.year.isin(hours_years).to_numpy()
        if not keep.any():
            continue
        key = pd.DataFrame(
            {"day": ts.dt.normalize().to_numpy(), "he": (ts.dt.hour + 1).to_numpy()}
        )
        q = key.merge(nl, on=["day", "he"], how="left")["q"].to_numpy(float)
        hbin = np.searchsorted(np.asarray(edges), q, side="right")
        units = df["unit_code"].astype(str).to_numpy()
        ok = keep & np.isfinite(q)
        for u, b in zip(units[ok], hbin[ok]):
            seen[u] = seen.get(u, 0) | (1 << int(b))
        print(f"  [presence] {p.name}", flush=True)
    return seen


def accumulate(files, unit_seg, seg_pos, year_pos, conditionings, edges, keep_units):
    """Accumulate the ``(arm, seg, year, bin, share, cell)`` MW-weighted histogram.

    One pass over the corpus for every arm at once — the arms differ only in
    which conditioning frame supplies ``q`` (and, for ``C_fixedpop``, which
    units are kept), so sharing the pass keeps them exactly comparable.

    The within-unit share sampling, the implied-HR normalisation and the
    histogram grid are the frozen derive's, reused verbatim.

    Args:
        files: Monthly raw offer parquets.
        unit_seg: ``unit -> segment`` mapping.
        seg_pos: ``segment -> index``.
        year_pos: ``year -> index``.
        conditionings: ``{arm: (day, he) -> q frame}``.
        edges: Bin edges.
        keep_units: ``{arm: set|None}`` — unit restriction per arm (None = all).

    Returns:
        ``(n_arms, n_seg, n_years, n_bins, n_shares, n_cells)`` float array.
    """
    fuel = _pjm_fuel_daily()
    n_bins = len(edges) + 1
    hist = np.zeros(
        (
            len(ARMS),
            len(seg_pos),
            len(year_pos),
            n_bins,
            len(SHARES),
            len(MULT_GRID) + 1,
        ),
        dtype=float,
    )
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
        key = pd.DataFrame({"day": day.to_numpy(), "he": (ts.dt.hour + 1).to_numpy()})
        gas = fuel.reindex(pd.DatetimeIndex(day)).to_numpy(float)
        year = ts.dt.year.to_numpy()
        units = df["unit_code"].astype(str).to_numpy()
        mws = df[_MW_COLS].to_numpy(float)
        bids = df[_BID_COLS].to_numpy(float)
        w = df["avg_ecomax"].to_numpy(float)
        mw_max = np.nanmax(mws, axis=1)
        seg_idx_all = seg.map(seg_pos).to_numpy()
        yr_idx_all = np.array([year_pos.get(int(y), -1) for y in year])

        for ai, arm in enumerate(ARMS):
            q = key.merge(conditionings[arm], on=["day", "he"], how="left")[
                "q"
            ].to_numpy(float)
            ok = (
                np.isfinite(q)
                & np.isfinite(gas)
                & (gas > 0.0)
                & (mw_max > 0.0)
                & (yr_idx_all >= 0)
            )
            if keep_units[arm] is not None:
                ok &= np.isin(units, list(keep_units[arm]))
            rows = np.where(ok)[0]
            if rows.size == 0:
                continue
            hbin = np.searchsorted(np.asarray(edges), q[rows], side="right")
            share_curve = mws[rows] / mw_max[rows][:, None]
            share_sorted = np.where(np.isfinite(share_curve), share_curve, np.inf)
            n_pts = np.isfinite(share_curve).sum(axis=1)
            bids_r = bids[rows]
            gas_r = gas[rows]
            w_r = w[rows]
            s_r = seg_idx_all[rows]
            y_r = yr_idx_all[rows]
            for si, s in enumerate(SHARES):
                pos = np.minimum((share_sorted < s).sum(axis=1), n_pts - 1)
                mult = bids_r[np.arange(rows.size), pos] / gas_r
                cell = np.searchsorted(MULT_GRID, mult, side="right")
                m = np.isfinite(mult)
                np.add.at(hist, (ai, s_r[m], y_r[m], hbin[m], si, cell[m]), w_r[m])
        print(f"  [accum] {p.name}: {len(df)} rows", flush=True)
    return hist


def median_of(h: np.ndarray) -> float:
    """Return the cap-weighted median mult of one histogram row.

    The frozen derive's estimator, reused verbatim so arm A is comparable to
    the committed surface cell for cell.

    Args:
        h: One ``(n_cells,)`` MW-weighted histogram.

    Returns:
        The weighted median multiplier, or NaN when the row is empty.
    """
    grid_mid = np.concatenate([MULT_GRID - 0.025, [MULT_GRID[-1] + 0.025]])
    tot = h.sum()
    if tot <= 0.0:
        return float("nan")
    return float(grid_mid[int(np.searchsorted(np.cumsum(h), 0.5 * tot))])


def band_median(hist, ai, si_seg, yi, b, seg_name) -> float:
    """Return the median ladder value over a segment's diagnostic share band.

    Args:
        hist: The accumulated histogram.
        ai: Arm index.
        si_seg: Segment index.
        yi: Year index, or ``None`` to pool years.
        b: Bin index.
        seg_name: Segment name (selects the band).

    Returns:
        Median across the band's shares.
    """
    lo, hi = SEGMENT_BAND[seg_name]
    vals = []
    for si, share in enumerate(SHARES):
        if not (lo - 1e-9 <= share <= hi + 1e-9):
            continue
        h = (
            hist[ai, si_seg, :, b, si].sum(axis=0)
            if yi is None
            else hist[ai, si_seg, yi, b, si]
        )
        v = median_of(h)
        if np.isfinite(v):
            vals.append(v)
    return float(np.median(vals)) if vals else float("nan")


def main() -> int:
    """Run the three arms, evaluate the pre-registered criteria, report."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--edges", nargs="*", type=float, default=[0.80, 0.90, 0.97])
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--skip-fidelity",
        action="store_true",
        help="Report the arm-A vs committed-JSON deviation instead of hard-stopping "
        "on it. ONLY legitimate when --years is a strict subset of the committed "
        "surface's years, where segmentation differs by construction.",
    )
    args = ap.parse_args()

    files, coverage = _month_files(args.years)
    print(f"pass 1: unit physics over {len(files)} month files ...", flush=True)
    per_unit = _unit_physics(files)
    segments = _segments(per_unit)
    unit_seg = pd.Series("", index=per_unit.index, dtype=object)
    for seg, idx in segments.items():
        unit_seg.loc[idx] = seg
        print(f"  segment {seg}: {len(idx)} units", flush=True)
    unit_seg = unit_seg[unit_seg != ""]

    seg_names = sorted(segments)
    seg_pos = {s: i for i, s in enumerate(seg_names)}
    year_pos = {y: i for i, y in enumerate(args.years)}
    edges = tuple(args.edges)

    nl_frozen = _netload_pct(args.years)
    nl_season = season_netload_pct(args.years)

    print("pass 2: bin presence (arm C population) ...", flush=True)
    presence = bin_presence(files, unit_seg, nl_frozen, edges, set(args.years))
    all_bins = (1 << (len(edges) + 1)) - 1
    fixed_pop = {u for u, mask in presence.items() if mask == all_bins}
    print(
        f"  {len(fixed_pop)} of {len(presence)} units offer in ALL "
        f"{len(edges) + 1} bins (arm C population)",
        flush=True,
    )

    print("pass 3: ladder accumulation, all arms ...", flush=True)
    hist = accumulate(
        files,
        unit_seg,
        seg_pos,
        year_pos,
        {"A_frozen": nl_frozen, "B_season": nl_season, "C_fixedpop": nl_frozen},
        edges,
        {"A_frozen": None, "B_season": None, "C_fixedpop": fixed_pop},
    )

    # ---- fidelity guard ---------------------------------------------------
    committed = json.loads(OUT_JSON.read_text())
    worst, worst_where = 0.0, ""
    for seg_name in seg_names:
        si_seg = seg_pos[seg_name]
        for yi, yr in enumerate(args.years):
            lad = committed.get(seg_name, {}).get("years", {}).get(str(yr))
            if lad is None:
                continue
            for b in range(len(edges) + 1):
                for si, (_share, ref) in enumerate(lad[b]):
                    got = median_of(hist[0, si_seg, yi, b, si])
                    if not (np.isfinite(got) and np.isfinite(ref)):
                        continue
                    d = abs(got - ref)
                    if d > worst:
                        worst, worst_where = d, f"{seg_name}/{yr}/bin{b}/s{_share}"
    print(
        f"\nfidelity: worst arm-A vs committed deviation {worst:.3f} "
        f"at {worst_where} (tol {FIDELITY_TOL})"
    )
    if worst > FIDELITY_TOL and not args.skip_fidelity:
        raise SystemExit(
            f"arm A does not reproduce the committed surface (worst {worst:.3f} > "
            f"{FIDELITY_TOL} at {worst_where}) — this is not measuring the frozen "
            "surface; aborting rather than reporting"
        )

    # ---- the inversion gap, per arm, per segment --------------------------
    rows, verdict_seg = [], {}
    for seg_name in seg_names:
        si_seg = seg_pos[seg_name]
        gaps = {}
        for ai, arm in enumerate(ARMS):
            b2 = band_median(hist, ai, si_seg, None, 2, seg_name)
            b3 = band_median(hist, ai, si_seg, None, 3, seg_name)
            gaps[arm] = b2 - b3
            rows.append(
                {
                    "segment": seg_name,
                    "arm": arm,
                    "bin2": round(b2, 3),
                    "bin3": round(b3, 3),
                    "gap": round(b2 - b3, 3),
                }
            )
        base = gaps["A_frozen"]
        seg_flags = {}
        for arm in ("B_season", "C_fixedpop"):
            g = gaps[arm]
            if not np.isfinite(g) or not np.isfinite(base) or base == 0.0:
                seg_flags[arm] = "NA"
            elif np.sign(g) != np.sign(base):
                seg_flags[arm] = "FLIP"
            elif abs(g) <= (1.0 - GAP_NARROW_FRAC) * abs(base):
                seg_flags[arm] = "NARROW"
            else:
                seg_flags[arm] = "HOLDS"
        verdict_seg[seg_name] = {"gaps": gaps, "flags": seg_flags}

    print("\n-- inversion gap (bin2 - bin3; positive = bin3 cheaper) --")
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    print("\n-- per-segment flags vs arm A --")
    for seg_name, v in verdict_seg.items():
        print(
            f"  {seg_name:9} A={v['gaps']['A_frozen']:+.3f}  "
            f"B_season={v['gaps']['B_season']:+.3f} [{v['flags']['B_season']}]  "
            f"C_fixedpop={v['gaps']['C_fixedpop']:+.3f} [{v['flags']['C_fixedpop']}]"
        )

    n_artifact = sum(
        1
        for v in verdict_seg.values()
        if "FLIP" in v["flags"].values() or "NARROW" in v["flags"].values()
    )
    n_real = sum(
        1
        for v in verdict_seg.values()
        if all(f == "HOLDS" for f in v["flags"].values())
    )
    if n_artifact >= MIN_SEGMENTS:
        verdict = "ARTIFACT"
    elif n_real >= MIN_SEGMENTS:
        verdict = "REAL"
    else:
        verdict = "INDETERMINATE"

    print(
        f"\n  segments reading ARTIFACT: {n_artifact}/3   "
        f"segments reading REAL: {n_real}/3"
    )
    print(f"\n  VERDICT: {verdict}")
    if verdict == "ARTIFACT":
        print("  => pjm-123 §3 narrows to the 2026-07 conditioning vintage;")
        print("     the measured surface is a live lever again; Lane 2 STAYS OPEN.")
    elif verdict == "REAL":
        print("  => pjm-123 §3 stands as written; the surface stays closed as a")
        print("     dispersion lever; Lane 2 CLOSES.")
    else:
        print("  => escalate to the owner; no re-derive; Lane 2 does NOT close.")
    print()

    report = {
        "probe": "pjm126_midcurve_conditioning_precheck",
        "years": args.years,
        "edges": list(edges),
        "coverage": coverage,
        "segment_units": {s: int(len(segments[s])) for s in seg_names},
        "fixed_pop_units": len(fixed_pop),
        "presence_units": len(presence),
        "fidelity_worst_dev": worst,
        "fidelity_worst_where": worst_where,
        "gap_table": rows,
        "per_segment": {
            s: {
                "gaps": {a: float(v["gaps"][a]) for a in ARMS},
                "flags": v["flags"],
            }
            for s, v in verdict_seg.items()
        },
        "n_artifact_segments": n_artifact,
        "n_real_segments": n_real,
        "verdict": verdict,
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2))
        print(f"  wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
