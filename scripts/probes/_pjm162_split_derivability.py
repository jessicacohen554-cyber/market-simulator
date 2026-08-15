"""pjm-162 Phase 0(b): is a planned/forced split DERIVABLE from the CAMPD record?

THE QUESTION. pjm-161 SS7.4 named, as the second successor the same measurement
selects, "a derivation that splits the CAMPD-detected windows into
maintenance-season planned versus event-driven forced [which] would let the
forced components be compared like with like". Route (1) needs a comparison
basis; pjm-161 SS7.2 measured that neither published basis works against the
model's unsplit envelope (the TOTAL is dominated by planned outages scheduled
AWAY from peaks; the FORCED component is trivially inert against a 41 GW
envelope that carries planned outages too).

This probe asks whether the split can be derived AT ALL, from the source data
the model already consumes, and identified against PJM's own published typed
record (`gen_outages_by_type`: planned / maintenance / forced daily MW). That
identification target is measured operator data, not a residual (rule 23).

WHAT IS MEASURED, and the order matters because the second test can kill the
first:

  1. SEPARABILITY. Stratify the CAMPD-detected windows by duration and by start
     month, and correlate each stratum's daily MW against PJM's published
     FORCED series and against its published PLANNED+MAINTENANCE series. A
     derivable split needs a stratum that tracks forced and a stratum that
     tracks planned, with the correlations clearly separated.

  2. THE KILL TEST — EVENT RESPONSE. pjm-161's defect is that the WHOLE envelope
     FALLS during winter stress events (Elliott: 15.6 GW, the lowest derate of
     2022, against PJM's published 31-41 GW). A split only rescues route (1) if
     SOME subset of the CAMPD envelope RISES during those events. If every
     stratum falls, the forced-outage information is simply ABSENT from the
     CAMPD record — the detector cannot see it, by construction — and no
     partition of an envelope that lacks the signal can supply it. That would
     make the split necessary but NOT sufficient, and route (1) unbuildable
     from this source.

Both tests are pure CSV/parquet arithmetic on the raw record. No LP, no fleet
build, no solve. Years 2022-2025 are READ (2022 from already-committed raw
inputs only, the pjm-157/158/161 posture); nothing is solved, scored or
registered.

Run:  PYTHONPATH=. uv run python scripts/probes/_pjm162_split_derivability.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

RAW = REPO / "data" / "raw"
E930 = RAW / "eia-930-hourly" / "PJM hourly.parquet"
OUT_PATH = REPO / "results/calibration/_pjm162_split_derivability.json"

#: The two window families the model's PJM envelope actually consumes
#: (same SOURCES tuple as _pjm161_outage_inversion.py).
SOURCES = ("campd-unit-outages-PJM", "campd-unit-outages-short-PJM")

#: Duration strata (days). GADS practice separates a short unscheduled trip from
#: a multi-week scheduled overhaul; these are REPORTING boundaries used to test
#: separability, not fitted thresholds — every stratum is reported.
STRATA = ((0.0, 3.0), (3.0, 7.0), (7.0, 21.0), (21.0, 60.0), (60.0, 1e9))

EVENTS = {
    2022: ("2022-12-23", "2022-12-26", "Elliott"),
    2023: ("2023-02-03", "2023-02-04", "Feb cold snap"),
    2024: ("2024-01-15", "2024-01-17", "Heather"),
    2025: ("2025-01-21", "2025-01-23", "Enzo"),
}

YEARS = (2022, 2023, 2024, 2025)


def load_windows() -> pd.DataFrame:
    """Return every CAMPD-detected outage window the model consumes."""
    frames = []
    for name in SOURCES:
        d = pd.read_csv(RAW / f"{name}.csv")
        d["source"] = name
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    d["s"] = pd.to_datetime(d["outage_start"])
    d["e"] = pd.to_datetime(d["outage_end"])
    return d


def daily_mw(windows: pd.DataFrame, year: int) -> pd.Series:
    """Daily derated MW asserted by ``windows`` on ``year``'s calendar."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    out = pd.Series(0.0, index=days)
    w = windows[(windows["e"] >= days[0]) & (windows["s"] <= days[-1])]
    for _, r in w.iterrows():
        lo = max(r["s"].normalize(), days[0])
        hi = min(r["e"].normalize(), days[-1])
        if hi >= lo:
            out.loc[lo:hi] += r["unit_capacity_mw"]
    return out


def published(year: int) -> pd.DataFrame:
    """PJM RTO published daily outage MW by type (lead_days == 0 actuals)."""
    from market_sim.data.pjm_outages import _load_pjm_outage_source

    df = _load_pjm_outage_source(year)
    if df is None:
        return pd.DataFrame()
    df = df[(df["lead_days"] == 0) & (df["region"] == "PJM RTO")].copy()
    df["d"] = pd.to_datetime(df["forecast_date"]).dt.normalize()
    df = df[df["d"].dt.year == year].groupby("d").mean(numeric_only=True)
    return df


def net_load_daily(year: int) -> pd.Series:
    d = pd.read_parquet(E930)
    d = d[pd.to_datetime(d["Local date"]).dt.year == year].copy()
    d["lt"] = pd.to_datetime(d["Local time"])
    d = d.set_index("lt").sort_index()
    dem = pd.to_numeric(d["Demand"], errors="coerce")
    vre = pd.to_numeric(d["NG: WND"], errors="coerce").fillna(0) + pd.to_numeric(
        d["NG: SUN"], errors="coerce"
    ).fillna(0)
    return (dem - vre).dropna().resample("D").max()


