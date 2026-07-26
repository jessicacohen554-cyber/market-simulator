"""neiso-65 follow-up — root-cause the RESIDUAL CAMPD outage over-count.

The freeze's lift condition. After the merit-order guard, the CEMS detector
still books **1.5-2.13x** the published outage MW on CAISO's crosswalked
active-plant scope (``RESULTS-neiso65-crossiso-reaudit-2026-07.md`` §4) and
1.29-1.36x whole-fleet on NEISO. The re-audit left two candidate directions
open and adjudicated neither:

  H1  the detector books economic cycling that sits BELOW the guard's
      ``MERIT_OOM_FRAC`` = 0.90 out-of-merit threshold as mechanical outage;
  H2  CNOG (a DAM prior-trade-date snapshot) UNDER-reports intraday forced
      outages, so the published side is the one that is wrong.

This probe discriminates them with the guard's OWN measured instrument — the
:class:`MeritOrderPanel` out-of-merit share (measured CAMPD heat rate x
delivered fuel price vs the revealed running-unit RCC). No LMP, no cleared
price, no residual anywhere: rules 11/13/26 hold exactly as they do for the
guard itself.

Method. Every window the guard KEPT (i.e. every window still in the committed
extract) on the crosswalked active-plant scope is labelled against the
published CNOG series for its own plant:

  MATCHED  the plant carries published outage MW on >= --match-frac of the
           window's days -> the detector and the publisher agree;
  EXCESS   it does not -> this window IS the over-count.

Then each window's guard out-of-merit share is recovered and the two groups'
distributions are compared. The three outcomes are stated in advance so the
read is not post-hoc:

  * EXCESS mass concentrated at HIGH-but-sub-0.90 OOM share -> **H1**, and
    specifically a THRESHOLD gap: the discriminator is right, the cut is wrong.
  * EXCESS mass concentrated in UNIDENTIFIED windows (no OOM share: no measured
    heat rate, no delivered price, or cogeneration) -> **H1'**, a COVERAGE gap:
    the guard is fail-safe-inert on exactly the units that carry the residual.
  * EXCESS OOM distribution indistinguishable from MATCHED (both low) and
    EXCESS durations short -> **H2**, the published side under-reports.

Usage::

    python scripts/probes/_neiso65_overcount_rootcause.py \\
        --guard data/raw/campd-unit-outages-CAISO.csv \\
        --layup data/raw/campd-unit-outages-layup-CAISO.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from lib.outage_detect import (  # noqa: E402
    MERIT_OOM_FRAC,
    build_merit_order_panel,
)
from market_sim.data import campd  # noqa: E402

RAW = REPO / "data" / "raw"
CROSSWALK = RAW / "reference" / "caiso-resource-eia-crosswalk.csv"
WINDOWS = RAW / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"

# Same exclusion as the neiso-64/65 scorers: ambient capability derates are not
# unavailability events.
_AMBIENT = ("AMBIENT_DUE_TO_TEMP", "AMBIENT_NOT_DUE_TO_TEMP")


def crosswalk() -> pd.DataFrame:
    """Accepted resource -> plant_code rows of the reviewed CAISO crosswalk."""
    cw = pd.read_csv(CROSSWALK)
    return cw[cw["accepted"] == 1][["resource_id", "plant_code"]]


def cnog_daily(years: list[int]) -> pd.DataFrame:
    """Published daily outage MW per crosswalked plant (columns = plant_code).

    Deduplicated to one row per outage ``mrid`` (the raw parquet repeats an
    outage on every trade date it was reported; the last report is the settled
    version), ambient capability derates dropped — identical conventions to
    ``_neiso65_caiso_crosswalk_score.py`` so the two read on the same basis.
    """
    cw = crosswalk()
    d = pd.read_parquet(WINDOWS)
    d = d.sort_values("last_trade_date").groupby("mrid").tail(1)
    d = d[~d["nature_of_work"].isin(_AMBIENT)]
    d = d.merge(cw, on="resource_id", how="inner")
    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    out = pd.DataFrame(0.0, index=idx, columns=sorted(d["plant_code"].unique()))
    for r in d.itertuples(index=False):
        lo = max(pd.Timestamp(r.start).normalize(), idx[0])
        hi = min(pd.Timestamp(r.end).normalize(), idx[-1])
        if hi >= lo:
            out.loc[lo:hi, r.plant_code] += float(r.curtailment_mw)
    return out


def load_extract(path: Path, years: list[int]) -> pd.DataFrame:
    """Extract rows whose window starts in ``years``."""
    d = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    return d[d["outage_start"].dt.year.isin(years)].copy()


def window_hours(row) -> tuple[int, int, int]:
    """``(year, start_hour, stop_hour)`` on that year's Jan-1 hourly clock.

    Inverts the deriver's write step (``start = clock[s]``, ``last =
    clock[e - 1]``), so the recovered span indexes the merit panel exactly as
    the guard did when it judged the window.
    """
    y = int(row.outage_start.year)
    origin = pd.Timestamp(f"{y}-01-01")
    s = int((row.outage_start - origin).total_seconds() // 3600)
    e = int((row.outage_end - origin).total_seconds() // 3600) + 1
    return y, s, e


def match_label(row, pub: pd.DataFrame, frac: float) -> tuple[str, float]:
    """``(MATCHED|EXCESS, published-day share)`` for one extract window.

    A window is MATCHED when its own plant carries published CNOG outage MW on
    at least ``frac`` of the window's days. Plant-grain, not fleet-grain: the
    crosswalk exists precisely so this comparison is like-for-like.
    """
    pc = int(row.facility_id)
    if pc not in pub.columns:
        return "EXCESS", 0.0
    lo = row.outage_start.normalize()
    hi = row.outage_end.normalize()
    seg = pub[pc].loc[lo:hi]
    if seg.empty:
        return "EXCESS", 0.0
    share = float((seg > 0).mean())
    return ("MATCHED" if share >= frac else "EXCESS"), share


def _q(a: np.ndarray, p: float) -> float:
    return float(np.percentile(a, p)) if len(a) else float("nan")


def describe(tag: str, sub: pd.DataFrame) -> None:
    """Print the OOM-share / duration / MW-day profile of one group."""
    gwd = float((sub["unit_capacity_mw"] * sub["duration_days"]).sum()) / 1000.0
    n = len(sub)
    if n == 0:
        print(f"  {tag}: (empty)")
        return
    unid = sub["oom"].isna()
    ident = sub.loc[~unid, "oom"].to_numpy(dtype=float)
    w_unid = float(
        (sub.loc[unid, "unit_capacity_mw"] * sub.loc[unid, "duration_days"]).sum()
    ) / 1000.0
    print(f"  {tag}: {n} windows, {gwd:,.0f} GW-days")
    print(
        f"    UNIDENTIFIED (guard inert, window always kept): "
        f"{int(unid.sum())}/{n} windows = {unid.mean():.0%}; "
        f"{w_unid:,.0f} GW-days = {(w_unid / gwd if gwd else 0):.0%} of the group"
    )
    if len(ident):
        print(
            f"    out-of-merit share (identified n={len(ident)}): "
            f"p25 {_q(ident, 25):.2f}  median {_q(ident, 50):.2f}  "
            f"p75 {_q(ident, 75):.2f}  mean {ident.mean():.2f}"
        )
        # The band that decides H1-as-threshold-gap: high out-of-merit, yet
        # under the 0.90 cut, so the guard kept it.
        near = (ident >= 0.50) & (ident < MERIT_OOM_FRAC)
        print(
            f"    in the 0.50-0.90 near-miss band: {int(near.sum())}/{len(ident)} "
            f"= {near.mean():.0%} of identified windows"
        )
    d = sub["duration_days"].to_numpy(dtype=float)
    print(
        f"    duration (days): median {_q(d, 50):.1f}  p75 {_q(d, 75):.1f}  "
        f"p90 {_q(d, 90):.1f}  max {d.max():.1f}"
    )
    short = d <= 2.0
    print(
        f"    short (<=2 d, the intraday-forced signature): "
        f"{int(short.sum())}/{n} = {short.mean():.0%} of windows, "
        f"{float((sub.loc[short, 'unit_capacity_mw'] * sub.loc[short, 'duration_days']).sum()) / 1000.0:,.0f}"
        f" GW-days"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--guard", required=True, help="Guard-on (committed) extract CSV.")
    ap.add_argument("--layup", default=None, help="Guard's layup companion CSV.")
    ap.add_argument("--iso", default="CAISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--match-frac",
        type=float,
        default=0.25,
        help="Published-day share for MATCHED. Deliberately lenient: a lenient "
        "cut can only SHRINK the EXCESS group, so an EXCESS finding is "
        "conservative.",
    )
    args = ap.parse_args()

    years = sorted(args.years)
    iso = args.iso.upper()
    pub = cnog_daily(years)

    guard = load_extract(Path(args.guard), years)
    # Active-plant scope, matching the re-audit §4 table: crosswalked plants on
    # which the CEMS detector actually has signal. The ten no-window plants are
    # long-term mothball/seasonal-RMR states the model owns through fleet
    # status, not the outage overlay.
    scope = [pc for pc in pub.columns if (guard["facility_id"] == pc).any()]
    g = guard[guard["facility_id"].isin(scope)].copy()
    print(f"\n===== {iso} residual over-count root cause {years} =====")
    print(f"  crosswalked plants: {len(pub.columns)}; active scope: {len(scope)}")
    print(f"  kept (guard-on) windows in scope: {len(g)}")

    # Recover each kept window's guard verdict input from the same panel the
    # guard used. Panels are per ISO-year and expensive, so build once.
    states = campd.states_for_iso(iso)
    panels: dict[int, object] = {}
    for y in years:
        n_full = len(pd.date_range(f"{y}-01-01", f"{y}-12-31 23:00", freq="h"))
        panels[y] = build_merit_order_panel(iso, y, n_full, states)
        p = panels[y]
        print(
            f"  merit panel {y}: "
            + ("UNIDENTIFIED (inert)" if p is None else f"{len(p.srmc)} priced units")
        )

    oom: list[float | None] = []
    lab: list[str] = []
    shr: list[float] = []
    for r in g.itertuples(index=False):
        y, s, e = window_hours(r)
        p = panels.get(y)
        oom.append(
            None
            if p is None
            else p.out_of_merit_share((int(r.facility_id), str(r.unit_id)), s, e)
        )
        lb, sh = match_label(r, pub, args.match_frac)
        lab.append(lb)
        shr.append(sh)
    g["oom"] = pd.Series(oom, index=g.index, dtype="float64")
    g["label"] = lab
    g["pub_day_share"] = shr

    print(
        f"\n  MATCHED = plant carries published outage MW on >= "
        f"{args.match_frac:.0%} of the window's days\n"
    )
    for tag in ("MATCHED", "EXCESS"):
        describe(tag, g[g["label"] == tag])
        print()

    # The headline: how much of the over-count each direction can explain.
    ex = g[g["label"] == "EXCESS"]
    ex_gwd = float((ex["unit_capacity_mw"] * ex["duration_days"]).sum()) / 1000.0
    tot_gwd = float((g["unit_capacity_mw"] * g["duration_days"]).sum()) / 1000.0
    unid = ex["oom"].isna()
    unid_gwd = float(
        (ex.loc[unid, "unit_capacity_mw"] * ex.loc[unid, "duration_days"]).sum()
    ) / 1000.0
    near = ex["oom"].between(0.50, MERIT_OOM_FRAC, inclusive="left")
    near_gwd = float(
        (ex.loc[near, "unit_capacity_mw"] * ex.loc[near, "duration_days"]).sum()
    ) / 1000.0
    print("  ---- attribution of the EXCESS (the over-count itself) ----")
    print(f"    kept total           {tot_gwd:8,.0f} GW-days")
    print(f"    EXCESS               {ex_gwd:8,.0f} GW-days = {ex_gwd / tot_gwd:.0%} of kept")
    print(
        f"      of which UNIDENTIFIED  {unid_gwd:8,.0f} GW-days = "
        f"{(unid_gwd / ex_gwd if ex_gwd else 0):.0%} of EXCESS   [H1' coverage gap]"
    )
    print(
        f"      of which 0.50-0.90 OOM {near_gwd:8,.0f} GW-days = "
        f"{(near_gwd / ex_gwd if ex_gwd else 0):.0%} of EXCESS   [H1 threshold gap]"
    )
    rest = ex_gwd - unid_gwd - near_gwd
    print(
        f"      residual (<0.50 OOM)   {rest:8,.0f} GW-days = "
        f"{(rest / ex_gwd if ex_gwd else 0):.0%} of EXCESS   [H2 / genuinely mechanical]"
    )

    # Per-year, so a single year cannot carry the read.
    print("\n  ---- per year ----")
    for y in years:
        gy = g[g["outage_start"].dt.year == y]
        ey = gy[gy["label"] == "EXCESS"]
        t = float((gy["unit_capacity_mw"] * gy["duration_days"]).sum()) / 1000.0
        e_ = float((ey["unit_capacity_mw"] * ey["duration_days"]).sum()) / 1000.0
        u = ey["oom"].isna()
        n_ = ey["oom"].between(0.50, MERIT_OOM_FRAC, inclusive="left")
        ug = float((ey.loc[u, "unit_capacity_mw"] * ey.loc[u, "duration_days"]).sum()) / 1000.0
        ng = float((ey.loc[n_, "unit_capacity_mw"] * ey.loc[n_, "duration_days"]).sum()) / 1000.0
        print(
            f"    {y}: kept {t:6,.0f}  EXCESS {e_:6,.0f} ({(e_ / t if t else 0):.0%})"
            f"  unid {ug:6,.0f} ({(ug / e_ if e_ else 0):.0%})"
            f"  near-miss {ng:6,.0f} ({(ng / e_ if e_ else 0):.0%})"
        )

    # Which units carry the unidentified excess — names the fixable population.
    if unid.any():
        print("\n  ---- top UNIDENTIFIED-EXCESS units (the H1' population) ----")
        u = ex[unid].copy()
        u["gwd"] = u["unit_capacity_mw"] * u["duration_days"] / 1000.0
        agg = (
            u.groupby(["facility_id", "facility_name", "plant_group"], observed=True)["gwd"]
            .sum()
            .sort_values(ascending=False)
        )
        for (fid, name, grp), v in agg.head(12).items():
            print(f"    {fid:6d} {str(name)[:38]:38s} {str(grp)[:12]:12s} {v:7,.0f} GW-days")


if __name__ == "__main__":
    main()
