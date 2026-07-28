"""Derive an ISO's OWN ambient capability-derate slope and onset from CAMPD conduct.

The measured-conduct basis for the hour-grain leg of the temperature-dependent
capacity derate (``ScenarioConfig.temp_dependent_derate`` +
``temp_derate_hourly_grain``).  The committed per-class slopes
(``temp_derate_slope_cc`` 0.0076/C, ``temp_derate_slope_ct`` 0.0126/C,
``temp_derate_slope_st_gas`` 0.0054/C) are literature values, and **pjm-95
refuted them on PJM's own CAMPD** — so under rule 25 ``[R-ISO-SCOPE]`` they do
not transfer, and any ISO arming the leg must identify its own pair first.
This script is that identification.

Why the response is identifiable at all
---------------------------------------
A cogen pinned at/near its capability (a refinery CC running flat-out against a
continuous-process host) has no dispatch freedom, so its metered output IS its
hourly capability.  What remains in its hour-of-day profile is the physical
ambient response — for a gas turbine the air-density / mass-flow effect, which
is the dominant term at any GT-based plant.

Estimator (WITHIN-DAY, the clean identification)
------------------------------------------------
Day-level confounders — outages, host steam demand, fuel switches, planned
derates, seasonal maintenance — move a plant's LEVEL, not its shape within the
day.  So the slope is estimated on within-day deviations only::

    y = log(P_h) - mean_d(log P)        # fractional deviation from the day's mean
    x = T_h     - mean_d(T)             # deg C deviation from the day's mean
    slope = -OLS(y ~ x)                 # fractional capability LOSS per deg C

Regressing in logs makes the OLS coefficient directly a *fractional* response,
so units of different size pool without a capacity normalization, and any
day-level multiplicative confounder drops out with the day mean.  ``T`` is the
hour-grain dry-bulb reconstruction the model itself consumes
(``data.eia930.weather.iso_zone_hourly_drybulb``) — the SAME function, imported,
so the derivation and the LP can never drift apart.

Onset
-----
The committed curve is a hinge, ``1 - slope * max(0, T - ref)``, which asserts
NO response below ``ref`` (15 C).  That functional form is right for a
condenser-limited steam plant and WRONG for a gas turbine, whose output varies
continuously through its ISO rating point (it GAINS below 15 C).  Rather than
assume either, the onset is measured non-parametrically: the within-day slope is
re-estimated inside bins of the day's mean temperature.  A hinge at ``ref`` shows
up as a slope that collapses to ~0 in the bins below it; a slope that is flat
across cold and warm bins alike says the response is linear over the observed
range and there is NO onset (report ``ref = None``).

Cross-checks reported, never fitted
-----------------------------------
* **Phase.** The within-day estimate depends on the assumed diurnal shape, so
  the script re-runs it against shifted copies of the proxy and reports which
  lag maximizes the fit.  This VALIDATES the climatological anchors
  (``constants.DIURNAL_TMIN_HOUR`` / ``DIURNAL_TMAX_HOUR``); it never feeds them.
* **Seasonal slope.** The between-day regression (day-mean output on day-mean
  temperature) is reported for comparison.  It is NOT used: it is contaminated
  by exactly the seasonal confounders the within-day estimator removes.
* **Shape sensitivity.** The slope is re-estimated against a triangular bridge
  instead of the cosine one, to size the functional-form dependence.

Scope: units at plants whose ISO model fleet assigns them to one of
``--classes`` (default the cogen pair ``ST_CHP,CT_CHP``).  A plant carrying a
COAL fleet row is DROPPED: its CEMS meter is the coal boiler, so its hourly
record identifies a different machine than the class being derived.

Output: ``data/raw/_processed-legacy/campd_temp_derate_params_{ISO}.csv``
(pooled class rows plus per-plant detail).

Governance (CLAUDE.md rules 13 ``[R-MEASURED]`` / 23 ``[R-FROZEN-DERIVE]`` / 25
``[R-ISO-SCOPE]``): the slope is a unit-conduct property measured against an
exogenous physical driver.  Rule-13 admissibility — the same regression would be
produced for a forward year from forward weather, and the response moves when
conditions move (a hotter year derates more).  It is not a measured OUTCOME fed
back to close a residual: the estimator never sees a price, a benchmark, or a
model output.  Re-derive ONLY when the CAMPD or weather source data updates,
never because a residual moved.

Usage::

    python scripts/data/derive_campd_temp_derate_params.py --iso MISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.data.eia930.weather import (  # noqa: E402
    diurnal_drybulb_from_daily,
    iso_zone_tmax,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

#: Default model classes to derive: the cogen pair.  Both are tranches of the
#: same physical cogen facilities, and the CEMS meter is the facility — so the
#: metered response identifies the pair jointly, not either alone.
DEFAULT_CLASSES: tuple[str, ...] = ("ST_CHP", "CT_CHP")

#: A plant with any fleet row in one of these classes is dropped: its CEMS
#: units are a different machine than the cogen tranche being derived (e.g.
#: MISO's R S Nelson, whose only CEMS unit is a tangentially-fired coal boiler
#: while its ST_CHP slice is an EIA-923 monthly split off that same meter).
CONTAMINATING_CLASSES: frozenset[str] = frozenset({"COAL"})

#: Online detection, matching the ``derive_campd_gas_commitment_params`` /
#: ``derive_cc_committed_pct`` convention: a unit counts as online when it is
#: above both an absolute floor and a fraction of its own sustained maximum, so
#: brief start/stop ramp transients do not enter the loading distribution.
_ONLINE_FRAC: float = 0.20
_HSL_PCTILE: float = 99.5

#: A plant must clear these to be identified at all — below them the regression
#: is noise, not conduct.
_MIN_ANNUAL_MWH: float = 10_000.0
_MIN_ONLINE_HOURS: int = 2_000

#: Day-mean-temperature bin edges (deg C) for the non-parametric onset scan.
_ONSET_BINS: tuple[float, ...] = (-30.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 40.0)

#: A bin needs this many days before its slope is reported (else it is noise).
_MIN_BIN_DAYS: int = 30


def _fleet_index(iso: str) -> tuple[dict[int, set[str]], dict[int, str]]:
    """Return ``(plant_code -> fleet classes, plant_code -> model zone)``."""
    groups: dict[int, set[str]] = {}
    zones: dict[int, str] = {}
    for plant in load_fleet_from_csv(iso):
        code = int(plant.plant_code)
        groups.setdefault(code, set()).add(plant.plant_group)
        zones[code] = plant.zone
    return groups, zones


def _target_plants(
    groups: dict[int, set[str]], classes: tuple[str, ...]
) -> tuple[set[int], list[int]]:
    """Split the fleet into derivable target plants and dropped contaminated ones."""
    wanted = set(classes)
    targets: set[int] = set()
    dropped: list[int] = []
    for code, found in groups.items():
        if not (found & wanted):
            continue
        if found & CONTAMINATING_CLASSES:
            dropped.append(code)
        else:
            targets.add(code)
    return targets, sorted(dropped)


def _load_campd(iso: str, years: tuple[int, ...], plants: set[int]) -> pd.DataFrame:
    """Load facility-hour gross load for *plants* across *years*.

    Sums the plant's CEMS units to the facility meter — the object that pairs
    with the model's per-plant tranches — on the CAMPD Local Standard Time
    clock the rest of the repo indexes hourly conduct on.
    """
    frames: list[pd.DataFrame] = []
    for year in years:
        for state in states_for_iso(iso):
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=["facilityId", "facilityName", "date", "hour", "grossLoad"],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            df = df[df["facilityId"].isin(plants)]
            if df.empty:
                continue
            df["year"] = year
            frames.append(df)
    if not frames:
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    raw["facilityId"] = raw["facilityId"].astype(int)
    raw["grossLoad"] = pd.to_numeric(raw["grossLoad"], errors="coerce").fillna(0.0)
    fac = raw.groupby(["facilityId", "year", "date", "hour"], as_index=False).agg(
        gross_mw=("grossLoad", "sum"), name=("facilityName", "first")
    )
    fac["date"] = pd.to_datetime(fac["date"])
    return fac


def _zone_temperature(
    iso: str, year: int, zone: str, triangular: bool = False
) -> pd.DataFrame | None:
    """Return an hour-grain dry-bulb frame ``(date, hour, temp_c)`` for a zone-year.

    Uses the model's own reconstruction (:func:`diurnal_drybulb_from_daily`), or
    a triangular bridge over the same daily extremes when *triangular* — the
    functional-form sensitivity leg.
    """
    hours = 8760
    pair = iso_zone_tmax(iso, year, hours, zone=zone)
    if pair is None or pair[0] is None or pair[1] is None:
        return None
    tmax, tmin = pair
    if triangular:
        from market_sim.config.constants import DIURNAL_TMAX_HOUR, DIURNAL_TMIN_HOUR

        clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
        hod = clock.hour.to_numpy()
        h_min, h_max = int(DIURNAL_TMIN_HOUR), int(DIURNAL_TMAX_HOUR)
        rise = np.clip((hod - h_min) / (h_max - h_min), 0.0, 1.0)
        fall = np.clip((hod - h_max) / (24 - h_max + h_min), 0.0, 1.0)
        temp = np.where(
            hod <= h_max, tmin + (tmax - tmin) * rise, tmax - (tmax - tmin) * fall
        )
    else:
        temp = diurnal_drybulb_from_daily(tmin, tmax, year, hours)

    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return pd.DataFrame({"date": clock.normalize(), "hour": clock.hour, "temp_c": temp})


#: The within-day panel key. Demeaning must be PER PLANT-DAY, never per date:
#: pooling several plants under one date mean leaks cross-plant level and
#: cross-zone temperature differences into both regressors, which biases the
#: pooled slope far outside the range of any individual plant's.
_DAY_KEY: tuple[str, ...] = ("facilityId", "year", "date")


def _within_day_slope(frame: pd.DataFrame) -> tuple[float, float, int]:
    """Return ``(slope, r, n_hours)`` of the within-day log-output/temperature fit.

    ``slope`` is the fractional capability LOSS per deg C (positive = output
    falls as ambient rises).  Both series are demeaned WITHIN each PLANT-day
    (:data:`_DAY_KEY`), so every day-level and plant-level confounder is
    differenced away and the pooled estimate is a true fixed-effects fit.
    """
    work = frame.copy()
    work["logp"] = np.log(work["gross_mw"])
    key = [c for c in _DAY_KEY if c in work.columns]
    grp = work.groupby(key)
    work["y"] = work["logp"] - grp["logp"].transform("mean")
    work["x"] = work["temp_c"] - grp["temp_c"].transform("mean")
    # Days with no temperature spread carry no identification.
    work = work[grp["temp_c"].transform("std") > 0.1]
    if len(work) < 100:
        return float("nan"), float("nan"), len(work)
    x = work["x"].to_numpy()
    y = work["y"].to_numpy()
    slope = float(np.polyfit(x, y, 1)[0])
    r = float(np.corrcoef(x, y)[0, 1])
    return -slope, r, len(work)


def _loading_ratio(frame: pd.DataFrame) -> float:
    """Return the plant's median online loading as a fraction of its own HSL.

    The capability-limitation screen.  An ambient derate is only OBSERVABLE at a
    plant that runs against its ceiling: there, the meter is the capability.  A
    plant with headroom is dispatch- or host-limited, and its meter measures
    what its offtaker asked for, not what the machine could make.
    """
    hsl = float(np.percentile(frame["gross_mw"], _HSL_PCTILE))
    if hsl <= 0.0:
        return 0.0
    return float(np.median(frame["gross_mw"]) / hsl)


def _onset_scan(frame: pd.DataFrame) -> list[dict]:
    """Re-estimate the within-day slope inside day-mean-temperature bins."""
    work = frame.copy()
    key = [c for c in _DAY_KEY if c in work.columns]
    day_mean = work.groupby(key)["temp_c"].transform("mean")
    work["bin"] = pd.cut(day_mean, bins=list(_ONSET_BINS))
    rows: list[dict] = []
    for label, part in work.groupby("bin", observed=True):
        n_days = part.groupby(key).ngroups
        if n_days < _MIN_BIN_DAYS:
            continue
        slope, r, n = _within_day_slope(part)
        rows.append(
            {
                "bin_lo_c": float(label.left),
                "bin_hi_c": float(label.right),
                "n_days": int(n_days),
                "slope_per_c": slope,
                "r": r,
            }
        )
    return rows


def _phase_scan(frame: pd.DataFrame) -> list[dict]:
    """Re-fit against hour-shifted copies of the proxy; report the best lag.

    The shift is applied WITHIN each plant-year, in time order, so no lag ever
    wraps one plant's temperature onto another's output.
    """
    work = frame.sort_values(["facilityId", "year", "date", "hour"]).copy()
    keys = ["facilityId", "year"]
    rows: list[dict] = []
    for lag in range(-6, 7):
        shifted = work.copy()
        shifted["temp_c"] = shifted.groupby(keys)["temp_c"].transform(
            lambda s, _lag=lag: pd.Series(np.roll(s.to_numpy(), _lag), index=s.index)
        )
        slope, r, _ = _within_day_slope(shifted)
        rows.append({"lag_h": lag, "slope_per_c": slope, "r": r})
    return rows


def _seasonal_slope(frame: pd.DataFrame) -> tuple[float, float]:
    """Between-day regression of day-mean log output on day-mean temperature."""
    daily = frame.groupby(["year", "date"]).agg(
        logp=("gross_mw", lambda s: float(np.log(s).mean())),
        temp=("temp_c", "mean"),
    )
    if len(daily) < 30:
        return float("nan"), float("nan")
    x = daily["temp"].to_numpy()
    y = daily["logp"].to_numpy()
    return -float(np.polyfit(x, y, 1)[0]), float(np.corrcoef(x, y)[0, 1])


def derive(iso: str, years: tuple[int, ...], classes: tuple[str, ...]) -> dict:
    """Run the full derivation for *iso* and return the result payload."""
    groups, zones = _fleet_index(iso)
    targets, dropped = _target_plants(groups, classes)
    print(f"{iso}: {len(targets)} candidate plant(s) in {'/'.join(classes)}")
    for code in dropped:
        print(
            f"  DROPPED {code}: carries a {sorted(groups[code] & CONTAMINATING_CLASSES)} "
            "fleet row — its CEMS meter is a different machine"
        )

    fac = _load_campd(iso, years, targets)
    if fac.empty:
        raise SystemExit(f"{iso}: no CAMPD hourly rows for any target plant")

    # Attach the hour-grain temperature of each plant's model zone.
    parts: list[pd.DataFrame] = []
    tri_parts: list[pd.DataFrame] = []
    for (code, year), part in fac.groupby(["facilityId", "year"]):
        zone = zones.get(int(code))
        if zone is None:
            continue
        for triangular, sink in ((False, parts), (True, tri_parts)):
            temp = _zone_temperature(iso, int(year), zone, triangular=triangular)
            if temp is None:
                continue
            merged = part.merge(temp, on=["date", "hour"], how="inner")
            merged["zone"] = zone
            sink.append(merged)
    if not parts:
        raise SystemExit(f"{iso}: no weather coverage for any target plant's zone")

    panel = pd.concat(parts, ignore_index=True)
    tri_panel = pd.concat(tri_parts, ignore_index=True) if tri_parts else pd.DataFrame()

    detail: list[dict] = []
    kept: list[pd.DataFrame] = []
    for code, part in panel.groupby("facilityId"):
        name = str(part["name"].iloc[0])
        annual = float(part["gross_mw"].sum()) / max(1, len(years))
        hsl = float(np.percentile(part["gross_mw"], _HSL_PCTILE))
        online = part[part["gross_mw"] >= max(_ONLINE_MW, _ONLINE_FRAC * hsl)]
        if annual < _MIN_ANNUAL_MWH or len(online) < _MIN_ONLINE_HOURS:
            print(
                f"  skip {code} {name}: {annual / 1e3:.1f} GWh/yr, "
                f"{len(online)} online h (below identification floor)"
            )
            continue
        slope, r, n = _within_day_slope(online)
        seas_slope, seas_r = _seasonal_slope(online)
        detail.append(
            {
                "plant_code": int(code),
                "plant_name": name,
                "zone": str(part["zone"].iloc[0]),
                "annual_gwh": annual / 1e3,
                "hsl_mw": hsl,
                "loading_ratio": _loading_ratio(online),
                "online_hours": int(len(online)),
                "within_day_slope_per_c": slope,
                "within_day_r": r,
                "within_day_n": int(n),
                "seasonal_slope_per_c": seas_slope,
                "seasonal_r": seas_r,
            }
        )
        kept.append(online)

    if not kept:
        raise SystemExit(f"{iso}: no plant cleared the identification floor")

    pooled = pd.concat(kept, ignore_index=True)
    p_slope, p_r, p_n = _within_day_slope(pooled)
    s_slope, s_r = _seasonal_slope(pooled)

    # The CLASS parameter: the capacity-weighted p50 of the per-plant slopes.
    # Same population statistic ``derive_campd_gas_commitment_params`` uses for
    # min_load_frac, and the reason it is a median rather than a mean: a class
    # of a handful of cogens must not be set by whichever single plant swings
    # furthest. No plant is screened out — see the module docstring on why the
    # "pin the identification to the most capability-limited plant" screen is
    # NOT applied (MISO's most-pinned cogens show the SMALLEST response, which
    # refutes the dispatch-contamination premise that would justify it).
    det = pd.DataFrame(detail).sort_values("within_day_slope_per_c")
    w = det["hsl_mw"].to_numpy(dtype=float)
    cum = np.cumsum(w)
    idx = int(np.searchsorted(cum, 0.5 * cum[-1]))
    class_slope = float(
        det["within_day_slope_per_c"].to_numpy()[min(idx, len(det) - 1)]
    )
    energy_w = float(
        np.average(
            det["within_day_slope_per_c"].to_numpy(dtype=float),
            weights=det["annual_gwh"].to_numpy(dtype=float),
        )
    )

    tri_slope = float("nan")
    if not tri_panel.empty:
        codes = {d["plant_code"] for d in detail}
        tri_keep = tri_panel[tri_panel["facilityId"].isin(codes)]
        tri_hsl = float(np.percentile(tri_keep["gross_mw"], _HSL_PCTILE))
        tri_keep = tri_keep[
            tri_keep["gross_mw"] >= max(_ONLINE_MW, _ONLINE_FRAC * tri_hsl)
        ]
        tri_slope, _, _ = _within_day_slope(tri_keep)

    # Onset scan on the single largest identified plant as well as the class:
    # the class scan pools a heterogeneous fleet, so a hinge visible at the
    # dominant plant would otherwise be averaged away.
    top = max(detail, key=lambda d: d["annual_gwh"])
    top_frame = pooled[pooled["facilityId"] == top["plant_code"]]

    return {
        "detail": detail,
        "class_slope_per_c": class_slope,
        "energy_weighted_slope_per_c": energy_w,
        "pooled": {
            "slope_per_c": p_slope,
            "r": p_r,
            "n_hours": p_n,
            "seasonal_slope_per_c": s_slope,
            "seasonal_r": s_r,
            "triangular_slope_per_c": tri_slope,
        },
        "onset": _onset_scan(pooled),
        "onset_top": _onset_scan(top_frame),
        "top_plant": top,
        "phase": _phase_scan(pooled),
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--classes",
        default=",".join(DEFAULT_CLASSES),
        help="comma-separated model classes to derive",
    )
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    iso = args.iso.upper()
    classes = tuple(c.strip() for c in args.classes.split(",") if c.strip())
    result = derive(iso, tuple(args.years), classes)

    detail = pd.DataFrame(result["detail"])
    print("\n=== per-plant identification ===")
    print(detail.to_string(index=False))

    pooled = result["pooled"]
    print("\n=== pooled within-day identification ===")
    print(
        f"  slope        {pooled['slope_per_c']:.5f} /degC   "
        f"(r={pooled['r']:+.3f}, n={pooled['n_hours']} h)"
    )
    print(
        f"  triangular   {pooled['triangular_slope_per_c']:.5f} /degC  (form sensitivity)"
    )
    print(
        f"  seasonal     {pooled['seasonal_slope_per_c']:.5f} /degC  "
        f"(r={pooled['seasonal_r']:+.3f}) — cross-check only, NOT used"
    )

    print("\n=== CLASS PARAMETER ===")
    print(
        f"  capacity-weighted p50 slope   {result['class_slope_per_c']:.5f} /degC"
        "   <-- the derived class value"
    )
    print(
        f"  energy-weighted mean slope    {result['energy_weighted_slope_per_c']:.5f}"
        " /degC   (context only)"
    )

    print("\n=== onset scan (within-day slope by day-mean temperature bin) ===")
    onset = pd.DataFrame(result["onset"])
    print(onset.to_string(index=False))
    top = result["top_plant"]
    print(f"\n--- same scan, largest identified plant ({top['plant_name']}) ---")
    print(pd.DataFrame(result["onset_top"]).to_string(index=False))

    print("\n=== phase validation (hour-shifted proxy) ===")
    phase = pd.DataFrame(result["phase"])
    best = phase.loc[phase["r"].abs().idxmax()]
    print(phase.to_string(index=False))
    print(
        f"  best lag {int(best['lag_h'])} h (r={best['r']:+.3f}) — 0 confirms the anchors"
    )

    out = args.out or (PROCESSED_DIR / f"campd_temp_derate_params_{iso}.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = detail.assign(scope="plant")
    rows = pd.concat(
        [
            rows,
            pd.DataFrame(
                [
                    {
                        "scope": "pooled",
                        "plant_name": "|".join(classes),
                        "within_day_slope_per_c": pooled["slope_per_c"],
                        "within_day_r": pooled["r"],
                        "within_day_n": pooled["n_hours"],
                        "seasonal_slope_per_c": pooled["seasonal_slope_per_c"],
                        "seasonal_r": pooled["seasonal_r"],
                    },
                    {
                        "scope": "class_parameter",
                        "plant_name": "|".join(classes),
                        "within_day_slope_per_c": result["class_slope_per_c"],
                        "seasonal_slope_per_c": result["energy_weighted_slope_per_c"],
                    },
                ]
            ),
        ],
        ignore_index=True,
    )
    rows.to_csv(out, index=False)
    onset.assign(scope="onset_bin").to_csv(
        out.with_name(out.stem + "_onset.csv"), index=False
    )
    phase.assign(scope="phase_lag").to_csv(
        out.with_name(out.stem + "_phase.csv"), index=False
    )
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