def main() -> None:
    w = load_windows()
    result: dict = {"years": {}}

    for year in YEARS:
        pub = published(year)
        if pub.empty:
            continue
        nl = net_load_daily(year)
        pub_forced = pub["forced_outages_mw"]
        pub_plan = pub["planned_outages_mw"] + pub["maintenance_outages_mw"]

        s, e, ev_label = EVENTS[year]
        ev_days = pd.date_range(s, e, freq="D")

        yr: dict = {"event": ev_label, "strata": {}}

        # ---------- test 1 + 2, per duration stratum ----------
        for lo, hi in STRATA:
            sub = w[(w["duration_days"] >= lo) & (w["duration_days"] < hi)]
            if sub.empty:
                continue
            mw = daily_mw(sub, year)
            j = pd.DataFrame({"mw": mw}).join(
                pd.DataFrame({"f": pub_forced, "p": pub_plan}), how="inner"
            ).dropna()
            if len(j) < 30:
                continue
            ann = float(j["mw"].mean())
            ev_mw = float(mw.reindex(ev_days).dropna().mean())
            q = j["mw"].copy()
            nlj = nl.reindex(j.index).dropna()
            common = j.index.intersection(nlj.index)
            top1 = nlj.loc[common].rank(pct=True) >= 0.99
            key = f"{lo:g}-{hi:g}d" if hi < 1e8 else f">{lo:g}d"
            yr["strata"][key] = {
                "n_windows": int(len(sub)),
                "annual_mean_MW": ann,
                "corr_vs_published_FORCED": float(np.corrcoef(j["mw"], j["f"])[0, 1]),
                "corr_vs_published_PLANNED_MAINT": float(
                    np.corrcoef(j["mw"], j["p"])[0, 1]
                ),
                "corr_vs_netload": float(
                    np.corrcoef(q.loc[common], nlj.loc[common])[0, 1]
                ),
                "event_mean_MW": ev_mw,
                "event_over_annual": (ev_mw / ann) if ann > 0 else None,
                "top1pct_netload_MW": float(q.loc[common][top1].mean()),
                "top1pct_over_annual": (
                    float(q.loc[common][top1].mean()) / ann if ann > 0 else None
                ),
            }

        # ---------- the published reference, same statistics ----------
        for label, ser in (("PUBLISHED_forced", pub_forced), ("PUBLISHED_planned_maint", pub_plan)):
            ann = float(ser.mean())
            ev_mw = float(ser.reindex(ev_days).dropna().mean())
            nlj = nl.reindex(ser.index).dropna()
            common = ser.index.intersection(nlj.index)
            top1 = nlj.loc[common].rank(pct=True) >= 0.99
            yr["strata"][label] = {
                "n_windows": None,
                "annual_mean_MW": ann,
                "corr_vs_published_FORCED": float(np.corrcoef(ser, pub_forced)[0, 1]),
                "corr_vs_published_PLANNED_MAINT": float(np.corrcoef(ser, pub_plan)[0, 1]),
                "corr_vs_netload": float(
                    np.corrcoef(ser.loc[common], nlj.loc[common])[0, 1]
                ),
                "event_mean_MW": ev_mw,
                "event_over_annual": (ev_mw / ann) if ann > 0 else None,
                "top1pct_netload_MW": float(ser.loc[common][top1].mean()),
                "top1pct_over_annual": (
                    float(ser.loc[common][top1].mean()) / ann if ann > 0 else None
                ),
            }

        result["years"][str(year)] = yr

    OUT_PATH.write_text(json.dumps(result, indent=2))

    print()
    print("=" * 108)
    print("pjm-162 PHASE 0(b) — can the CAMPD envelope be split into planned vs forced?")
    print("=" * 108)
    print()
    print("TEST 1 (separability) = the two corr columns; TEST 2 (KILL) = event/ann and top1%/ann")
    print("A stratum carrying forced-outage information must have event/ann > 1 (it RISES in the event).")
    print()
    hdr = (
        f"{'year':>5} {'stratum':>22} {'n win':>6} {'ann MW':>9} "
        f"{'r vs FORC':>10} {'r vs PLAN':>10} {'r vs NL':>8} "
        f"{'ev MW':>9} {'ev/ann':>7} {'top1/ann':>9}"
    )
    for year in YEARS:
        if str(year) not in result["years"]:
            continue
        blk = result["years"][str(year)]
        print(f"--- {year} ({blk['event']}) " + "-" * 84)
        print(hdr)
        for k, v in blk["strata"].items():
            nw = v["n_windows"]
            print(
                f"{year:>5} {k:>22} {(str(nw) if nw is not None else '-'):>6} "
                f"{v['annual_mean_MW']:>9,.0f} "
                f"{v['corr_vs_published_FORCED']:>10.3f} "
                f"{v['corr_vs_published_PLANNED_MAINT']:>10.3f} "
                f"{v['corr_vs_netload']:>8.3f} "
                f"{v['event_mean_MW']:>9,.0f} "
                f"{(v['event_over_annual'] or 0):>7.2f} "
                f"{(v['top1pct_over_annual'] or 0):>9.2f}"
            )
        print()
    print(f"written: {OUT_PATH}")


if __name__ == "__main__":
    main()
