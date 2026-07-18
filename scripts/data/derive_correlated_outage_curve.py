#!/usr/bin/env python
"""Derive the ERCOT correlated cold-event forced-outage curve (FF-1B Stage 1).

Fits the per-class temperature -> excess-forced-outage hinge curves consumed by
``market_sim.data.outages.apply_correlated_outage_derate`` (the forecast/
hindcast correlated forced-outage availability derate,
``ScenarioConfig.correlated_forced_outage``) and frozen into
``market_sim.config.constants.CORRELATED_OUTAGE_CURVE``. Design charter:
``docs/handoffs/ercot-retirement-composition-2026-07-16.md`` Part D.

Identification (measured-admissible, CLAUDE.md rule 13)
-------------------------------------------------------
Cold-event unavailability is measured from the CAMPD unit-level hourly gross
load (``data/raw/campd-unit-level/TX_<year>.parquet``) against the ERCOT CAMPD
bin-sheet class capacities, on *certified scarcity event days* only:

* **Event window**: a maximal run of consecutive days (gaps <= 2 d) whose
  system daily MIN temperature — the plain mean of ``tmin_c`` across the six
  ERCOT weather zones (``data/raw/ercot-weather/ercot_zone_temp_daily*.csv``,
  NOAA) — is at or below the hinge onset ``T0_C`` (-7 degC ~ 20 degF, the NERC
  cold-weather onset of sharply-rising generator outages; the same anchor as
  ``ScenarioConfig.neiso_gas_derate_t0_c``).
* **In-merit certificate**: the window must contain a day whose daily-max
  EIA-930 ERCO NET load (demand - wind - solar, the exogenous instrument of
  ``scripts/lib/outage_detect.py``) reaches the year's 99th percentile. Under
  that certificate every thermal class is unambiguously called, so capacity
  that never runs is *unavailable*, not out of merit. Certification extends to
  the whole window (+1 recovery day) because measured demand mid-event is
  firm-load-shed-suppressed (Uri: EIA-930 demand collapses Feb 15-18 while
  Feb 14 sets the record) — the tightness that certifies day 1 does not end
  when the shed begins.
* **Instrument**: per class per event day, the class's *best-mustered hour* —
  ``max_h sum_p gross(p, h) / sum_p capacity(p)`` over the day — measured at
  the window's coldest (TMIN-min) day so the muster response aligns with the
  temperature driver (a front that arrives in the evening chills the calendar
  day's TMIN while the fleet response lands next morning: Elliott Dec-22 vs
  Dec-23). CHP classes are EXCLUDED (host-loaded; gross output cannot certify
  grid availability), as is nuclear (no CAMPD trace; the STP-1 Uri trip is a
  documented under-coverage, not modeled here).
* **Excess** over the class's normal forced-outage rate:
  ``excess = clip((1 - EFORD[class]) - bestfrac, 0, 1)`` with ``EFORD`` the
  NERC-GADS class EFORd already in ``constants.EFORD`` — the same baseline the
  statistical WEFOR availability model is built on, so the excess is by
  construction the *event increment on top of* the model's existing forced-
  outage representation (charter D.3/D.6 in-fleet double-count guard).

Curve form and era split
------------------------
Per class and era, a saturating hinge on the system daily TMIN:

    excess(T) = clip(slope_per_c * (T0_C - T), 0, cap)

* ``slope_per_c``: through-origin least squares on the certified window
  points (one point per window: the coldest day's excess vs its TMIN depth).
* ``cap``: the era's maximum observed event excess (the demonstrated
  saturation depth — Uri for the pre era; Elliott for the post era).
* **Eras**: ``pre`` (windows before 2021-12-01) vs ``post`` — the PUCT
  weatherization rule (16 TAC 25.55, adopted Oct-2021, phase-1 compliance
  winter 2021-22) is the physical break: the post-Uri weatherized fleet
  demonstrates roughly half the pre-era saturation depth. This is the
  forward-responsiveness lever the charter requires (a winterized fleet
  shrinks the derate; ``ScenarioConfig.correlated_outage_winterized_year``
  selects the era from the weather-driver year).

Also derives, per era/class, the **winter event share** — the climatological
Dec-Feb mean of the curve applied to the era's own winters' TMIN record —
which the runtime derate ADDS BACK to winter availability before subtracting
the weather-year excess series, so the correlated model *relocates* the
cold-event share already embedded in the flat GADS-based WEFOR instead of
stacking on it (charter D.3 baseline coordination; in an average winter the
two cancel in the mean, in a Uri winter the realized excess dominates).

Admissibility (rule 13): every input regenerates for a forward year from
forward drivers — a weather-year TMIN sample, the NERC-GADS EFORd, and the
fleet winterization state — and responds to changed conditions (colder sample
-> deeper derate; post-weatherization era -> shallower curve). No price, LMP,
or model-residual input anywhere; the curve re-derives only when its source
data (CAMPD extracts, weather archive, EIA-930) updates (rule 23). External
validation anchor: the FERC/NERC Feb-2021 Cold Weather Report (ERCOT lost
~half its expected-available fleet at the Uri peak) — the capacity-weighted
Feb-16 measurement here reproduces ~44% thermal-wide.

Usage::

    python scripts/data/derive_correlated_outage_curve.py

Prints the fitted curve table (the ``CORRELATED_OUTAGE_CURVE`` constants
block), the per-day measurement record, and the validation residuals.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from market_sim.config.constants import EFORD  # noqa: E402

# Hinge onset (deg C): NERC cold-weather analyses place the onset of sharply
# rising generator forced outages near 20 degF (~ -7 degC) — the same anchor as
# ScenarioConfig.neiso_gas_derate_t0_c / correlated_outage_t0_c.
T0_C: float = -7.0

# Era boundary: PUCT weatherization rule 16 TAC 25.55 (adopted Oct-2021),
# phase-1 compliance winter 2021-22. Windows before this date exercise the
# pre-Uri unweatherized fleet.
WINTERIZED_DATE = pd.Timestamp("2021-12-01")

# Model class -> NERC-GADS EFORd key (constants.EFORD). CHP classes and
# nuclear are deliberately absent — see the module docstring.
CLASS_EFORD_KEY: dict[str, str] = {
    "COAL": "coal",
    "CC_REGULAR": "gas_cc",
    "CT_PEAKER": "gas_ct",
    "ST_GAS": "gas_st",
}

# In-merit certificate: the event window must contain a day whose daily-max
# EIA-930 ERCO net load reaches this annual percentile.
CERT_NET_LOAD_PCTL: float = 0.99

# Derive window: complete winters on record outside the H1-2026 quarantine.
FIRST_YEAR, LAST_YEAR = 2018, 2025

# Winter (flat-WEFOR season) months for the event-share climatology.
WINTER_MONTHS: tuple[int, ...] = (12, 1, 2)


def system_daily_tmin() -> pd.Series:
    """System daily TMIN: plain mean of tmin_c across the six weather zones."""
    frames = [
        pd.read_csv(p)
        for p in sorted(
            glob.glob(str(_ROOT / "data/raw/ercot-weather/ercot_zone_temp_daily*.csv"))
        )
    ]
    wx = pd.concat(frames, ignore_index=True)
    wx["date"] = pd.to_datetime(wx["date"])
    return wx.groupby("date")["tmin_c"].mean().sort_index()


def certified_days() -> pd.Series:
    """Bool per day: daily-max EIA-930 ERCO net load >= its year's p99."""
    e = pd.read_parquet(_ROOT / "data/raw/eia-930-hourly/ERCO hourly.parquet")
    e["date"] = pd.to_datetime(e["Local date"])
    dem = e["Adjusted demand"] if "Adjusted demand" in e else e["Demand"]
    wnd = e.get("Adjusted WND Gen", e.get("NG: WND")).fillna(0)
    sun = e.get("Adjusted SUN Gen", e.get("NG: SUN")).fillna(0)
    e["net"] = (
        pd.to_numeric(dem, errors="coerce")
        - pd.to_numeric(wnd, errors="coerce")
        - pd.to_numeric(sun, errors="coerce")
    )
    dmax = e.groupby("date")["net"].max()
    p = e.groupby(e["date"].dt.year)["net"].quantile(CERT_NET_LOAD_PCTL)
    return dmax >= dmax.index.year.map(p)


