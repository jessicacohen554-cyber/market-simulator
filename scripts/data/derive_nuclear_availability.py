"""Derive per-ISO per-reactor DAILY nuclear availability from NRC status reports.

The PJM generalization of ``scripts/data/derive_ercot_nuclear_availability.py``
(pjm-nuc-1b, owner-ordered 2026-07-16 —
``docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md`` §8.2.1):
``NUCLEAR_MONTHLY_CF_BY_YEAR`` carries the measured EIA-923 fleet monthly
energy but smears it uniformly across all reactors and every hour of the
month, so a unit-specific refuel/trip inside a scarcity hour is invisible
(the measured 2025 summer-tail smear error is +147 MW mean — small, and
fixed here with the real mechanism rather than left in the smear).

This script reconciles two measured sources at their native grain:

* **Timing (daily, per reactor)** — the NRC daily Power Reactor Status
  reports (``data/raw/nrc-reactor-status/<YYYY>PowerStatus.txt``,
  ``scripts/data/fetch_nrc_reactor_status.py``): ``avail_raw = Power / 100``
  per reactor-day. Unlike the ERCOT 60-Day-DAM HSL basis this is a direct
  physical measurement (percent of licensed thermal power at the morning
  report) — no healthy-day reference is needed and there is no economic-
  withholding confound. Daily grain means a mid-day trip appears in the
  NEXT morning's report; disclosed, not corrected.
* **Level (monthly energy)** — the committed EIA-923 anchor
  (``NUCLEAR_MONTHLY_CF_BY_YEAR[iso]``): raw NRC availability energy sits
  0.7–1.6 %/yr below the anchor (winter-uprate / thermal-vs-net basis
  wedge), so, exactly as in the ERCOT deriver, EVENT days
  (raw < :data:`EVENT_RAW_MAX`, frozen 0.90 — refuel windows, trips, ramps,
  deep derates) stay exactly as measured and the remaining pool is scaled
  by one per-month fixed-point factor (per-day cap 1.0, scale clip 1.25,
  both frozen) so the fleet-month availability energy reproduces the anchor
  exactly — **the anchor owns the LEVEL, NRC owns the TIMING**. A month the
  capped fixed-point still cannot bring within :data:`WEDGE_TOL` of the
  anchor (uprate-season months where NRC %-thermal x nameplate cannot
  express the measured net energy) is DROPPED — the loader NaNs it and the
  smear (the anchor itself) stands, so the overlay never posts a level the
  basis wedge is known to bias low.

Output: ``data/raw/nuclear-availability-<ISO>.csv`` with one row per
(reactor, date): ``date, plant_code, unit_no, reactor, avail_raw, avail``
(``avail`` = the reconciled series the model consumes) — the same schema as
``data/raw/ercot-nuclear-availability.csv``, consumed by
``data.outages.nuclear_unit_availability_series`` under
``ScenarioConfig.nuclear_unit_availability``.

Admissibility (rule 13): a refuel window / reactor power state is a physical
availability event — the same class as the CAMPD fossil outage windows and
the ERCOT nuclear overlay — produced forward by the static
``NUCLEAR_MONTHLY_CF`` / refuel-block scheduling, and it responds to changed
conditions. Zero fitted scalars: EVENT_RAW_MAX / cap / clip are inherited
frozen from the ERCOT deriver (rule 23: re-run only when a new NRC year
lands; cite the data change).

Usage::

    python scripts/data/derive_nuclear_availability.py --iso PJM [--check]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
)

NRC_DIR = REPO / "data" / "raw" / "nrc-reactor-status"
YEARS = (2023, 2024, 2025)

# Frozen constants inherited verbatim from derive_ercot_nuclear_availability
# (never re-tuned here — rule 23). A unit-day BELOW EVENT_RAW_MAX is a
# measured event day (refuel window, trip, ramp, deep derate) kept exactly as
# measured; days at/above it form the pool the monthly EIA-923 anchor is
# solved over.
EVENT_RAW_MAX = 0.90
SCALE_CLIP = 1.25
# Off-anchor tolerance (the ERCOT deriver's existing 1 % warning threshold,
# reused here as a month-level FALLBACK criterion, not a new tuned scalar).
# A month whose reconciliation still misses the anchor after the capped
# fixed-point ("event days bind") is a month where the NRC thermal-% basis is
# measurably misaligned to the model's nameplate-net representation — the
# winter-uprate wedge: net capability exceeds nameplate in cold weather, so
# 923 net energy reads ABOVE what NRC-%power x nameplate can express, and
# posting the NRC level would remove real winter capability the smear
# (the anchor itself, cf capped at 1.0) correctly carries. Those months are
# DROPPED from the extract (no rows -> loader NaN -> the smear stands),
# per CLAUDE.md rule 14's misalignment clause: prefer the reconciled measured
# level over a basis known biased low. Months that reconcile within the
# tolerance keep NRC daily timing at the anchor level — every 2023-2025
# Jun-Sep month reconciles to +-0.0000 %.
WEDGE_TOL = 0.01

# NRC unit name -> (EIA plant code, model unit number) for each ISO's fleet.
# Identifier crosswalk (not a tunable): the model's nuclear generators carry
# unit_id "<plant_code>_<unit_no>" from EIA-860 (see
# data.fleet.load_fleet_from_csv); the dormant Crane/TMI-1 unit (EIA 8011) is
# deliberately absent — it does not report to NRC and NUCLEAR_DORMANT_UNTIL
# zeroes it downstream of this overlay.
NRC_TO_EIA: dict[str, dict[str, tuple[int, int]]] = {
    "PJM": {
        "Beaver Valley 1": (6040, 1),
        "Beaver Valley 2": (6040, 2),
        "Braidwood 1": (6022, 1),
        "Braidwood 2": (6022, 2),
        "Byron 1": (6023, 1),
        "Byron 2": (6023, 2),
        "Calvert Cliffs 1": (6011, 1),
        "Calvert Cliffs 2": (6011, 2),
        "D.C. Cook 1": (6000, 1),
        "D.C. Cook 2": (6000, 2),
        "Davis-Besse": (6149, 1),
        "Dresden 2": (869, 2),
        "Dresden 3": (869, 3),
        "Hope Creek 1": (6118, 1),
        "LaSalle 1": (6026, 1),
        "LaSalle 2": (6026, 2),
        "Limerick 1": (6105, 1),
        "Limerick 2": (6105, 2),
        "North Anna 1": (6168, 1),
        "North Anna 2": (6168, 2),
        "Peach Bottom 2": (3166, 2),
        "Peach Bottom 3": (3166, 3),
        "Perry 1": (6020, 1),
        "Quad Cities 1": (880, 1),
        "Quad Cities 2": (880, 2),
        "Salem 1": (2410, 1),
        "Salem 2": (2410, 2),
        "Surry 1": (3806, 1),
        "Surry 2": (3806, 2),
        "Susquehanna 1": (6103, 1),
        "Susquehanna 2": (6103, 2),
    },
}


def fleet_caps(iso: str) -> dict[tuple[int, int], float]:
    """EIA-860 pmax per (plant_code, unit_no) — the capacities the model
    dispatches, used as the monthly-reconciliation weights."""
    import logging

    logging.disable(logging.WARNING)
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    caps: dict[tuple[int, int], float] = {}
    for g in load_fleet_from_csv(iso, get_iso_config(iso), year=YEARS[-1]):
        if g.fuel_type != "nuclear":
            continue
        tail = str(g.unit_id).rsplit("_", 1)[-1]
        if tail.isdigit():
            caps[(int(g.plant_code), int(tail))] = float(g.pmax_mw)
    return caps


def load_daily_raw(iso: str) -> pd.DataFrame:
    """Per (reactor, date) raw daily availability from the NRC reports."""
    xwalk = NRC_TO_EIA[iso]
    frames = []
    for yr in YEARS:
        path = NRC_DIR / f"{yr}PowerStatus.txt"
        if not path.exists():
            raise FileNotFoundError(
                f"{path} missing — run scripts/data/fetch_nrc_reactor_status.py"
            )
        df = pd.read_csv(path, sep="|", encoding="utf-8-sig")
        df["date"] = pd.to_datetime(df["ReportDt"]).dt.normalize()
        df = df[(df.date.dt.year == yr) & df["Unit"].isin(xwalk)]
        frames.append(df[["date", "Unit", "Power"]])
    day = pd.concat(frames, ignore_index=True)
    # One report per reactor-day; keep the last if NRC ever republishes.
    day = day.drop_duplicates(["Unit", "date"], keep="last")
    day["reactor"] = day["Unit"]
    key = day["Unit"].map(xwalk)
    day["plant_code"] = [k[0] for k in key]
    day["unit_no"] = [k[1] for k in key]
    day["avail_raw"] = (day["Power"].astype(float) / 100.0).clip(0.0, 1.0)
    return day[["date", "plant_code", "unit_no", "reactor", "avail_raw"]].sort_values(
        ["plant_code", "unit_no", "date"]
    )


def reconcile_monthly(day: pd.DataFrame, iso: str) -> pd.DataFrame:
    """Scale non-event unit-days so fully-covered months hit the EIA-923 anchor.

    Ported verbatim from ``derive_ercot_nuclear_availability.reconcile_monthly``
    (same frozen constants, same fixed-point construction): event days stay
    exactly as measured; the pool takes one per-month factor (per-day cap 1.0)
    so the fleet-month availability energy reproduces
    ``NUCLEAR_MONTHLY_CF_BY_YEAR[iso]`` exactly. The anchor's fleet pmax
    excludes dormant units (they have no NRC rows here either).
    """
    cf_by_year = NUCLEAR_MONTHLY_CF_BY_YEAR[iso]
    caps = fleet_caps(iso)
    covered_keys = {
        k for k in caps if any((day.plant_code == k[0]) & (day.unit_no == k[1]))
    }
    missing = {
        k
        for k in caps
        if k not in covered_keys and YEARS[-1] >= NUCLEAR_DORMANT_UNTIL.get(k[0], 0)
    }
    if missing:
        print(f"  NOTE: fleet units with no NRC rows (smear stands): {sorted(missing)}")
    fleet_cap = sum(caps[k] for k in covered_keys)
    day = day.assign(avail=day.avail_raw)
    day["capw"] = [caps[(p, u)] for p, u in zip(day.plant_code, day.unit_no)]
    n_units = len(covered_keys)
    for yr in YEARS:
        cf = cf_by_year.get(yr)
        if cf is None:
            continue
        for mo in range(1, 13):
            days_in_month = pd.Period(f"{yr}-{mo:02d}").days_in_month
            sel = (day.date.dt.year == yr) & (day.date.dt.month == mo)
            sub = day[sel]
            covered_dates = sub.date.dt.day.nunique()
            if covered_dates < days_in_month or len(sub) < n_units * days_in_month:
                if len(sub):
                    print(
                        f"  {yr}-{mo:02d}: partial coverage "
                        f"({covered_dates}/{days_in_month} days) — raw kept, "
                        "uncovered dates fall back to the monthly smear"
                    )
                continue
            target = cf[mo - 1] * fleet_cap * days_in_month * 24.0
            capw = sub.capw.to_numpy(float)
            raw = sub.avail_raw.to_numpy(float)
            pool = raw >= EVENT_RAW_MAX
            e_event = float((raw[~pool] * capw[~pool]).sum() * 24.0)
            if not pool.any():
                continue
            e_pool_raw = float((raw[pool] * capw[pool]).sum() * 24.0)
            s = (target - e_event) / e_pool_raw
            if s > 1.0:
                for _ in range(4):
                    posted = np.minimum(1.0, raw[pool] * s)
                    at_cap = posted >= 1.0
                    e_cap = float((capw[pool][at_cap]).sum() * 24.0)
                    e_free_raw = float(
                        (raw[pool][~at_cap] * capw[pool][~at_cap]).sum() * 24.0
                    )
                    if e_free_raw <= 0:
                        break
                    s = max(1.0, (target - e_event - e_cap) / e_free_raw)
            s = float(np.clip(s, 0.0, SCALE_CLIP))
            posted = np.minimum(1.0, raw[pool] * s)
            achieved = e_event + float((posted * capw[pool]).sum() * 24.0)
            print(
                f"  {yr}-{mo:02d}: pool scale {s:.3f}, month energy "
                f"{achieved / target - 1:+.4%} vs anchor"
            )
            if abs(achieved / target - 1) > WEDGE_TOL:
                print(
                    f"  {yr}-{mo:02d}: OFF-ANCHOR {achieved / target - 1:+.2%} "
                    "(event days bind — winter thermal-vs-net wedge): month "
                    "DROPPED, smear stands"
                )
                day.loc[sel, "avail"] = np.nan
                continue
            vals = day.loc[sel, "avail_raw"].to_numpy(float).copy()
            vals[pool] = posted
            day.loc[sel, "avail"] = vals
    dropped = day["avail"].isna()
    if dropped.any():
        day = day[~dropped]
    return day.drop(columns=["capw"])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", default="PJM", choices=sorted(NRC_TO_EIA))
    ap.add_argument(
        "--check",
        action="store_true",
        help="verify the committed CSV reproduces from the raw NRC files",
    )
    args = ap.parse_args()
    out_csv = REPO / "data" / "raw" / f"nuclear-availability-{args.iso}.csv"

    day = load_daily_raw(args.iso)
    day = reconcile_monthly(day, args.iso)
    day["date"] = day["date"].dt.strftime("%Y-%m-%d")
    day["avail_raw"] = day["avail_raw"].round(4)
    day["avail"] = day["avail"].round(4)
    day = day[["date", "plant_code", "unit_no", "reactor", "avail_raw", "avail"]]

    if args.check:
        committed = pd.read_csv(out_csv, dtype=str)
        fresh = day.astype(str).reset_index(drop=True)
        if committed.reset_index(drop=True).equals(fresh):
            print(f"OK: {out_csv.name} reproduces byte-for-byte")
            return 0
        print(f"MISMATCH: {out_csv.name} does not reproduce")
        return 1

    day.to_csv(out_csv, index=False)
    print(f"wrote {out_csv} ({len(day):,} rows, {day.reactor.nunique()} reactors)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
