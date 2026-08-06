"""caiso-178 — derive CAISO's battery DAM discharge bid FLOOR from OASIS ``PUB_DAM_GRP``.

WHY THIS DERIVER EXISTS
-----------------------
``ScenarioConfig.battery_dispatch_adder = 5.0`` is CAISO's last genuinely free
residual-identified DOF entry. caiso-176 established, model-free, that the
fleet's DAM discharge marginal cost is **<= $15/MWh in all three training
years** — from the ``bid_stack`` sheet of CAISO's own Daily Energy Storage
Report. That instrument BOUNDS the parameter but cannot IDENTIFY it: its
published grain is a **15 $/MWh-wide bucket exactly where the parameter
lives** (``(0,15]``, carrying 8.72/16.43/17.52 % of priced DAM discharge).

OASIS ``PUB_DAM_GRP`` carries the ACTUAL piecewise breakpoint PRICES at
masked-resource grain, so it attacks the wall at the point the wall is made
of — resolution. It cannot remove the wall's other half: a bid is bounded
BELOW by marginal cost, which is what makes the one-sided inference valid and
is exactly what stops it becoming a two-sided identification.

THE TWO INSTRUMENTS ARE COMPLEMENTS, AND THAT IS THE DESIGN
-----------------------------------------------------------
  bid_stack (caiso-176)  : 15 $/MWh buckets, but LABELLED (RES_TYPE LESR/HYBD)
  PUB_DAM_GRP (this)     : exact $/MWh breakpoints, but MASKED (no fuel/location)

Each supplies what the other lacks, so CAISO's own labelled aggregate is used
here to VALIDATE a price-blind classifier built on the unlabelled corpus (gate
H1b). No new assumption is imported to do it.

PRE-REGISTRATION
----------------
Every classifier stage, gate and threshold below is fixed in
``results/calibration/PRECHECK-caiso178-public-bids-2026-08-06.md``, which was
committed and pushed BEFORE any bid price was read. This module implements
that document; it does not extend it.

THE CLASSIFIER IS PRICE-BLIND BY CONSTRUCTION
---------------------------------------------
S0  universe          RESOURCE_TYPE=GENERATOR, product=EN, row_kind=segment
S1  withdrawal-hour   min(segment_mw) <= -1 AND max(segment_mw) >= +1
S2  set S             >= 50 % of the year's EN curve-hours withdrawal-capable
                      AND >= 500 EN curve-hours in the year
S3  set B             S restricted by power symmetry
                      sym = |p05(min_mw)| / p95(max_mw) in [0.5, 2.0]
S4  set B_noPS        B minus large-stable-preexisting (>= 200 MW, present all
                      three years, < 10 % p95(max_mw) drift) — pumped storage

No price enters ANY stage. Every price-side result is therefore an
out-of-construction test of the classifier (rules 1/13).

KNOWN CONTAMINATION AND THE SIGN OF ITS BIAS (declared before the answer)
-------------------------------------------------------------------------
HYBD hybrids bid DEEPLY NEGATIVE (caiso-176 §3b) and pumped storage has a very
low throughput cost, so every contaminant this classifier can admit biases a
lower envelope DOWN — i.e. only ever toward CHANGING the incumbent. A high
result is trustworthy; a low result must survive the H1c sensitivity grid.

THE STATISTIC — the LOWER envelope, never the upper rungs
----------------------------------------------------------
Per (resource, hour) storage curve, the price at which the resource offers its
FIRST DISCHARGE MWh:

  p_hi = price at min{segment_mw : segment_mw >= 0}   conservative, biased UP
  p_lo = price at max{segment_mw : segment_mw <= 0}   aggressive, biased DOWN

The true reservation price is BRACKETED by [p_lo, p_hi]. The headline uses
``p_hi``, because only ``p_hi`` is unambiguously an offer to DISCHARGE.

A storage energy bid is an OPPORTUNITY-COST object, which the LP already
generates endogenously through SOC + RTE; the upper rungs are equilibrium
objects presuming the scarcity the model lacks (ERCOT-162; caiso-176 §3a).
Only the lower envelope is used. Fleet statistic = MEDIAN OVER RESOURCES of
each resource's own ``q05`` of ``p_hi`` — resource-weighted, so one
heavily-bidding resource cannot set the fleet number.

Bid-curve volume convention: the published curve is a step function with price
``p_i`` applying on ``[mw_i, mw_{i+1})``, so discharge volume priced at ``p_i``
is ``mw_{i+1} - max(mw_i, 0)`` for every segment whose top edge is positive.
The top breakpoint has no interval above it and contributes zero.

Usage::

    uv run python scripts/data/derive_caiso_battery_bid_floor.py
    uv run python scripts/data/derive_caiso_battery_bid_floor.py --years 2024

Writes (all committed — the zips are gitignored, the derivation is not):
    results/calibration/_caiso178_public_bid_floor.json      gate record
    results/calibration/_caiso178_bid_floor_resources.csv    per resource-year
    results/calibration/_caiso178_bid_floor_hist.csv         $0.25-grid histogram
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.lib.dam_public_bids.caiso import parse_day  # noqa: E402

ZIPS = REPO / "data" / "raw" / "caiso-public-bids" / "zips"
OUT_JSON = REPO / "results" / "calibration" / "_caiso178_public_bid_floor.json"
OUT_RES = REPO / "results" / "calibration" / "_caiso178_bid_floor_resources.csv"
OUT_HIST = REPO / "results" / "calibration" / "_caiso178_bid_floor_hist.csv"
#: caiso-176's committed bucket vocabulary — read, never re-declared here.
BIDSTACK_JSON = REPO / "results" / "calibration" / "_caiso176_bidstack_reservation.json"

YEARS = (2023, 2024, 2025)

# ---------------------------------------------------------------------------
# Pre-registered thresholds (PRECHECK-caiso178 §3, §4, §5). None is tunable.
# ---------------------------------------------------------------------------
WD_MW_EPS = 1.0  # S1: |MW| that counts as a real withdrawal / injection range
S2_WD_FRAC = 0.50  # S2: share of EN curve-hours that must be withdrawal-capable
S2_MIN_HOURS = 500  # S2: minimum EN curve-hours in the year
S3_SYM_LO, S3_SYM_HI = 0.5, 2.0  # S3: power-symmetry band
S4_PS_MW = 200.0  # S4: "large" threshold for the pumped-storage exclusion
S4_PS_DRIFT = 0.10  # S4: max p95(max_mw) drift across all three years
H1A_TOL = 0.25  # H1a: +/-25 % against the measured capacity envelope
H1B_MAD_PP = 5.0  # H1b: max mean absolute bucket deviation, percentage points
H1C_MAX_SPREAD = 1.00  # H1c: max headline movement across the sensitivity grid
MODE_GRID = 0.25  # $/MWh grid for the mass-point test
MODE_MIN_SHARE = 0.20  # >= 20 % of resource-hours in one bin, every year
MODE_WINDOW = 0.50  # +/- $ window reported alongside the bare bin
MODE_STABILITY = 1.00  # the three yearly modes must lie inside a $1.00 window
CAISO_BOUND = 15.0  # caiso-176's model-free upper bound; admissibility screen

#: Independently MEASURED CAISO battery capacity envelope (caiso-174's
#: ``caiso_storage_shape_anchor``) — the H1a reference. Not derived here.
MEASURED_BATTERY_MW = {2023: 4256.5, 2024: 6914.6, 2025: 9550.3}

#: Known CAISO pumped-storage fleet (FINDING-caiso140 §B) — the S4 cross-check.
CAISO_PS_FLEET_MW = 2078.0


@lru_cache(maxsize=1)
def _bucket_edges() -> tuple[tuple[str, float, float], ...]:
    """caiso-176's 11 published price buckets, read from its committed record."""
    rec = json.loads(BIDSTACK_JSON.read_text())
    return tuple((b["label"], b["low"], b["high"]) for b in rec["bucket_edges"])


