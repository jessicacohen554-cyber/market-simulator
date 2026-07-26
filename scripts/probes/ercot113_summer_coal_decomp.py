"""ERCOT-113 Task A: decompose the SUMMER coal over-run before building anything.

ERCOT-112 fixed the annual coal LEVEL (ratio 1.161/1.213/1.207 -> 1.053/1.122/
1.151) but barely touched summer: the treatment arm's Jun-Sep ratio is still
1.169 / 1.292 / 1.256 while the shoulder months sit at or below 1.0. A model
that is right in March and 30 % over in August is missing a summer-specific
driver, not making an offer-level error.

This probe is **no-LP** (rule 15 — it reads the committed ERCOT-112 bundle
sidecars and the raw measured data; it never re-solves). It measures the three
candidates the ERCOT-113 charter enumerated, so a mechanism is only built after
its driver has been shown to exist:

* **(a) summer AMBIENT DERATE of coal capability** — does the measured 60-Day
  DAM live-HSL fall in Jun-Sep *relative to plant rating* more than the rest of
  the year? Reported as the measured ``live_mw / rating_mw`` fraction by month.
  Note the model already pins coal availability to exactly this fraction at
  plant-hour grain (``ercot_thermal_dam_availability_coal`` + ``_hourly`` +
  ``_plant``, all armed in both ERCOT-112 arms), so a summer dip that is
  present in the measured fraction is *already in the model's envelope*.
* **(b) summer PLANNED-OUTAGE / maintenance asymmetry** — does the measured
  live-HSL *level* (MW, not fraction) rise in summer because real coal takes
  its outages in spring/fall? Same pinning argument applies.
* **(c) DISPLACEMENT rather than a coal error** — bin model-minus-actual coal
  against model-minus-actual gas by month. If they are mirror images the
  marginal unit is being mis-ranked in summer, which points at the summer
  gas-price / heat-rate basis, not at coal availability.

The decisive quantity for (a)/(b) is **utilization of the measured envelope**:
``model_coal_mw / measured_live_mw`` versus ``actual_coal_mw / measured_live_mw``
by month. If the model's envelope already matches the measured one (it is
pinned to it) and the model still over-runs in summer, the over-run is
*within-envelope utilization* -- exactly what ERCOT-111 found at annual scale
(99 % economic dispatch inside the real committed HSL envelope) -- and (a)/(b)
cannot be the driver.

Usage:
    python scripts/probes/ercot113_summer_coal_decomp.py \
        --arm results/calibration/ercot112_coal_marginal_hr_fullspan
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.actuals import load_eia_hourly_benchmark  # noqa: E402

YEARS = (2023, 2024, 2025)
SUMMER = (6, 7, 8, 9)
# The measured 60-Day DAM disclosure, site-hour grain: the same artifact the
# ercot_thermal_dam_availability overlay reads. live_mw is the committed
# high-sustained-limit; rating_mw is the plant rating.
_DAM_SITE = REPO / "data/raw/ercot-thermal-dam-availability-site-hourly.parquet"


def _month_of_hour() -> np.ndarray:
    """Month index (1-12) for each of the 8760 model hours (non-leap clock)."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])