def class_capacity() -> tuple[pd.Series, pd.Series]:
    """(class capacity MW, plant -> class) from the ERCOT CAMPD bin sheet."""
    bins = pd.read_csv(_ROOT / "data/raw/reference/custom-bin-assignments.csv")
    cap = (
        bins.groupby(["Plant_Code", "Plant_Group"])["Nameplate_MW"].sum().reset_index()
    )
    cap["Plant_Code"] = cap["Plant_Code"].astype(int)
    cap = cap[cap["Plant_Group"].isin(CLASS_EFORD_KEY)]
    return (
        cap.groupby("Plant_Group")["Nameplate_MW"].sum(),
        cap.set_index("Plant_Code")["Plant_Group"],
    )


def class_day_bestfrac(
    dates: pd.DatetimeIndex, class_cap: pd.Series, plant2grp: pd.Series
) -> dict[tuple[str, pd.Timestamp], float]:
    """Per (class, day): the class's best-mustered hour fraction of capacity."""
    out: dict[tuple[str, pd.Timestamp], float] = {}
    for y in sorted({d.year for d in dates}):
        u = pd.read_parquet(
            _ROOT / f"data/raw/campd-unit-level/TX_{y}.parquet",
            columns=["facilityId", "date", "hour", "grossLoad"],
        )
        u["date"] = pd.to_datetime(u["date"])
        u = u[u["date"].isin(dates)]
        u["facilityId"] = pd.to_numeric(u["facilityId"], errors="coerce")
        u["grossLoad"] = pd.to_numeric(u["grossLoad"], errors="coerce").fillna(0.0)
        u["grp"] = u["facilityId"].map(plant2grp)
        u = u.dropna(subset=["grp"])
        hr = u.groupby(["grp", "date", "hour"])["grossLoad"].sum().reset_index()
        hr["frac"] = hr["grossLoad"] / hr["grp"].map(class_cap)
        for (g, d), sub in hr.groupby(["grp", "date"]):
            out[(str(g), pd.Timestamp(d))] = float(sub["frac"].max())
    return out