def _published_lesr_shares() -> dict[int, dict[str, float]]:
    """caiso-176's committed IFM|LESR discharge shares — the H1b reference."""
    rec = json.loads(BIDSTACK_JSON.read_text())
    panel = rec["discharge_stack"]["IFM|LESR"]
    out: dict[int, dict[str, float]] = {}
    for year, blk in panel.items():
        out[int(year)] = {
            row["bucket"]: float(row["share_of_priced"])
            for row in blk["share_by_bucket_of_priced"]
        }
    return out


def _day_records(path: Path) -> dict | None:
    """Reduce one daily zip to compact per-resource records.

    Returns ``None`` when the file cannot be parsed (reported as a coverage
    hole, never silently skipped). The returned payload is deliberately small
    so it can cross a process boundary cheaply.
    """
    try:
        df = parse_day(path)
    except Exception as exc:  # noqa: BLE001 — a bad day is coverage, not a crash
        return {"path": path.name, "error": repr(exc)}

    edges = _bucket_edges()
    gen = df[
        (df["resource_type"] == "GENERATOR")
        & (df["product"] == "EN")
        & (df["row_kind"] == "segment")
    ]
    ss = df[
        (df["resource_type"] == "GENERATOR")
        & (df["product"] == "EN")
        & (df["row_kind"] == "self_sched")
    ]

    # EN curve-hours per resource (the S2 denominator) — price-blind.
    en_hours = (
        gen.groupby("resource_seq")["interval_start_utc"].nunique().to_dict()
        if len(gen)
        else {}
    )

    hours: list[tuple] = []
    bucket_vol: dict[int, np.ndarray] = {}
    if len(gen):
        gen = gen.sort_values(["resource_seq", "interval_start_utc", "segment_mw"])
        mw_all = gen["segment_mw"].to_numpy(dtype="float64")
        px_all = gen["segment_price_usd_per_mwh"].to_numpy(dtype="float64")
        rs_all = gen["resource_seq"].to_numpy()
        hr_all = gen["interval_start_utc"].to_numpy()
        # Hour-of-day in CAISO local time (DST-exact) for the descriptive
        # profile below; never used by the classifier or the verdict.
        hod_all = (
            gen["interval_start_utc"].dt.tz_convert("America/Los_Angeles").dt.hour
        ).to_numpy()
        # Curve boundaries: a new (resource, hour) starts a new bid curve.
        new = np.empty(len(gen), dtype=bool)
        new[0] = True
        new[1:] = (rs_all[1:] != rs_all[:-1]) | (hr_all[1:] != hr_all[:-1])
        starts = np.flatnonzero(new)
        stops = np.append(starts[1:], len(gen))
        for i0, i1 in zip(starts, stops):
            mw = mw_all[i0:i1]
            px = px_all[i0:i1]
            if not np.isfinite(mw).all() or not np.isfinite(px).all():
                continue
            lo, hi = mw[0], mw[-1]
            if lo > -WD_MW_EPS or hi < WD_MW_EPS:
                continue  # S1: not withdrawal-capable in this hour
            rs = int(rs_all[i0])
            # p_hi: first breakpoint on the discharge side (>= 0 MW).
            j_hi = int(np.searchsorted(mw, 0.0, side="left"))
            # p_lo: step-convention price applying at MW = 0+ (last bp <= 0).
            j_lo = int(np.searchsorted(mw, 0.0, side="right")) - 1
            hours.append(
                (
                    rs,
                    float(lo),
                    float(hi),
                    float(px[j_hi]),
                    float(px[j_lo]),
                    int(hod_all[i0]),
                )
            )
            # Discharge priced volume by caiso-176 bucket: price p_i applies on
            # [mw_i, mw_{i+1}); the top breakpoint has no interval above it.
            vol = bucket_vol.setdefault(rs, np.zeros(len(edges)))
            top = np.maximum(mw[1:], 0.0)
            bot = np.maximum(mw[:-1], 0.0)
            width = top - bot
            for k in np.flatnonzero(width > 0):
                p = px[k]
                for bi, (_lab, blo, bhi) in enumerate(edges):
                    if blo < p <= bhi:
                        vol[bi] += width[k]
                        break

    selfsched = (
        ss.groupby("resource_seq")["self_sched_mw"].sum().to_dict() if len(ss) else {}
    )
    return {
        "path": path.name,
        "en_hours": en_hours,
        "hours": hours,
        "bucket_vol": {k: v.tolist() for k, v in bucket_vol.items()},
        "selfsched": {int(k): float(v) for k, v in selfsched.items()},
    }


