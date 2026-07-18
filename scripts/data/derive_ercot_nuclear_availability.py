"""Derive ERCOT per-reactor DAILY nuclear availability from the 60-Day DAM disclosure.

Measured-input refinement of the ERCOT nuclear refuel representation
(CLAUDE.md rules 14/15): ``NUCLEAR_MONTHLY_CF_BY_YEAR`` carries the measured
EIA-923 fleet monthly energy but smears it uniformly across all four reactors
and every hour of the month, which mis-times the spring/fall refuel windows by
up to ±1.4 GW *within* a month (the May-2024 forensics type case: STP-2 was
physically OUT 2024-03-23 -> 2024-05-19 — spanning the Apr-16, Apr-28 and
May-8 scarcity events — and back for the May-24..27 record-heat days, while
the 0.78 May smear spread that outage over the whole month; see
``docs/DIAGNOSIS-ercot-may2024-outage-forensics-2026-07.md`` §2.1).

This script reconciles the two measured sources at their native grain:

* **Timing (daily, per reactor)** — the ERCOT 60-Day DAM Disclosure
  ``Gen_Resource_Data`` NUC rows (``data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_
  DAM_Gen_Resource_Data_*.parquet``): a reactor-day's raw availability is its
  hour-summed non-OUT HSL over the day divided by 24 x its healthy hourly
  reference (the MEDIAN positive operating day — nuclear runs flat at rating,
  so the median is rated operation), clipped to [0, 1]. A reactor with every
  jack-bus row ``Resource Status == OUT`` all day reads 0.0; DAM-partial days
  (return-to-service ramps) read fractionally.
* **Level (monthly energy)** — the committed EIA-923 anchor
  (``NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"]``): for every month whose days are
  ALL disclosure-covered, EVENT days (raw < :data:`EVENT_RAW_MAX` — refuel
  windows, trips, ramps, deep derates like CP-1's 0.73 late-June-2023
  heat-dome level, cross-validated against the EIA-930 nuclear hourly) stay
  exactly as measured, and the remaining pool is scaled by one per-month
  factor (per-day cap 1.0) so the fleet-month availability energy reproduces
  the anchor exactly — the 0.90-0.99 pool band is dominated by the HSL
  basis's ~1-2 % low-read noise, so the anchor owns the LEVEL while the
  disclosure owns the TIMING. Months with uncovered days are left raw (the
  loader falls back to the monthly smear for uncovered dates, so scaling
  covered days against a whole-month energy target would double-count).

Output: ``data/raw/ercot-nuclear-availability.csv`` with one row per
(reactor, covered delivery date): ``date, plant_code, unit_no, reactor,
avail_raw, avail`` (``avail`` = the reconciled series the model consumes).
Delivery-date coverage is whatever the on-disk disclosure files span
(2023 has an Oct-2 -> Nov-1 hole; 2025 ends Nov-1 until the 2026
publications land); uncovered dates simply have no row.

Admissibility (rule 14): a refuel window is a physical availability event —
the same class as the CAMPD fossil outage windows — produced forward by the
static ``NUCLEAR_MONTHLY_CF`` / refuel-block scheduling, and it responds to
changed conditions. Rule 23: re-run only when new disclosure months land.

Usage::

    python scripts/data/derive_ercot_nuclear_availability.py [--check]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR  # noqa: E402

DISCLOSURE_GLOB = (
    "data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"
)
OUT_CSV = REPO / "data" / "raw" / "ercot-nuclear-availability.csv"

# Disclosure resource -> (EIA plant code, model unit number). The model's four
# EIA-860 nuclear generators are 6145_1/6145_2 (Comanche Peak 1/2, North zone)
# and 6251_1/6251_2 (South Texas Project 1/2, Houston zone).
REACTORS: dict[str, tuple[int, int]] = {
    "CP1": (6145, 1),
    "CP2": (6145, 2),
    "STP1": (6251, 1),
    "STP2": (6251, 2),
}

YEARS = (2023, 2024, 2025)

# A unit-day BELOW this raw fraction is a measured event day (a full/partial
# refuel-window, trip, ramp, or deep derate day — e.g. CP-1's 0.73 late-June
# 2023 heat-dome derate, cross-validated against the EIA-930 nuclear hourly):
# it is kept exactly as measured. Days AT OR ABOVE it form the scalable pool
# the monthly EIA-923 anchor is solved over (per-day cap 1.0) — the 0.90-0.99
# band is dominated by the disclosure HSL basis's ~1-2 % low-read noise
# (Aug-2023 raw ≈ 0.980 vs measured 930 fleet ≈ 0.992 with the anchor at
# 0.99), which at the August scarcity knee is worth several $/MWh of phantom
# tightness, so the anchor — not the noisy HSL read — sets the level there.
EVENT_RAW_MAX = 0.90

# Fleet nameplate weights for the monthly energy reconciliation (EIA-860
# nameplate, the same capacities the model dispatches).
CAP_MW = {"CP1": 1205.0, "CP2": 1195.0, "STP1": 1300.0, "STP2": 1280.0}


def _reactor(resource_name: str) -> str | None:
    """Map a disclosure NUC resource name to its reactor key."""
    if resource_name.startswith("CPSES_UNIT"):
        return "CP" + resource_name[-1]
    if "_STP_G" in resource_name:
        return "STP" + resource_name.split("_G")[1][0]
    return None


def load_daily_raw() -> pd.DataFrame:
    """Return per (reactor, date) raw daily availability from the disclosure.

    ``avail_raw = clip(sum over hours of non-OUT HSL / (24 x median positive
    operating day), 0, 1)`` — 0.0 for a full-OUT day, fractional for
    DAM-partial return-to-service days.
    """
    cols = ["Delivery Date", "Resource Name", "Resource Type", "HSL", "Resource Status"]
    frames = []
    for f in sorted(glob.glob(str(REPO / DISCLOSURE_GLOB))):
        df = pd.read_parquet(f, columns=cols)
        df = df[df["Resource Type"] == "NUC"].copy()
        if df.empty:
            continue
        df["date"] = pd.to_datetime(df["Delivery Date"])
        frames.append(df)
    nuc = pd.concat(frames, ignore_index=True)
    nuc = nuc[
        (nuc.date >= f"{YEARS[0]}-01-01") & (nuc.date <= f"{YEARS[-1]}-12-31")
    ].copy()
    nuc["reactor"] = nuc["Resource Name"].map(_reactor)
    if nuc["reactor"].isna().any():
        bad = sorted(nuc.loc[nuc["reactor"].isna(), "Resource Name"].unique())
        raise ValueError(f"unmapped NUC resource names: {bad}")
    nuc["avail"] = ~nuc["Resource Status"].isin(["OUT"])
    nuc["avail_hsl"] = np.where(nuc["avail"], nuc["HSL"].fillna(0.0), 0.0)
    day = (
        nuc.groupby(["reactor", nuc.date.dt.date], observed=True)["avail_hsl"]
        .sum()
        .rename("hsl_day")
        .reset_index()
        .rename(columns={"level_1": "date"})
    )
    day["date"] = pd.to_datetime(day["date"])
    out = []
    for r, g in day.groupby("reactor"):
        hourly = g.hsl_day / 24.0
        # Healthy reference = MEDIAN of positive operating days, not a high
        # percentile: nuclear runs flat at rating, so the median IS rated
        # operation, and a p98 ref made typical summer days read ~0.96
        # "sub-healthy" (heat-sagged HSL), which the monthly reconciliation
        # then could not lift (scale capped at 1.0) — silently shaving 2-4 %
        # off non-window months. Above-median days clip to 1.0.
        ref = float(np.median(hourly[hourly > 0]))
        g = g.assign(avail_raw=(g.hsl_day / 24.0 / ref).clip(0.0, 1.0))
        out.append(g[["reactor", "date", "avail_raw"]])
    return pd.concat(out, ignore_index=True).sort_values(["reactor", "date"])


def reconcile_monthly(day: pd.DataFrame) -> pd.DataFrame:
    """Scale non-event unit-days so fully-covered months hit the EIA-923 anchor.

    Event days (raw < :data:`EVENT_RAW_MAX` — refuel windows, trips, ramps and
    deep derates) stay exactly as measured. The remaining days form the
    scalable pool: one per-month factor ``s`` (found by a short fixed-point
    iteration because each day individually caps at 1.0) sets their level so
    the fleet-month availability energy reproduces the committed EIA-923
    anchor — the 0.90-0.99 pool values are dominated by the disclosure HSL
    basis's ~1-2 % low-read noise, so the anchor owns the LEVEL while the
    disclosure owns the TIMING.
    """
    cf_by_year = NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"]
    fleet_cap = sum(CAP_MW.values())
    day = day.assign(avail=day.avail_raw)
    for yr in YEARS:
        for mo in range(1, 13):
            days_in_month = pd.Period(f"{yr}-{mo:02d}").days_in_month
            sel = (day.date.dt.year == yr) & (day.date.dt.month == mo)
            sub = day[sel]
            covered_dates = sub.date.dt.day.nunique()
            if covered_dates < days_in_month or len(sub) < 4 * days_in_month:
                if len(sub):
                    print(
                        f"  {yr}-{mo:02d}: partial coverage "
                        f"({covered_dates}/{days_in_month} days) — raw kept, "
                        "uncovered dates fall back to the monthly smear"
                    )
                continue
            cf = cf_by_year.get(yr)
            if cf is None:
                continue
            target = cf[mo - 1] * fleet_cap * days_in_month * 24.0
            capw = sub.reactor.map(CAP_MW).to_numpy(float)
            raw = sub.avail_raw.to_numpy(float)
            pool = raw >= EVENT_RAW_MAX
            e_event = float((raw[~pool] * capw[~pool]).sum() * 24.0)
            if not pool.any():
                continue
            # Fixed-point on s: pool days post at min(1, raw*s); 4 rounds is
            # plenty (each round only re-splits the at-cap set). Solve the
            # UNCAPPED scale first: when it is <= 1 no per-day cap can bind
            # (raw <= 1), so it is exact — including the no-event month
            # (all raw = 1.0, anchor < 1), which must degrade to the uniform
            # smear rather than pin at the cap.
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
            s = float(np.clip(s, 0.0, 1.25))
            posted = np.minimum(1.0, raw[pool] * s)
            achieved = e_event + float((posted * capw[pool]).sum() * 24.0)
            print(
                f"  {yr}-{mo:02d}: pool scale {s:.3f}, month energy "
                f"{achieved / target - 1:+.4%} vs anchor"
            )
            if abs(achieved / target - 1) > 0.01:
                # The measured event days alone exceed / undershoot what the
                # 923 energy allows — flag loudly; never invent availability.
                print(
                    f"  {yr}-{mo:02d}: WARNING month energy off anchor by "
                    f"{achieved / target - 1:+.2%} (event days bind)"
                )
            vals = day.loc[sel, "avail_raw"].to_numpy(float).copy()
            vals[pool] = posted
            day.loc[sel, "avail"] = vals
    return day


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="re-derive and diff against the committed CSV (exit 1 on drift)",
    )
    args = ap.parse_args()

    day = reconcile_monthly(load_daily_raw())
    pc = day.reactor.map(lambda r: REACTORS[r][0])
    un = day.reactor.map(lambda r: REACTORS[r][1])
    out = pd.DataFrame(
        {
            "date": day.date.dt.strftime("%Y-%m-%d"),
            "plant_code": pc,
            "unit_no": un,
            "reactor": day.reactor,
            "avail_raw": day.avail_raw.round(4),
            "avail": day.avail.round(4),
        }
    ).sort_values(["date", "plant_code", "unit_no"])

    for yr in YEARS:
        sub = out[out.date.str.startswith(str(yr))]
        ndays = sub.date.nunique()
        full_out = int((sub.avail <= 0.0).sum())
        print(
            f"{yr}: {ndays} covered dates, {len(sub)} rows, "
            f"{full_out} full-OUT reactor-days"
        )

    if args.check:
        prev = pd.read_csv(OUT_CSV, dtype=str)
        new = out.astype(str).reset_index(drop=True)
        if prev.reset_index(drop=True).equals(new):
            print("check: committed CSV reproduces byte-identically")
            return
        raise SystemExit("check FAILED: derived output drifted from committed CSV")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV} ({len(out)} rows, {OUT_CSV.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
