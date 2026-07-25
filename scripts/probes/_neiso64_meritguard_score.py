"""neiso-64 — score a CAMPD unit-outage extract against its ISO's PUBLISHED series.

STEP 3 of the CAMPD economic-layup fix charter
(``docs/handoffs/campd-economic-layup-fix-charter-2026-07.md``): the merit-order
guard's corrected extract is validated against each ISO's own published
outage/availability instrument, on **level** and **seasonal shape**, at NO SOLVE
COST. The published outage MW is the target; the LMP residual is explicitly not
(charter section 4 — rule 14 reconciles an input to its own measurement, rule 13
forbids reconciling it to a dispatch outcome).

Published instruments, one per ISO:

* **NEISO** — ISO-NE Morning Report Section 3 ``gen_outages_reductions_mw``
  (``data/raw/neiso-operable-capacity/``). Uniquely, ISO-NE also publishes
  ``uncommitted_available_gen_nonfast_mw`` — available-but-not-committed
  capacity, i.e. the economic-layup population itself — so NEISO carries a
  **positive control**: the guard's KEPT windows should track the outage column
  and its VETOED windows the uncommitted column.
* **MISO** — ``miso_outages_estimated_<Y>.csv`` Forced + Planned + Unplanned.
* **PJM** — ``gen_outages_by_type_<Y>.csv``, region ``PJM RTO``, ``lead_days=0``.
* **CAISO** — the Curtailed and Non-Operational Generator report, deduplicated
  to one row per outage ``mrid`` (the raw parquet repeats each outage on every
  trade date it was reported, so summing it raw over-counts ~5x).
* **ERCOT** — ``ercot-thermal-dam-availability.csv`` (60-day DAM disclosure),
  ``rating_mw - live_mw``. Owner-authorised 2026-07-25 as ERCOT's anchor with
  the caveat recorded below.
* **NYISO** — none identified; its extract stays UNVERIFIED.

**Scope caveats — read before quoting a level ratio.** The extract is
CEMS-thermal only (coal / CC / gas-steam); several published series are
whole-fleet. So a level *ratio* is only interpretable where the extract exceeds
a whole-fleet published total (an unambiguous over-count, as in NEISO), and the
robust cross-ISO axis is the **monthly correlation**. ERCOT's DAM series is
offered-capacity-based, so it conflates mechanical unavailability with a unit
that simply did not offer — i.e. it carries some layup itself.

Usage::

    python scripts/probes/_neiso64_meritguard_score.py \\
        --iso NEISO --base data/raw/campd-unit-outages-NEISO.csv \\
        --guard /tmp/NEISO_guard.csv --layup /tmp/NEISO_guard-layup.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"

SEASONS = {12: "DJF", 1: "DJF", 2: "DJF", 3: "MAM", 4: "MAM", 5: "MAM",
           6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
# CAISO natures of work that are ambient CAPABILITY derates, not unavailability
# events; excluded so the comparison is against outages, which is what the CAMPD
# full-stop detector produces.
_CAISO_AMBIENT = ("AMBIENT_DUE_TO_TEMP", "AMBIENT_NOT_DUE_TO_TEMP")
# CAISO resource-id fragments that mark a non-thermal resource. A name heuristic,
# not a crosswalk — stated as such wherever a CAISO number is quoted.
_CAISO_NONTHERMAL = ("SOLAR", "WIND", "BATT", "_PV", "ESS", "HYDRO", "PUMP")


def daily_mw(win: pd.DataFrame, years: list[int]) -> pd.Series:
    """Daily outage-MW series implied by a window set."""
    idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
    out = pd.Series(0.0, index=idx)
    for r in win.itertuples(index=False):
        lo = max(pd.Timestamp(r.outage_start), idx[0])
        hi = min(pd.Timestamp(r.outage_end), idx[-1])
        if hi >= lo:
            out.loc[lo:hi] += float(r.unit_capacity_mw)
    return out


def published(iso: str, years: list[int]) -> pd.Series | None:
    """The ISO's published outage series, daily MW, or ``None`` if it has none."""
    iso = iso.upper()
    if iso == "NEISO":
        d = pd.concat([
            pd.read_csv(RAW / "neiso-operable-capacity" /
                        f"neiso_operable_capacity_{y}.csv", parse_dates=["report_date"])
            for y in years
        ]).set_index("report_date")
        return d["gen_outages_reductions_mw"].astype(float)
    if iso == "MISO":
        d = pd.concat([
            pd.read_csv(RAW / "miso-generation-outages" /
                        f"miso_outages_estimated_{y}.csv", parse_dates=["interval_date"])
            for y in years
        ]).set_index("interval_date")
        return (d["MISO_Forced"] + d["MISO_Planned"] + d["MISO_Unplanned"]).astype(float)
    if iso == "PJM":
        d = pd.concat([
            pd.read_csv(RAW / "pjm-outages" / "by-year" /
                        f"gen_outages_by_type_{y}.csv", parse_dates=["forecast_date"])
            for y in years
        ])
        d = d[(d["region"] == "PJM RTO") & (d["lead_days"] == 0)]
        return d.groupby("forecast_date")["total_outages_mw"].mean().astype(float)
    if iso == "ERCOT":
        d = pd.read_csv(RAW / "ercot-thermal-dam-availability.csv", parse_dates=["date"])
        d = d[d["date"].dt.year.isin(years)]
        return (d.assign(out=d["rating_mw"] - d["live_mw"])
                .groupby("date")["out"].sum().astype(float))
    if iso == "CAISO":
        d = pd.read_parquet(
            RAW / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"
        )
        # One row per outage: the raw file repeats an outage on every trade date
        # it was reported, so the last report is the settled version.
        d = d.sort_values("last_trade_date").groupby("mrid").tail(1)
        d = d[~d["nature_of_work"].isin(_CAISO_AMBIENT)]
        rid = d["resource_id"].astype(str).str.upper()
        d = d[~rid.str.contains("|".join(_CAISO_NONTHERMAL), regex=True)]
        idx = pd.date_range(f"{min(years)}-01-01", f"{max(years)}-12-31", freq="D")
        out = pd.Series(0.0, index=idx)
        for r in d.itertuples(index=False):
            lo = max(pd.Timestamp(r.start).normalize(), idx[0])
            hi = min(pd.Timestamp(r.end).normalize(), idx[-1])
            if hi >= lo:
                out.loc[lo:hi] += float(r.curtailment_mw)
        return out
    return None