def scan_year(year: int, workers: int) -> dict:
    """Stream one year's daily zips into per-resource accumulators."""
    files = sorted(ZIPS.glob(f"{year}*_PUB_BID_DAM_v3_csv.zip"))
    start, end = dt.date(year, 1, 1), dt.date(year, 12, 31)
    wanted = {
        (start + dt.timedelta(days=i)).strftime("%Y%m%d")
        for i in range((end - start).days + 1)
    }
    present = {f.name[:8] for f in files}

    en_hours: dict[int, int] = defaultdict(int)
    bucket_vol: dict[int, np.ndarray] = defaultdict(
        lambda: np.zeros(len(_bucket_edges()))
    )
    selfsched: dict[int, float] = defaultdict(float)
    rows: list[tuple] = []
    errors: list[str] = []

    with ProcessPoolExecutor(max_workers=workers) as pool:
        for rec in pool.map(_day_records, files, chunksize=4):
            if rec is None or "error" in rec:
                errors.append(f"{rec['path']}: {rec['error']}" if rec else "unknown")
                continue
            for rs, n in rec["en_hours"].items():
                en_hours[int(rs)] += int(n)
            for rs, v in rec["bucket_vol"].items():
                bucket_vol[int(rs)] += np.asarray(v)
            for rs, v in rec["selfsched"].items():
                selfsched[int(rs)] += float(v)
            rows.extend(rec["hours"])

    hours = pd.DataFrame(
        rows, columns=["resource_seq", "min_mw", "max_mw", "p_hi", "p_lo", "hour_pt"]
    )
    return {
        "year": year,
        "days_requested": len(wanted),
        "days_present": len(present),
        "days_missing": sorted(wanted - present),
        "parse_errors": errors,
        "en_hours": dict(en_hours),
        "bucket_vol": {k: v.tolist() for k, v in bucket_vol.items()},
        "selfsched": dict(selfsched),
        "hours": hours,
    }