def _model_series(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Return (coal MW, gas MW) hourly for a bundle-year, or ``None``.

    Class tokens match ``scripts/probes/ercot112_score_coal_arms.py`` so the
    aggregates are directly comparable to the published ERCOT-112 numbers.
    """
    path = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df[df["pass"] == "P1"]
    if df.empty:
        return None
    kl = df["klass"].astype(str).str.upper()
    coal = df[kl.str.contains("COAL")]
    gas = df[kl.str.startswith(("CC_", "CT_", "ST_"))]

    def _sum(frame: pd.DataFrame) -> np.ndarray:
        if frame.empty:
            return np.zeros(8760)
        return (
            frame.groupby("hour")["mw"]
            .sum()
            .reindex(range(8760), fill_value=0.0)
            .to_numpy(dtype=float)
        )

    return _sum(coal), _sum(gas)


def _measured_coal_envelope(year: int) -> pd.DataFrame | None:
    """Monthly measured coal DAM envelope: live MW, rating MW, and coverage.

    Aggregates the site-hour disclosure to a system COAL total per date-hour,
    then to a calendar-month mean. ``days`` is the number of disclosed days in
    the month -- the overlay leaves uncovered days on the statistical model, so
    a month with thin coverage is not evidence either way.
    """
    if not _DAM_SITE.exists():
        return None
    df = pd.read_parquet(_DAM_SITE, columns=["date", "class", "he", "live_mw", "rating_mw"])
    df = df[df["class"].astype(str) == "COAL"]
    if df.empty:
        return None
    dt = pd.to_datetime(df["date"].astype(str))
    df = df.assign(year=dt.dt.year.to_numpy(), month=dt.dt.month.to_numpy())
    df = df[df["year"] == year]
    if df.empty:
        return None
    # System total per (date, hour-ending), then the mean across those hours.
    per_hour = df.groupby(["month", "date", "he"], observed=True)[
        ["live_mw", "rating_mw"]
    ].sum()
    out = per_hour.groupby("month").mean()
    out["frac"] = out["live_mw"] / out["rating_mw"].where(out["rating_mw"] > 0)
    out["days"] = df.groupby("month")["date"].nunique()
    return out


def year_table(bundle: Path, year: int) -> pd.DataFrame | None:
    """Monthly decomposition table for one year."""
    ms = _model_series(bundle, year)
    act = load_eia_hourly_benchmark("ERCOT", year)
    if ms is None or act is None:
        return None
    m_coal, m_gas = ms
    a_coal = np.asarray(act["coal"], dtype=float)
    a_gas = np.asarray(act["gas"], dtype=float)
    mo = _month_of_hour()

    rows = []
    env = _measured_coal_envelope(year)
    for m in range(1, 13):
        sel = mo == m
        mc, ac = m_coal[sel].mean(), a_coal[sel].mean()
        mg, ag = m_gas[sel].mean(), a_gas[sel].mean()
        row = {
            "month": m,
            "model_coal": mc,
            "act_coal": ac,
            "coal_ratio": mc / ac if ac > 0 else np.nan,
            "d_coal": mc - ac,
            "model_gas": mg,
            "act_gas": ag,
            "d_gas": mg - ag,
            "live_mw": np.nan,
            "rating_mw": np.nan,
            "meas_frac": np.nan,
            "days": 0,
            "model_util": np.nan,
            "act_util": np.nan,
        }
        if env is not None and m in env.index:
            e = env.loc[m]
            row["live_mw"] = float(e["live_mw"])
            row["rating_mw"] = float(e["rating_mw"])
            row["meas_frac"] = float(e["frac"])
            row["days"] = int(e["days"])
            if e["live_mw"] > 0:
                row["model_util"] = mc / float(e["live_mw"])
                row["act_util"] = ac / float(e["live_mw"])
        rows.append(row)
    return pd.DataFrame(rows).set_index("month")


def main() -> None:
    """Print the three-candidate monthly decomposition for every year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--arm",
        type=Path,
        default=REPO / "results/calibration/ercot112_coal_marginal_hr_fullspan",
        help="bundle to decompose (default: the ERCOT-112 treatment arm)",
    )
    args = ap.parse_args()

    tables: dict[int, pd.DataFrame] = {}
    for y in YEARS:
        t = year_table(args.arm, y)
        if t is None:
            print(f"{y}: -- not available --")
            continue
        tables[y] = t

    for y, t in tables.items():
        print(f"\n=== {y} — monthly coal decomposition (arm: {args.arm.name}) ===")
        print(
            f"{'mo':>3}{'days':>6}{'live MW':>10}{'rating':>9}{'meas':>7}"
            f"{'m_coal':>9}{'a_coal':>9}{'ratio':>7}"
            f"{'m_util':>8}{'a_util':>8}{'dCoal':>8}{'dGas':>8}"
        )
        for m, r in t.iterrows():
            def _f(v: float, w: int, p: int) -> str:
                return f"{v:{w}.{p}f}" if np.isfinite(v) else f"{'--':>{w}}"

            print(
                f"{m:>3}{int(r['days']):>6}{_f(r['live_mw'], 10, 0)}"
                f"{_f(r['rating_mw'], 9, 0)}{_f(r['meas_frac'], 7, 3)}"
                f"{r['model_coal']:9.0f}{r['act_coal']:9.0f}{r['coal_ratio']:7.3f}"
                f"{_f(r['model_util'], 8, 3)}{_f(r['act_util'], 8, 3)}"
                f"{r['d_coal']:8.0f}{r['d_gas']:8.0f}"
            )

    # ---- Candidate adjudication -------------------------------------------
    print("\n\n################ CANDIDATE ADJUDICATION ################")

    print("\n--- (a) summer AMBIENT DERATE: measured live/rating by season ---")
    print(f"{'year':>6}{'shoulder':>11}{'summer':>10}{'delta':>9}{'sh days':>9}{'su days':>9}")
    for y, t in tables.items():
        su = t[t.index.isin(SUMMER)]
        sh = t[~t.index.isin(SUMMER)]
        su_f = su["meas_frac"].mean()
        sh_f = sh["meas_frac"].mean()
        print(
            f"{y:>6}{sh_f:11.3f}{su_f:10.3f}{su_f - sh_f:+9.3f}"
            f"{int(sh['days'].sum()):9d}{int(su['days'].sum()):9d}"
        )
    print(
        "  READ: a NEGATIVE delta = the measured fraction DIPS in summer (an ambient\n"
        "  derate exists in the data). Because the overlay pins the model's coal\n"
        "  availability to this very fraction at plant-hour grain, whatever dip is\n"
        "  here is ALREADY in the model's envelope -- it is not a missing driver."
    )

    print("\n--- (b) summer PLANNED-OUTAGE asymmetry: measured live MW by season ---")
    print(f"{'year':>6}{'shoulder':>11}{'summer':>10}{'delta':>9}{'pct':>9}")
    for y, t in tables.items():
        su = t[t.index.isin(SUMMER)]["live_mw"].mean()
        sh = t[~t.index.isin(SUMMER)]["live_mw"].mean()
        print(f"{y:>6}{sh:11.0f}{su:10.0f}{su - sh:+9.0f}{(su / sh - 1) * 100:+8.1f}%")
    print(
        "  READ: a POSITIVE delta = real coal genuinely has MORE capability committed\n"
        "  in summer (spring/fall maintenance). Same pinning argument as (a)."
    )

    print("\n--- (a)+(b) DECISIVE: utilization of the MEASURED envelope ---")
    print(
        f"{'year':>6}{'season':>10}{'model util':>12}{'act util':>10}"
        f"{'gap pp':>9}{'model MW':>10}{'act MW':>9}"
    )
    for y, t in tables.items():
        for name, sel in (("shoulder", ~t.index.isin(SUMMER)), ("summer", t.index.isin(SUMMER))):
            s = t[sel]
            mu, au = s["model_util"].mean(), s["act_util"].mean()
            print(
                f"{y:>6}{name:>10}{mu:12.3f}{au:10.3f}{(mu - au) * 100:+9.1f}"
                f"{s['model_coal'].mean():10.0f}{s['act_coal'].mean():9.0f}"
            )
    print(
        "  READ: if the model's envelope is pinned to the measured one, then any\n"
        "  summer over-run shows up as a UTILIZATION gap, not a capability gap.\n"
        "  A summer gap much larger than the shoulder gap = within-envelope\n"
        "  over-dispatch => candidates (a) and (b) are NOT the driver."
    )

    print("\n--- (c) DISPLACEMENT: is dCoal the mirror of dGas? ---")
    print(
        f"{'year':>6}{'corr(dCoal,dGas)':>19}{'sum dCoal':>12}{'sum dGas':>11}"
        f"{'offset %':>10}{'su dCoal':>10}{'su dGas':>10}"
    )
    for y, t in tables.items():
        dc, dg = t["d_coal"].to_numpy(), t["d_gas"].to_numpy()
        corr = float(np.corrcoef(dc, dg)[0, 1])
        su = t[t.index.isin(SUMMER)]
        offset = -dg.sum() / dc.sum() * 100.0 if dc.sum() != 0 else np.nan
        print(
            f"{y:>6}{corr:19.3f}{dc.sum():12.0f}{dg.sum():11.0f}{offset:9.1f}%"
            f"{su['d_coal'].mean():10.0f}{su['d_gas'].mean():10.0f}"
        )
    print(
        "  READ: corr near -1 with offset near 100 % = the coal surplus is exactly the\n"
        "  gas deficit, i.e. a MERIT-ORDER mis-ranking (a displacement error), not a\n"
        "  coal availability error. That points at the summer gas-price / heat-rate\n"
        "  basis as the driver to measure next."
    )


if __name__ == "__main__":
    main()