def neiso_uncommitted(years: list[int]) -> pd.Series:
    """ISO-NE's published available-but-NOT-COMMITTED capacity (the layup bucket)."""
    d = pd.concat([
        pd.read_csv(RAW / "neiso-operable-capacity" /
                    f"neiso_operable_capacity_{y}.csv", parse_dates=["report_date"])
        for y in years
    ]).set_index("report_date")
    return d["uncommitted_available_gen_nonfast_mw"].astype(float)


def score(series: pd.Series, pub: pd.Series, years: list[int]) -> list[str]:
    """One line per year: level ratio, monthly correlation, seasonal ratios."""
    j = pd.concat([series.rename("m"), pub.rename("p")], axis=1).dropna()
    j = j[j["p"] > 0]
    lines = []
    for y in years:
        jj = j[j.index.year == y]
        if jj.empty:
            continue
        mm = jj.groupby(jj.index.month)[["m", "p"]].mean()
        jj = jj.assign(s=[SEASONS[t.month] for t in jj.index])
        g = jj.groupby("s")[["m", "p"]].mean()
        cells = " ".join(f"{s} {g.loc[s, 'm'] / g.loc[s, 'p']:.2f}x"
                         for s in ("DJF", "MAM", "JJA", "SON") if s in g.index)
        lines.append(
            f"    {y}: {jj['m'].mean():7.0f}/{jj['p'].mean():7.0f} = "
            f"{jj['m'].mean() / jj['p'].mean():.2f}x  r {mm['m'].corr(mm['p']):+.2f}"
            f"   | {cells}"
        )
    return lines


