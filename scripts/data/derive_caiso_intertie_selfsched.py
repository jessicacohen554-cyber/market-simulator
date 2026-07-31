"""Derive CAISO's measured price-insensitive INTERTIE ceiling — (month x hod) MW.

The parameter series behind ``config.caiso_firm_import_selfsched_clip``
(caiso-151), specified at caiso-150 §F. It measures, from CAISO's own
as-submitted day-ahead bids, how much intertie MW is offered
**price-insensitively** — the object the caiso-77 firm must-flow floor
(``caiso_firm_import_selfschedule``) claims to represent but has never been
checked against.

WHY A NEW SERIES. The floor pins both firm tranches' ``min_gen`` at their FULL
shaped capability, and its rule-17 window declaration rests on "the measured
(month x hod) median self-schedule". The series it actually uses
(``measured_firm_import_shape``) is EIA-930 realised **net corridor
interchange** = a broadly flat price-insensitive core PLUS a large price-elastic
economic layer, so the floor attributes the whole diurnal swing of realised flow
to the price-insensitive core. caiso-150 measured the gap on this source: the
floor forces more price-insensitive import than CAISO's ENTIRE measured
price-insensitive intertie position in 23.9/47.2/48.9 % of hours (2023/24/25),
0.969/4.634/5.705 TWh, concentrated overnight, and growing with the DMM RA
level. Evidence:
``results/calibration/FINDING-caiso150-firm-import-elasticity-2026-07-31.md``.

THE QUANTITY (deliberately ONE-SIDED — see the wall below)::

    ceiling[month, hod] = mean over sampled days of
        ( ALL intertie self-schedule MW, both directions, unsigned )
      + ( import-classified economic MW offered at or below $0/MWh )

The second limb is the other half of the floor's OWN definition of price-taking
conduct — "self-scheduled **or bid at/below $0/MWh**" (CPUC D.20-06-028 RA
import must-offer, quoted in ``inject_caiso_firm_import_selfschedule``) — which
is an ECONOMIC bid and so invisible in ``SELFSCHEDMW``.

THE IDENTIFICATION WALL (binding; caiso-150 §B, DO-NOT-REDO §H). Direction is
NOT identifiable. A resource that self-schedules submits no economic curve —
that is what price-insensitive means — and the masked feed carries no direction
field (``PRODUCTBID_DESC`` / ``MARKETPRODUCT_DESC`` are entirely NaN on INTERTIE
rows), leaving 1,141 of 1,452 resources carrying 94.91 % of self-scheduled MW
unclassifiable. There is no public crosswalk: masking is the disclosure's
purpose. So only a one-sided CEILING is measurable, and by construction

    ceiling[t] >= (true price-insensitive IMPORT position)[t]

in every hour, whatever the unresolvable split turns out to be. That is exactly
what the mechanism needs: clipping a floor at an upper bound can only ever
REMOVE forcing the measured record cannot support, never add any. Do not attempt
the import/export split by curve monotonicity, by any masked-id crosswalk, or by
correlating against EIA-930 (the last contaminates the independence the whole
finding rests on).

RUN-LENGTH ENCODING — the thing that must not be got wrong. OASIS publishes bids
RLE: one row spans the whole interval over which a resource's bid is unchanged
(``TIMEINTERVALSTART_GMT`` .. ``TIMEINTERVALEND_GMT``, spans of 1-24 h). Every
row is expanded to its hour slots BEFORE any hourly statistic is taken. Skipping
this yields a flat ~2.3 GW artifact of range start-times clustering. (The repo's
canonical parser ``scripts/lib/dam_public_bids/caiso.py`` keys rows by their
START stamp alone and never expands — a separate, filed defect belonging to the
offer-surface lane, caiso-150 §E1; it is NOT used here.)

CLOCK. OASIS stamps are exact UTC, converted to US/Pacific wall time and bucketed
by (local month, local hour). ``envelopes._caiso_interchange_model_clock`` is
deliberately NOT applied: that lag exists only to undo an EIA-930 publication
artifact, which this source does not carry.

CORPUS BALANCE IS LOAD-BEARING (caiso-150 §B). A winter-only corpus reads the
position at 2,291 MW and nearly flat (1.32x diurnal); the seasonally balanced
corpus reads 3,449 MW peaking in the evening (1.49x) — a ~50 % headline
overstatement and a mislocated peak. The sampler here is balanced by
construction: days 2,5,8,11,14,17,20,23,26,29 of every month of every train
year. Spacing 3 walks the weekday through all seven within each month; 10 days
per (year, month) gives every (month x hod) bucket per-year coverage, which the
leave-one-year-out gate needs. Feb 29 is dropped so all three Februaries carry
the same 9 sampled days and the sample matches the model's non-leap calendar.

POOLING. The shipped table is the POOLED climatology, formed as the equal-weight
mean of the three per-year (month x hod) tables — never a raw pooled mean, which
would weight years by their surviving day count. Equal year weight is the same
discipline as the seasonal balance above. Per-year tables exist only to feed the
honesty gates. This also matches the caiso-150 §C confrontation, which was
computed on the pooled corpus, so the armed mechanism removes exactly the excess
the finding published.

GATES (FROZEN EX ANTE, before any value was computed — rule 23
``[R-FROZEN-DERIVE]``; thresholds are the caiso-81/86/87/88 standard):

* **G1 year-stability CV <= 0.20** on the three per-year annual mean levels.
* **G2 LOYO level <= 25 %** — each held-out year's annual mean vs the mean of
  the other two.
* **G3 LOYO shape <= 25 %** — each held-out year, the MEDIAN across the 288
  (month x hod) buckets of the relative error of the mean-of-other-two. A scalar
  level gate alone is too weak for a series whose SHAPE is what the mechanism
  consumes.
* **G4 coverage** — every one of the 288 (month x hod) buckets carries sampled
  days in all three years.

A FAIL files a FINDING and the lane STOPS — nothing here is iterated against the
gates, and rule 23 forbids re-deriving because a residual moved: this script
re-runs only when its SOURCE corpus changes, and such a commit must cite the
data change.

FORWARD STORY (rule 13 ``[R-MEASURED]``). OASIS publishes Public Bid Data
continuously at a 90-day lag, so this same quantity regenerates for any forward
year from the same query, and it responds to changed conditions (a market with
more price-insensitive intertie conduct measures a higher ceiling). A forecast
year consumes the pooled climatology exactly as the caiso-73 shape already
consumes its own pooled climatology.

Source: ``data/raw/caiso-public-bids/zips/`` (gitignored; regenerate with
``scripts/data/fetch_caiso_public_bids.py``).
Output: ``data/raw/_processed-legacy/caiso_intertie_selfsched_ceiling.csv``.

Usage::

    .venv/bin/python scripts/data/derive_caiso_intertie_selfsched.py
    .venv/bin/python scripts/data/derive_caiso_intertie_selfsched.py --report-only
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import (  # noqa: E402
    CAISO_PUBLIC_BIDS_DIR,
    PROCESSED_DIR,
)

YEARS = (2023, 2024, 2025)
N_MONTHS = 12
N_HOD = 24

#: Frozen estimation-stage honesty gates (caiso-81/86/87/88 standard).
CV_MAX = 0.20
LOYO_MAX = 0.25

BID_ZIPS = CAISO_PUBLIC_BIDS_DIR / "zips"
OUT_CSV = PROCESSED_DIR / "caiso_intertie_selfsched_ceiling.csv"

#: Raw OASIS columns actually used (the rest are redundant renderings).
_RAW_COLS = [
    "RESOURCE_TYPE",
    "RESOURCEBID_SEQ",
    "TIMEINTERVALSTART_GMT",
    "TIMEINTERVALEND_GMT",
    "MARKETPRODUCTTYPE",
    "SELFSCHEDMW",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTOP_GMT",
    "SCH_BID_XAXISDATA",
    "SCH_BID_Y1AXISDATA",
]


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #
def _expand(
    res: np.ndarray,
    start: pd.Series,
    stop: pd.Series,
    val: np.ndarray,
    extra: np.ndarray | None = None,
    extra2: np.ndarray | None = None,
) -> pd.DataFrame:
    """Expand run-length-encoded ``[start, stop)`` rows into one row per hour."""
    if not len(res):
        return pd.DataFrame(columns=["res", "utc", "val", "extra", "extra2"])
    s = pd.to_datetime(pd.Series(start).to_numpy(), utc=True, format="mixed")
    e = pd.to_datetime(pd.Series(stop).to_numpy(), utc=True, format="mixed")
    span = np.clip(((e - s).total_seconds() // 3600).to_numpy().astype(int), 1, None)
    rep = np.repeat(np.arange(len(res)), span)
    offs = np.concatenate([np.arange(n) for n in span]) if len(span) else np.array([])
    return pd.DataFrame(
        {
            "res": res[rep],
            "utc": s.to_numpy()[rep] + pd.to_timedelta(offs, unit="h"),
            "val": val[rep],
            "extra": (extra[rep] if extra is not None else ""),
            "extra2": (extra2[rep] if extra2 is not None else 0.0),
        }
    )


def parse_bid_day(path: Path) -> pd.DataFrame:
    """Reduce one ``PUB_BID_DAM`` zip to per-(intertie resource, HOUR) records.

    Returns columns ``res`` / ``utc`` / ``ss_mw`` (self-scheduled MW) /
    ``mw_le0`` (cumulative MW the economic curve offers at or below $0/MWh) /
    ``curve`` (``import`` / ``export`` / ``flat`` from the curve's own
    price-vs-MW monotonicity — supply offers rise, demand bids fall — and ``""``
    where the resource-hour carries no curve at all).
    """
    with zipfile.ZipFile(path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        with z.open(name) as fh:
            df = pd.read_csv(fh, usecols=_RAW_COLS, low_memory=False)
    df = df[(df["RESOURCE_TYPE"] == "INTERTIE") & (df["MARKETPRODUCTTYPE"] == "EN")]
    df = df[df["RESOURCEBID_SEQ"].notna()].copy()
    empty = pd.DataFrame(columns=["res", "utc", "ss_mw", "mw_le0", "curve"]).astype(
        {"res": "int64"}
    )
    if df.empty:
        return empty

    is_seg = df["SCH_BID_XAXISDATA"].notna()
    seg = df[is_seg]
    ss = df[~is_seg & df["SELFSCHEDMW"].notna()]

    # --- self-schedule: expand each RLE range, sum per (resource, hour) ---
    ss_rows = _expand(
        ss["RESOURCEBID_SEQ"].astype("int64").to_numpy(),
        ss["TIMEINTERVALSTART_GMT"],
        ss["TIMEINTERVALEND_GMT"],
        ss["SELFSCHEDMW"].astype("float64").to_numpy(),
    )
    ss_h = (
        ss_rows.groupby(["res", "utc"], sort=False)["val"].sum().rename("ss_mw")
        if len(ss_rows)
        else pd.Series(dtype="float64", name="ss_mw")
    )

    # --- curves: classify per (resource, RLE range), then expand ---
    if len(seg):
        key = ["RESOURCEBID_SEQ", "SCH_BID_TIMEINTERVALSTART_GMT"]
        s = seg.sort_values(key + ["SCH_BID_XAXISDATA"], kind="mergesort")
        g = s.groupby(key, sort=False)
        le0 = s["SCH_BID_XAXISDATA"].where(s["SCH_BID_Y1AXISDATA"] <= 0.0)
        summary = pd.DataFrame(
            {
                "mw_le0": le0.groupby([s[k] for k in key], sort=False).max(),
                "inc": g["SCH_BID_Y1AXISDATA"].apply(
                    lambda v: bool((np.diff(v.to_numpy()) > 0).any())
                ),
                "dec": g["SCH_BID_Y1AXISDATA"].apply(
                    lambda v: bool((np.diff(v.to_numpy()) < 0).any())
                ),
                "stop": g["SCH_BID_TIMEINTERVALSTOP_GMT"].first(),
            }
        ).reset_index()
        summary["mw_le0"] = summary["mw_le0"].fillna(0.0)
        summary["curve"] = np.where(
            summary["inc"] & ~summary["dec"],
            "import",
            np.where(summary["dec"] & ~summary["inc"], "export", "flat"),
        )
        seg_rows = _expand(
            summary["RESOURCEBID_SEQ"].astype("int64").to_numpy(),
            summary["SCH_BID_TIMEINTERVALSTART_GMT"],
            summary["stop"],
            summary["mw_le0"].astype("float64").to_numpy(),
            extra=summary["curve"].to_numpy(),
        )
        seg_h = seg_rows.groupby(["res", "utc"], sort=False).agg(
            mw_le0=("val", "sum"), curve=("extra", "first")
        )
    else:
        seg_h = pd.DataFrame(columns=["mw_le0", "curve"])

    out = pd.concat([ss_h, seg_h], axis=1).reset_index()
    if "index" in out.columns:  # empty-frame edge case
        out = out.drop(columns=["index"])
    for col, fill in (("ss_mw", 0.0), ("mw_le0", 0.0), ("curve", "")):
        if col not in out.columns:
            out[col] = fill
        out[col] = out[col].fillna(fill)
    return out[["res", "utc", "ss_mw", "mw_le0", "curve"]]


def classify_interties(bids: pd.DataFrame) -> pd.Series:
    """Classify each masked intertie resource as ``import`` / ``export``.

    A CAISO **import** intertie submits a SUPPLY offer (price non-decreasing in
    MW); an **export** submits a DEMAND bid (price non-increasing). The vote is
    longitudinal over the whole corpus — the masked ``RESOURCEBID_SEQ`` is
    persistent across days and years — so a resource that only self-schedules on
    some days is still classified from the days it bids economically. Resources
    that NEVER submit an economic curve stay unclassified and are reported as an
    explicit coverage bound, never imputed (the §B wall).
    """
    seen = bids[bids["curve"].isin(("import", "export"))]
    if seen.empty:
        return pd.Series(dtype="object")
    return seen.groupby("res")["curve"].agg(lambda s: s.value_counts().idxmax())


def load_corpus() -> pd.DataFrame:
    """Parse every fetched daily zip into per-(resource, hour) intertie records."""
    files = sorted(BID_ZIPS.glob("*_PUB_BID_DAM_v3_csv.zip"))
    if not files:
        raise SystemExit(
            f"no bid zips under {BID_ZIPS} — run scripts/data/fetch_caiso_public_bids.py"
        )
    frames = []
    for f in files:
        if f.name[:8] == "20240229":
            continue  # non-leap model calendar; keeps all three Februaries equal
        d = parse_bid_day(f)
        if not d.empty:
            d["day"] = f.name[:8]
            frames.append(d)
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------- #
# the ceiling
# --------------------------------------------------------------------------- #
def hourly_ceiling(bids: pd.DataFrame, votes: pd.Series) -> pd.DataFrame:
    """Aggregate the corpus to one system-total ceiling row per sampled hour."""
    b = bids.copy()
    b["cls"] = b["res"].map(votes).fillna("unknown")
    local = pd.to_datetime(b["utc"], utc=True).dt.tz_convert("US/Pacific")
    b["ts"] = local.dt.tz_localize(None)
    b["year"] = local.dt.year
    b["month"] = local.dt.month
    b["hod"] = local.dt.hour
    # The import limb of the <=$0 economic layer only; the self-schedule limb is
    # unsigned across both directions (the wall).
    b["le0_import"] = np.where(b["cls"] == "import", b["mw_le0"], 0.0)
    per_hour = (
        b.groupby(["ts", "year", "month", "hod"], sort=False)[["ss_mw", "le0_import"]]
        .sum()
        .reset_index()
    )
    per_hour["ceiling_mw"] = per_hour["ss_mw"] + per_hour["le0_import"]
    return per_hour[per_hour["year"].isin(YEARS)]


def year_tables(per_hour: pd.DataFrame) -> dict[int, np.ndarray]:
    """Per-year (12 x 24) mean ceiling tables, NaN where a bucket is unsampled."""
    out: dict[int, np.ndarray] = {}
    for yr in YEARS:
        tab = np.full((N_MONTHS, N_HOD), np.nan)
        sub = per_hour[per_hour["year"] == yr]
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            tab[int(m) - 1, int(h)] = float(g["ceiling_mw"].mean())
        out[yr] = tab
    return out


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def run_gates(tabs: dict[int, np.ndarray]) -> tuple[bool, dict]:
    """Score the four frozen honesty gates; print the report."""
    levels = {y: float(np.nanmean(t)) for y, t in tabs.items()}
    vals = np.array([levels[y] for y in YEARS])
    cv = float(vals.std() / vals.mean())
    g1 = cv <= CV_MAX
    print("\n  per-year annual mean ceiling:")
    for y in YEARS:
        print(f"    {y}: {levels[y]:,.0f} MW")
    print(
        f"\n  G1 year-stability CV = {cv:.3f} (gate <= {CV_MAX}): "
        f"{'PASS' if g1 else 'FAIL'}"
    )

    g2 = True
    g3 = True
    for held in YEARS:
        others = [y for y in YEARS if y != held]
        pred = float(np.mean([levels[y] for y in others]))
        err = abs(pred - levels[held]) / levels[held]
        ok = err <= LOYO_MAX
        g2 = g2 and ok
        print(
            f"  G2 LOYO level, held-out {held}: mean-of-others {pred:,.0f} vs "
            f"{levels[held]:,.0f} -> {err:.1%} (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )
    for held in YEARS:
        others = [y for y in YEARS if y != held]
        pred_tab = np.nanmean(np.stack([tabs[y] for y in others]), axis=0)
        held_tab = tabs[held]
        m = np.isfinite(pred_tab) & np.isfinite(held_tab) & (held_tab > 0)
        rel = np.abs(pred_tab[m] - held_tab[m]) / held_tab[m]
        med = float(np.median(rel))
        ok = med <= LOYO_MAX
        g3 = g3 and ok
        print(
            f"  G3 LOYO shape, held-out {held}: median bucket rel-err {med:.1%} "
            f"over {int(m.sum())} buckets (gate <= {LOYO_MAX:.0%}): "
            f"{'PASS' if ok else 'FAIL'}"
        )

    covered = np.all(np.stack([np.isfinite(tabs[y]) for y in YEARS]), axis=0)
    n_cov = int(covered.sum())
    g4 = n_cov == N_MONTHS * N_HOD
    print(
        f"  G4 coverage: {n_cov} of {N_MONTHS * N_HOD} (month x hod) buckets "
        f"sampled in ALL three years: {'PASS' if g4 else 'FAIL'}"
    )
    passed = g1 and g2 and g3 and g4
    return passed, {
        "levels": levels,
        "cv": cv,
        "g1": g1,
        "g2": g2,
        "g3": g3,
        "g4": g4,
        "covered_buckets": n_cov,
    }


def main(argv: list[str] | None = None) -> int:
    """Derive the ceiling, score the frozen gates, write the artifact."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_CSV)
    ap.add_argument(
        "--report-only", action="store_true", help="score the gates, write nothing"
    )
    args = ap.parse_args(argv)

    print("=== CAISO measured price-insensitive INTERTIE ceiling (OASIS DAM bids) ===")
    bids = load_corpus()
    votes = classify_interties(bids)
    per_hour = hourly_ceiling(bids, votes)

    days = bids["day"].nunique()
    unk_mw = bids.loc[~bids["res"].isin(votes.index), "ss_mw"].sum()
    all_mw = bids["ss_mw"].sum()
    print(f"\n  corpus: {days} trade days, {len(bids):,} (resource x hour) records")
    print(
        f"  resources: {bids['res'].nunique()} masked seqs "
        f"(import {(votes == 'import').sum()}, export {(votes == 'export').sum()}, "
        f"unclassified {bids.loc[~bids['res'].isin(votes.index), 'res'].nunique()})"
    )
    print(
        f"  unclassified share of all self-schedule MW: "
        f"{100 * unk_mw / max(1e-9, all_mw):.2f} %  (the §B wall — one-sided by design)"
    )
    per_ym = per_hour.groupby(["year", "month"])["ts"].nunique() / 24.0
    print(
        f"  sampled days per (year, month): min {per_ym.min():.0f} "
        f"max {per_ym.max():.0f} mean {per_ym.mean():.1f}"
    )

    tabs = year_tables(per_hour)
    passed, report = run_gates(tabs)

    # Pooled climatology = EQUAL-WEIGHT mean of the three per-year tables.
    pooled = np.nanmean(np.stack([tabs[y] for y in YEARS]), axis=0)
    prof = np.nanmean(pooled, axis=0)
    print("\n  pooled ceiling by hour-of-day (MW):")
    for lo in (0, 8, 16):
        print(
            f"    h{lo:02d}-{lo + 7:02d}  "
            + " ".join(f"{prof[h]:6.0f}" for h in range(lo, lo + 8))
        )
    print(
        f"\n  pooled: mean {np.nanmean(pooled):,.0f} MW   "
        f"min {np.nanmin(pooled):,.0f} (m{np.unravel_index(np.nanargmin(pooled), pooled.shape)[0] + 1} "
        f"h{np.unravel_index(np.nanargmin(pooled), pooled.shape)[1]})   "
        f"max {np.nanmax(pooled):,.0f} (m{np.unravel_index(np.nanargmax(pooled), pooled.shape)[0] + 1} "
        f"h{np.unravel_index(np.nanargmax(pooled), pooled.shape)[1]})"
    )
    print(f"  diurnal swing (max hod / min hod): {prof.max() / prof.min():.2f}x")

    # Transparency only — the artifact ships the MEAN. The statistic is frozen;
    # these are printed so the choice is visible, never to offer a knob.
    for pct in (50, 75, 95):
        alt = per_hour.groupby(["month", "hod"])["ceiling_mw"].quantile(pct / 100.0)
        print(
            f"  [transparency] pooled-corpus p{pct} bucket mean: {alt.mean():,.0f} MW"
        )

    print(
        "\n  OVERALL: "
        + (
            "PASS — ceiling admissible; arm caiso_firm_import_selfsched_clip"
            if passed
            else "FAIL — file a FINDING and STOP; do NOT build"
        )
    )
    if not passed:
        return 2
    if args.report_only:
        print("  --report-only: nothing written")
        return 0

    rows = [
        {"month": m + 1, "hod": h, "ceiling_mw": round(float(pooled[m, h]), 3)}
        for m in range(N_MONTHS)
        for h in range(N_HOD)
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"  wrote {args.out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