def classify(scans: dict[int, dict]) -> pd.DataFrame:
    """Apply S2/S3/S4 — PRICE-BLIND. Returns one row per (resource_seq, year)."""
    recs = []
    for year, sc in scans.items():
        h = sc["hours"]
        if len(h):
            agg = h.groupby("resource_seq").agg(
                wd_hours=("min_mw", "size"),
                p05_min_mw=("min_mw", lambda s: float(np.percentile(s, 5))),
                p95_max_mw=("max_mw", lambda s: float(np.percentile(s, 95))),
            )
        else:
            agg = pd.DataFrame(columns=["wd_hours", "p05_min_mw", "p95_max_mw"]).astype(
                float
            )
        for rs, row in agg.iterrows():
            en = int(sc["en_hours"].get(int(rs), 0))
            wd = int(row["wd_hours"])
            sym = (
                abs(row["p05_min_mw"]) / row["p95_max_mw"]
                if row["p95_max_mw"] > 0
                else np.nan
            )
            recs.append(
                {
                    "resource_seq": int(rs),
                    "year": year,
                    "en_hours": en,
                    "wd_hours": wd,
                    "wd_frac": wd / en if en else 0.0,
                    "p05_min_mw": row["p05_min_mw"],
                    "p95_max_mw": row["p95_max_mw"],
                    "sym": sym,
                    "selfsched_mw": float(sc["selfsched"].get(int(rs), 0.0)),
                }
            )
    df = pd.DataFrame(recs)
    if df.empty:
        return df

    # S2 — storage-like.
    df["in_S"] = (df["wd_frac"] >= S2_WD_FRAC) & (df["en_hours"] >= S2_MIN_HOURS)
    # S3 — battery-like (power symmetry).
    df["in_B"] = df["in_S"] & df["sym"].between(S3_SYM_LO, S3_SYM_HI)
    # S4 — minus large / stable / pre-existing (pumped storage).
    big = df[df["in_B"]].groupby("resource_seq")
    ps: set[int] = set()
    for rs, grp in big:
        if set(grp["year"]) != set(YEARS):
            continue
        caps = grp.set_index("year")["p95_max_mw"]
        if caps.min() < S4_PS_MW:
            continue
        if (caps.max() - caps.min()) / caps.max() < S4_PS_DRIFT:
            ps.add(int(rs))
    df["is_ps_excluded"] = df["resource_seq"].isin(ps)
    df["in_B_noPS"] = df["in_B"] & ~df["is_ps_excluded"]
    return df