def cold_windows(tmin_sys: pd.Series) -> list[list[pd.Timestamp]]:
    """Maximal runs of days (gaps <= 2 d) with system TMIN <= T0_C."""
    cold = tmin_sys[
        (tmin_sys <= T0_C)
        & (tmin_sys.index >= f"{FIRST_YEAR}-01-01")
        & (tmin_sys.index < f"{LAST_YEAR + 1}-01-01")
    ]
    days = cold.index.sort_values()
    if len(days) == 0:
        return []
    windows: list[list[pd.Timestamp]] = []
    cur = [days[0]]
    for d in days[1:]:
        if (d - cur[-1]).days <= 2:
            cur.append(d)
        else:
            windows.append(cur)
            cur = [d]
    windows.append(cur)
    return windows


def main() -> int:
    tmin_sys = system_daily_tmin()
    cert = certified_days()
    class_cap, plant2grp = class_capacity()

    # One fit point per certified window per class: the coldest day's excess.
    pts: dict[tuple[str, str], list[tuple[float, float, str]]] = {}
    record: list[str] = []
    for w in cold_windows(tmin_sys):
        wdays = pd.DatetimeIndex(w)
        extended = wdays.append(pd.DatetimeIndex([w[-1] + pd.Timedelta(days=1)]))
        certified = bool(cert.reindex(extended).fillna(False).any())
        era = "pre" if w[0] < WINTERIZED_DATE else "post"
        record.append(
            f"window {w[0].date()}..{w[-1].date()} era={era} "
            f"tmin_min={float(tmin_sys[wdays].min()):.1f} cert={certified}"
        )
        if not certified:
            continue
        coldest = wdays[np.argmin(tmin_sys[wdays].to_numpy())]
        bf = class_day_bestfrac(extended, class_cap, plant2grp)
        for g, key in CLASS_EFORD_KEY.items():
            frac = bf.get((g, coldest))
            if frac is None:
                continue
            excess = float(np.clip((1.0 - EFORD[key]) - min(1.0, frac), 0.0, 1.0))
            t = float(tmin_sys[coldest])
            pts.setdefault((era, g), []).append((t, excess, str(coldest.date())))
            record.append(
                f"   {coldest.date()} {g:11s} tmin={t:6.1f} "
                f"best={frac:.3f} excess={excess:.3f}"
            )

    print("\n".join(record))
    print()

    # Hinge fit per era/class + the winter event-share climatology.
    curve: dict[str, dict[str, dict[str, float]]] = {}
    for era in ("pre", "post"):
        curve[era] = {}
        era_lo = FIRST_YEAR if era == "pre" else WINTERIZED_DATE.year
        era_hi = WINTERIZED_DATE.year if era == "pre" else LAST_YEAR + 1
        in_era = (
            (tmin_sys.index < WINTERIZED_DATE)
            if era == "pre"
            else (tmin_sys.index >= WINTERIZED_DATE)
        )
        winter = tmin_sys[
            in_era
            & tmin_sys.index.month.isin(WINTER_MONTHS)
            & (tmin_sys.index >= f"{FIRST_YEAR}-01-01")
            & (tmin_sys.index < f"{LAST_YEAR + 1}-01-01")
        ]
        for g in CLASS_EFORD_KEY:
            p = pts.get((era, g), [])
            if not p:
                continue
            x = np.array([T0_C - t for t, _, _ in p])
            yv = np.array([e for _, e, _ in p])
            slope = float((x * yv).sum() / (x * x).sum())
            cap = float(yv.max())
            # Winter event share: climatological Dec-Feb mean of the fitted
            # curve over the era's own winter TMIN record.
            excess_clim = np.clip(slope * (T0_C - winter.to_numpy()), 0.0, cap)
            share = float(excess_clim.mean()) if len(winter) else 0.0
            resid = yv - np.clip(slope * x, 0.0, cap)
            curve[era][g] = {
                "slope_per_c": round(slope, 4),
                "cap": round(cap, 3),
                "winter_event_share": round(share, 4),
            }
            print(
                f"{era:4s} {g:11s} slope={slope:.4f} cap={cap:.3f} "
                f"share={share:.4f} n_windows={len(p)} "
                f"resid_max={np.abs(resid).max():.3f} "
                f"anchors={[d for _, _, d in p]} (era winters {era_lo}-{era_hi})"
            )

    print("\nCORRELATED_OUTAGE_CURVE constants block:")
    print(repr(curve))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