def placebo(base: pd.DataFrame, target_gwd: float, pub: pd.Series,
            years: list[int], draws: int = 30) -> dict[int, tuple[float, float]]:
    """Null model: drop the SAME GW-days at random and re-score the shape.

    Answers "would removing this much capacity have improved the correlation
    anyway?". A guard that does not clear the placebo p95 has not discriminated,
    it has only subtracted.
    """
    gwd = (base["unit_capacity_mw"] * base["duration_days"]).to_numpy(dtype=float)
    rng = np.random.default_rng(2026)
    rs: dict[int, list[float]] = {y: [] for y in years}
    for _ in range(draws):
        pick = np.zeros(len(base), dtype=bool)
        acc = 0.0
        for i in rng.permutation(len(base)):
            if acc >= target_gwd:
                break
            pick[i] = True
            acc += gwd[i]
        s = daily_mw(base[~pick], years)
        j = pd.concat([s.rename("m"), pub.rename("p")], axis=1).dropna()
        j = j[j["p"] > 0]
        for y in years:
            jj = j[j.index.year == y]
            if jj.empty:
                continue
            mm = jj.groupby(jj.index.month)[["m", "p"]].mean()
            rs[y].append(mm["m"].corr(mm["p"]))
    return {y: (float(np.mean(v)), float(np.percentile(v, 95)))
            for y, v in rs.items() if v}


def _load(path: Path, years: list[int]) -> pd.DataFrame:
    d = pd.read_csv(path, parse_dates=["outage_start", "outage_end"])
    return d[d["outage_start"].dt.year.isin(years)].copy()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--base", required=True, help="Baseline (guard-off) extract CSV.")
    ap.add_argument("--guard", required=True, help="Guard-on extract CSV.")
    ap.add_argument("--layup", default=None, help="Guard's layup companion CSV.")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    years = sorted(args.years)
    base = _load(Path(args.base), years)
    guard = _load(Path(args.guard), years)
    pub = published(args.iso, years)
    print(f"\n===== {args.iso} {years} =====")
    print(f"  windows: baseline {len(base)}  guard-on {len(guard)}")
    if pub is None:
        print("  NO PUBLISHED INSTRUMENT — this extract remains UNVERIFIED.")
        return
    print("  BASELINE\n" + "\n".join(score(daily_mw(base, years), pub, years)))
    print("  GUARD ON\n" + "\n".join(score(daily_mw(guard, years), pub, years)))

    if args.layup and Path(args.layup).exists():
        lay = _load(Path(args.layup), years)
        gwd = float((lay["unit_capacity_mw"] * lay["duration_days"]).sum())
        print(f"\n  reclassified layup: {len(lay)} windows, {gwd / 1000:,.0f} GW-days")
        print("  LAYUP windows vs published OUTAGES\n"
              + "\n".join(score(daily_mw(lay, years), pub, years)))
        if args.iso.upper() == "NEISO":
            unc = neiso_uncommitted(years)
            print("  POSITIVE CONTROL — vs published UNCOMMITTED-AVAILABLE")
            print("   kept:\n" + "\n".join(score(daily_mw(guard, years), unc, years)))
            print("   layup:\n" + "\n".join(score(daily_mw(lay, years), unc, years)))
        pl = placebo(base, gwd, pub, years)
        j = pd.concat([daily_mw(guard, years).rename("m"), pub.rename("p")],
                      axis=1).dropna()
        j = j[j["p"] > 0]
        print("\n  PLACEBO (same GW-days dropped at random, 30 draws)")
        for y in years:
            jj = j[j.index.year == y]
            if jj.empty or y not in pl:
                continue
            mm = jj.groupby(jj.index.month)[["m", "p"]].mean()
            r = mm["m"].corr(mm["p"])
            mean, p95 = pl[y]
            verdict = "BEATS" if r > p95 else "inside"
            print(f"    {y}: guard r {r:+.2f}  placebo mean {mean:+.2f} "
                  f"p95 {p95:+.2f}  -> {verdict} p95")


if __name__ == "__main__":
    main()