def _stat(hours: pd.DataFrame, members: set[int], col: str = "p_hi") -> dict:
    """Fleet floor statistic: MEDIAN over resources of each resource's own q05."""
    sub = hours[hours["resource_seq"].isin(members)]
    if sub.empty:
        return {"n_resources": 0, "n_hours": 0, "fleet_median_q05": None}
    q05 = sub.groupby("resource_seq")[col].quantile(0.05)
    return {
        "n_resources": int(len(q05)),
        "n_hours": int(len(sub)),
        "fleet_median_q05": round(float(q05.median()), 4),
        "q05_dist": {
            f"p{p}": round(float(np.percentile(q05, p)), 4)
            for p in (10, 25, 50, 75, 90)
        },
        "fleet_median_of_median": round(
            float(sub.groupby("resource_seq")[col].median().median()), 4
        ),
    }


def _mode_test(hours: pd.DataFrame, members: set[int]) -> dict:
    """The mass-point test — the ONLY route to an identification (§5 BRANCH I)."""
    sub = hours[hours["resource_seq"].isin(members)]
    if sub.empty:
        return {"n_hours": 0, "mode": None, "mode_share": 0.0}
    binned = (sub["p_hi"] / MODE_GRID).round() * MODE_GRID
    counts = binned.value_counts()
    mode = float(counts.index[0])
    share = float(counts.iloc[0] / len(binned))
    window = float(((binned - mode).abs() <= MODE_WINDOW).sum() / len(binned))
    # Resource-equal weighting: each resource votes once, with its OWN modal bin.
    per_res = binned.groupby(sub["resource_seq"]).agg(
        lambda s: float(s.value_counts().index[0])
    )
    res_counts = per_res.value_counts()
    return {
        "n_hours": int(len(sub)),
        "mode": mode,
        "mode_share": round(share, 4),
        "share_within_window": round(window, 4),
        "top5": [
            {"bin": float(b), "share": round(float(c / len(binned)), 4)}
            for b, c in counts.head(5).items()
        ],
        "resource_weighted_mode": float(res_counts.index[0]),
        "resource_weighted_share": round(float(res_counts.iloc[0] / len(per_res)), 4),
    }


def _descriptive(hours: pd.DataFrame, members: set[int]) -> dict:
    """Characterise the wall. REPORTED, NEVER USED BY THE VERDICT.

    DISCLOSED ORDERING: unlike everything above, this block was added AFTER a
    partial-corpus smoke test (87 days of 2023) showed the modal first
    discharge rung sitting at the $1,000 soft bid cap. It exists to describe
    WHY the corpus does not identify, not to pick a value: no branch in §5 of
    the pre-registration reads any field produced here, and none of these
    numbers can move the verdict. Recorded this way rather than presented as
    pre-registered.

    CAISO energy bid caps: -$150 floor / $1,000 soft / $2,000 hard (schema
    ``dam-public-bids``, ``segment_price_usd_per_mwh``).
    """
    sub = hours[hours["resource_seq"].isin(members)]
    if sub.empty:
        return {}
    p = sub["p_hi"]
    per_res_min = sub.groupby("resource_seq")["p_hi"].min()
    low = sub[p <= CAISO_BOUND]
    all_prof = sub["hour_pt"].value_counts(normalize=True).sort_index()
    low_prof = (
        low["hour_pt"].value_counts(normalize=True).sort_index()
        if len(low)
        else all_prof * 0.0
    )
    return {
        "share_at_soft_cap_ge_999": round(float((p >= 999.0).mean()), 4),
        "share_at_hard_cap_ge_1999": round(float((p >= 1999.0).mean()), 4),
        "share_le_caiso176_bound": round(float((p <= CAISO_BOUND).mean()), 4),
        "share_le_incumbent_5": round(float((p <= 5.0).mean()), 4),
        "per_resource_annual_min": {
            f"p{q}": round(float(np.percentile(per_res_min, q)), 4)
            for q in (10, 25, 50, 75, 90)
        },
        "hour_of_day_pt": {
            "all_storage_hours": {
                int(k): round(float(v), 4) for k, v in all_prof.items()
            },
            "hours_with_first_rung_le_15": {
                int(k): round(float(v), 4) for k, v in low_prof.items()
            },
        },
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    edges = _bucket_edges()
    labels = [lab for lab, _, _ in edges]
    published = _published_lesr_shares()

    scans = {y: scan_year(y, args.workers) for y in args.years}
    for y, sc in scans.items():
        print(
            f"{y}: {sc['days_present']}/{sc['days_requested']} days, "
            f"{len(sc['hours']):,} storage curve-hours, "
            f"{len(sc['days_missing'])} missing, {len(sc['parse_errors'])} errors",
            flush=True,
        )

    cls = classify(scans)
    cls.to_csv(OUT_RES, index=False)

    out: dict = {
        "probe": "caiso-178 PUB_DAM_GRP battery discharge bid floor",
        "prereg": "results/calibration/PRECHECK-caiso178-public-bids-2026-08-06.md",
        "source": "data/raw/caiso-public-bids/zips/*_PUB_BID_DAM_v3_csv.zip (OASIS PUB_DAM_GRP)",
        "incumbent_adder": 5.0,
        "caiso176_bound": CAISO_BOUND,
        "coverage": {
            str(y): {
                k: scans[y][k]
                for k in (
                    "days_requested",
                    "days_present",
                    "days_missing",
                    "parse_errors",
                )
            }
            for y in args.years
        },
        "classifier": {
            "price_blind": True,
            "stages": {
                "S1_wd_mw_eps": WD_MW_EPS,
                "S2_wd_frac": S2_WD_FRAC,
                "S2_min_hours": S2_MIN_HOURS,
                "S3_sym_band": [S3_SYM_LO, S3_SYM_HI],
                "S4_ps_mw": S4_PS_MW,
                "S4_ps_drift": S4_PS_DRIFT,
            },
        },
        "H1a_capacity": {},
        "H1b_bucket_agreement": {},
        "H1c_sensitivity": {},
        "statistic": {},
        "mode_test": {},
        "descriptive": {},
        "curve_geometry": {},
    }

    # --- H1a CAPACITY -------------------------------------------------------
    for y in args.years:
        mem = cls[(cls["year"] == y) & cls["in_B_noPS"]]
        tot = float(mem["p95_max_mw"].sum())
        ref = MEASURED_BATTERY_MW[y]
        out["H1a_capacity"][str(y)] = {
            "classified_mw": round(tot, 1),
            "measured_envelope_mw": ref,
            "ratio": round(tot / ref, 4),
            "within_tol": bool(abs(tot / ref - 1.0) <= H1A_TOL),
            "n_resources": int(len(mem)),
            "ps_excluded_mw": round(
                float(
                    cls[(cls["year"] == y) & cls["is_ps_excluded"]]["p95_max_mw"].sum()
                ),
                1,
            ),
            "ps_fleet_reference_mw": CAISO_PS_FLEET_MW,
        }
    caps = [out["H1a_capacity"][str(y)]["classified_mw"] for y in sorted(args.years)]
    out["H1a_capacity"]["growth_ordering_ok"] = bool(
        all(a < b for a, b in zip(caps, caps[1:]))
    )
    out["H1a_capacity"]["PASS"] = bool(
        all(out["H1a_capacity"][str(y)]["within_tol"] for y in args.years)
        and out["H1a_capacity"]["growth_ordering_ok"]
    )

    # --- H1b BUCKET AGREEMENT (out-of-construction) -------------------------
    for y in args.years:
        mem = set(cls[(cls["year"] == y) & cls["in_B_noPS"]]["resource_seq"])
        vol = np.zeros(len(edges))
        for rs, v in scans[y]["bucket_vol"].items():
            if int(rs) in mem:
                vol += np.asarray(v)
        tot = vol.sum()
        shares = vol / tot if tot else vol
        pub = published.get(y, {})
        dev = [
            abs(shares[i] - pub.get(labels[i], 0.0)) * 100.0 for i in range(len(edges))
        ]
        low_ours = next(
            (labels[i] for i in range(len(edges)) if shares[i] >= 0.01), None
        )
        low_pub = next((lab for lab in labels if pub.get(lab, 0.0) >= 0.01), None)
        out["H1b_bucket_agreement"][str(y)] = {
            "priced_mw": round(float(tot), 1),
            "ours": {labels[i]: round(float(shares[i]), 6) for i in range(len(edges))},
            "published_lesr": {k: round(v, 6) for k, v in pub.items()},
            "mad_pp": round(float(np.mean(dev)), 3),
            "mad_ok": bool(np.mean(dev) <= H1B_MAD_PP),
            "lowest_1pct_bucket_ours": low_ours,
            "lowest_1pct_bucket_published": low_pub,
            "lowest_bucket_match": bool(low_ours == low_pub),
        }
    n_match = sum(
        out["H1b_bucket_agreement"][str(y)]["lowest_bucket_match"] for y in args.years
    )
    out["H1b_bucket_agreement"]["PASS"] = bool(
        all(out["H1b_bucket_agreement"][str(y)]["mad_ok"] for y in args.years)
        and n_match >= 2
    )

    # --- the statistic, the mode test, and the H1c sensitivity grid ---------
    hist_rows = []
    for y in args.years:
        h = scans[y]["hours"]
        cy = cls[cls["year"] == y]
        sets = {
            "S": set(cy[cy["in_S"]]["resource_seq"]),
            "B": set(cy[cy["in_B"]]["resource_seq"]),
            "B_noPS": set(cy[cy["in_B_noPS"]]["resource_seq"]),
        }
        out["statistic"][str(y)] = {
            k: _stat(h, v)
            | {"p_lo_reading": _stat(h, v, col="p_lo")["fleet_median_q05"]}
            for k, v in sets.items()
        }
        out["mode_test"][str(y)] = _mode_test(h, sets["B_noPS"])
        out["descriptive"][str(y)] = _descriptive(h, sets["B_noPS"])
        sub = h[h["resource_seq"].isin(sets["B_noPS"])]
        if len(sub):
            binned = (sub["p_hi"] / MODE_GRID).round() * MODE_GRID
            vc = binned.value_counts().sort_index()
            for b, c in vc.items():
                hist_rows.append(
                    {
                        "year": y,
                        "bin_usd": float(b),
                        "n_hours": int(c),
                        "share": float(c / len(binned)),
                    }
                )
            out["curve_geometry"][str(y)] = {
                "storage_curve_hours": int(len(sub)),
                "share_bp_exactly_at_zero": round(
                    float((sub["p_hi"] == sub["p_lo"]).mean()), 4
                ),
                "share_p_hi_le_zero": round(float((sub["p_hi"] <= 0).mean()), 4),
                "share_p_hi_gt_caiso176_bound": round(
                    float((sub["p_hi"] > CAISO_BOUND).mean()), 4
                ),
            }
        # H1c sensitivity: sets x symmetry thresholds.
        grid = {}
        for name, mem in sets.items():
            grid[f"set={name}"] = _stat(h, mem)["fleet_median_q05"]
        for thr in (0.3, 0.5, 0.7):
            mem = set(
                cy[cy["in_S"] & cy["sym"].between(thr, 1.0 / thr)]["resource_seq"]
            ) - set(cy[cy["is_ps_excluded"]]["resource_seq"])
            grid[f"sym>={thr}"] = _stat(h, mem)["fleet_median_q05"]
        vals = [v for v in grid.values() if v is not None]
        out["H1c_sensitivity"][str(y)] = {
            "grid": grid,
            "spread": round(max(vals) - min(vals), 4) if vals else None,
            "robust": bool(vals and (max(vals) - min(vals)) <= H1C_MAX_SPREAD),
        }
    out["H1c_sensitivity"]["PASS"] = bool(
        all(out["H1c_sensitivity"][str(y)]["robust"] for y in args.years)
    )

    pd.DataFrame(hist_rows).to_csv(OUT_HIST, index=False)

    # --- the pre-registered verdict ----------------------------------------
    h1a, h1b, h1c = (
        out["H1a_capacity"]["PASS"],
        out["H1b_bucket_agreement"]["PASS"],
        out["H1c_sensitivity"]["PASS"],
    )
    classifier = (
        "VALIDATED"
        if (h1a and h1b and h1c)
        else "FAILED"
        if not (h1a or h1b)
        else "PROVISIONAL"
    )
    modes = [out["mode_test"][str(y)] for y in args.years]
    mode_vals = [m["mode"] for m in modes if m["mode"] is not None]
    mass_ok = bool(
        modes
        and all(m["mode_share"] >= MODE_MIN_SHARE for m in modes)
        and len(mode_vals) == len(args.years)
        and (max(mode_vals) - min(mode_vals)) <= MODE_STABILITY
        and all(m["resource_weighted_mode"] == m["mode"] for m in modes)
        and all(v > 0 for v in mode_vals)
        and all(v <= CAISO_BOUND for v in mode_vals)
    )
    out["verdict"] = {
        "classifier": classifier,
        "H1a_PASS": h1a,
        "H1b_PASS": h1b,
        "H1c_ROBUST": h1c,
        "mass_point_ok": mass_ok,
        "branch": (
            "I_IDENTIFIES"
            if (classifier == "VALIDATED" and mass_ok)
            else "III_NO_INSTRUMENT"
            if classifier == "FAILED"
            else "II_SHARPER_WALL"
        ),
        "identified_value": (
            round(float(np.mean(mode_vals)) / MODE_GRID) * MODE_GRID
            if (classifier == "VALIDATED" and mass_ok)
            else None
        ),
        "new_bound_fleet_median_q05": {
            str(y): out["statistic"][str(y)]["B_noPS"]["fleet_median_q05"]
            for y in args.years
        },
    }

    OUT_JSON.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["verdict"], indent=1))
    print(f"wrote {OUT_JSON}\n      {OUT_RES}\n      {OUT_HIST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
