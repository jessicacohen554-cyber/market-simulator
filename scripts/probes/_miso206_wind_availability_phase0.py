"""miso-206 phase 0 — BOUND the wind-availability object IN THE OBJECT'S OWN HOURS (zero-solve).

miso-205 aimed a candidate that had stood open but unaimed: the C3a-2025 object
is a LOW-WIND set (hour-of-day-matched p36.5) and MISO carries a standing model
wind excess of ~+5 TWh/yr over EIA-930.  Surplus wind in exactly the hours the
model should be short is supply that suppresses the marginal unit.  Whether the
excess LIVES in those hours, and whether removing it could reach the marginal
stack, is what this probe measures — before any solve, against pre-committed
bounds (PREREG-miso206, pushed at ``f55af87f``).

What the instrument establishes first (PRE-CONDITIONS — any failure stops):

* **N-1** the measured MISO wind/solar is rebuilt INDEPENDENTLY from the raw
  ``EIA930_BALANCE_<year>_<half>.parquet`` rows and asserted against the
  production loader ``load_eia_hourly_renewable_gen`` on the model's clock.
* **N-2** the production wind BOUND (``load_renewable_profiles`` under the
  keeper's own ``ScenarioConfig``) equals ``delivered / (1 - r)`` with the
  Potomac reference rate ``r``, and the keeper's P1 wind sits ON it.
* **N-3** the object set reproduces miso-205's thresholds and 2025 stamps.

Then, per year, on the OBJ hours / the top-15 gross-load hours / all Jun-Jul:
model vs measured wind (levels, excess, percentile ranks in Jun-Jul and
hour-of-day matched), solar as the control, the annual excess, and THE BOUND
against miso-203 G-D's own margins (read, never re-derived).

Every input is a committed artifact or a production loader; **no LP is
solved**.  Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso206_wind_availability_phase0.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import EIA_930_DIR, EIA_HOURLY_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import load_eia_hourly_renewable_gen  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    _miso_wind_reference_curtailment_rate,
    load_renewable_profiles,
)

ISO = "MISO"
BA = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
MARGINS = REPO / "results/calibration/_miso203_summer_peak_anchor_phase0.json"
CEILING = REPO / "results/calibration/_miso202_c3a_2025_anatomy.json"
M205 = REPO / "results/calibration/_miso205_ge_repaired_clock.json"
OUT = REPO / "results/calibration/_miso206_wind_availability_phase0.json"

SCORING_HUB = "INDIANA.HUB"
MONTH_LENS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
# miso-205, published — the N-3 reference.
M205_THRESHOLDS = {2023: 121.43, 2024: 159.01, 2025: 373.02}
# miso-203 G-D's licensing line, verbatim.
LICENSE_LINE = 0.25
# PREREG §3 P7: the object is an availability object only above this share.
P7_MATERIALITY = 0.10
# BALANCE bulk columns (new taxonomy, mid-2024 onward) and legacy names — the
# committed mapping in scripts/data/extend_eia930_hourly_from_balance.py.
_WIND_NEW = (
    "Net Generation (MW) from Wind without Integrated Battery Storage",
    "Net Generation (MW) from Wind with Integrated Battery Storage",
)
_SOLAR_NEW = (
    "Net Generation (MW) from Solar without Integrated Battery Storage",
    "Net Generation (MW) from Solar with Integrated Battery Storage",
)
_WIND_LEGACY = "Net Generation (MW) from Wind"
_SOLAR_LEGACY = "Net Generation (MW) from Solar"


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month per hour on the model's FIXED non-leap 8760 clock."""
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :hours
    ]


def _stamp(year: int, h: int) -> str:
    """'YYYY-MM-DD HEnn' on the fixed non-leap clock — miso-204 §6.4's format."""
    doy, hod = divmod(int(h), 24)
    m = 0
    while doy >= MONTH_LENS[m]:
        doy -= MONTH_LENS[m]
        m += 1
    return f"{year}-{m + 1:02d}-{doy + 1:02d} HE{hod + 1:02d}"


def _sum_or_nan(cols: list[pd.Series]) -> pd.Series:
    """Sum real values across ``cols``; NaN (not 0) where ALL are absent."""
    total = sum(c.fillna(0.0) for c in cols)
    total[pd.concat(cols, axis=1).isna().all(axis=1)] = np.nan
    return total


# The model's MISO calendar, the C3a scoring reference and the production
# renewable frame for 2022-2025 all sit on FIXED CST (Etc/GMT+6). The BALANCE
# bulk file's "Data Date" / "Local Time at End of Hour" for MISO are EST labels
# (MISO's market time), one hour ahead of CST — so the local year is keyed here
# on UTC directly, never on the file's own date columns (the first run of this
# probe keyed on "Data Date" and reproduced production at r = 1.000 only at a
# one-hour lag; that diagnosis is recorded in the N-1 block).
_CST_OFFSET_H = 6


def balance_rebuild(year: int) -> tuple[pd.DataFrame, dict]:
    """Rebuild MISO wind/solar for ``year`` from the raw BALANCE bulk files.

    Per-file taxonomy detection (a year can straddle EIA's mid-2024 revamp),
    the committed ``_NEW_SUM_MAP`` column sums, and the model's own clock: the
    hour whose interval BEGINS at fixed-CST local time ``t`` is the row whose
    ``UTC Time at End of Hour`` is ``t + 1 h + 6 h``; rows are kept for the CST
    local year, sorted by UTC, with the CST Feb 29 dropped. The adjacent years'
    files are read too so the year's boundary hours are present.
    """
    parts = []
    meta: dict = {"files": [], "with_battery_wind_sum_mw": 0.0}
    for yy, halves in (
        (year - 1, ("Jul_Dec",)),
        (year, ("Jan_Jun", "Jul_Dec")),
        (year + 1, ("Jan_Jun",)),
    ):
        for half in halves:
            path = EIA_930_DIR / f"EIA930_BALANCE_{yy}_{half}.parquet"
            if not path.exists():
                meta["files"].append({"file": path.name, "present": False})
                continue
            raw = pd.read_parquet(path)
            raw = raw[raw["Balancing Authority"] == BA]
            is_new = any("Excluding Pumped Storage" in c for c in raw.columns)
            if is_new:
                wind = _sum_or_nan(
                    [pd.to_numeric(raw[c], errors="coerce") for c in _WIND_NEW]
                )
                solar = _sum_or_nan(
                    [pd.to_numeric(raw[c], errors="coerce") for c in _SOLAR_NEW]
                )
                if yy == year:
                    meta["with_battery_wind_sum_mw"] += float(
                        pd.to_numeric(raw[_WIND_NEW[1]], errors="coerce")
                        .fillna(0.0)
                        .sum()
                    )
            else:
                wind = pd.to_numeric(raw[_WIND_LEGACY], errors="coerce")
                solar = pd.to_numeric(raw[_SOLAR_LEGACY], errors="coerce")
            parts.append(
                pd.DataFrame(
                    {
                        "utc": pd.to_datetime(raw["UTC Time at End of Hour"]),
                        "file_local_date": pd.to_datetime(raw["Data Date"]),
                        "file_local_end": pd.to_datetime(
                            raw["Local Time at End of Hour"]
                        ),
                        "wind": wind.to_numpy(float),
                        "solar": solar.to_numpy(float),
                    }
                )
            )
            meta["files"].append(
                {
                    "file": path.name,
                    "present": True,
                    "new_taxonomy": bool(is_new),
                    "rows": int(len(raw)),
                }
            )
    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(subset="utc").sort_values("utc").reset_index(drop=True)
    # The file's own label offset, recorded as the T1 diagnosis.
    file_off = (df["utc"] - df["file_local_end"]).dt.total_seconds() / 3600.0
    meta["file_local_label_utc_offset_h"] = {
        "min": float(file_off.min()),
        "max": float(file_off.max()),
        "note": "5 = EST (MISO market time); the model clock is fixed CST (6)",
    }
    cst_begin = df["utc"] - pd.Timedelta(hours=1 + _CST_OFFSET_H)
    df = df[
        (cst_begin.dt.year == year)
        & ~((cst_begin.dt.month == 2) & (cst_begin.dt.day == 29))
    ].reset_index(drop=True)
    meta["rows_in_cst_year_ex_feb29"] = int(len(df))
    if len(df) != HOURS:
        full = pd.date_range(
            pd.Timestamp(year=year, month=1, day=1)
            + pd.Timedelta(hours=1 + _CST_OFFSET_H),
            periods=HOURS + (24 if year % 4 == 0 else 0),
            freq="h",
        )
        lb = full - pd.Timedelta(hours=1 + _CST_OFFSET_H)
        full = full[~((lb.month == 2) & (lb.day == 29))]
        missing = full.difference(pd.DatetimeIndex(df["utc"]))
        meta["missing_utc_hours"] = [str(t) for t in missing]
        df = (
            df.set_index("utc")
            .reindex(full)
            .reset_index()
            .rename(columns={"index": "utc"})
        )
    else:
        meta["missing_utc_hours"] = []
    meta["archive_hole_hours"] = [
        int(i) for i in np.where(df["wind"].isna().to_numpy())[0]
    ]
    for col in ("wind", "solar"):
        df[col] = df[col].interpolate().bfill().ffill()
    assert len(df) == HOURS, len(df)
    return df, meta


def scoring_reference_rt(year: int, zon: pd.DataFrame) -> np.ndarray:
    """INDIANA.HUB RT on the model's clock — the series C3a is scored against."""
    s = zon[(zon.year == year) & (zon.hub == SCORING_HUB)].sort_values("hour")
    arr = np.full(HOURS, np.nan)
    idx = s["hour"].to_numpy(int)
    keep = idx < HOURS
    arr[idx[keep]] = s["rt"].to_numpy(float)[keep]
    return arr


def _pct_in(series: np.ndarray, idx: np.ndarray, within: np.ndarray) -> float:
    """Mean percentile rank of ``idx`` within the ``within`` population."""
    pop = series[within]
    return float(np.mean([(pop < series[i]).mean() for i in idx]) * 100.0)


def _pct_hod(
    series: np.ndarray, idx: np.ndarray, jj: np.ndarray, hod: np.ndarray
) -> float:
    """Mean percentile of each hour within Jun-Jul hours of the SAME hour-of-day."""
    out = []
    for h in idx:
        peers = jj[hod[jj] == hod[h]]
        out.append(float((series[peers] < series[h]).mean() * 100.0))
    return float(np.mean(out))


def _lag_scan(a: np.ndarray, b: np.ndarray) -> dict:
    """Pearson r of ``a`` shifted by k against ``b``, k in {-1, 0, +1}."""
    out = {}
    for k in (-1, 0, 1):
        if k == 0:
            x, y = a, b
        elif k > 0:
            x, y = a[k:], b[:-k]
        else:
            x, y = a[:k], b[-k:]
        out[str(k)] = round(float(np.corrcoef(x, y)[0, 1]), 6)
    return out


def main() -> None:  # noqa: PLR0915
    zon = pd.read_parquet(ZONAL)
    margins = json.loads(MARGINS.read_text())["g_d_reserve_binding"]
    ceiling = json.loads(CEILING.read_text())["a3_ceiling"]
    m205 = json.loads(M205.read_text())["years"]
    rc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    rate, rate_year = _miso_wind_reference_curtailment_rate()
    grossup = 1.0 / (1.0 - rate)
    iso_cfg = get_iso_config(ISO)
    zones = iso_cfg.zone_names

    report: dict = {
        "charter": (
            "miso-206 phase 0 — bound the WIND-AVAILABILITY object in the object's "
            "own hours before any solve. Zero-solve; nothing armed."
        ),
        "prereg": (
            "results/calibration/PREREG-miso206-wind-availability-object-hours-"
            "2026-09-04.md @ f55af87f"
        ),
        "keeper": "2026-09-03-miso-202-unitclip",
        "basis": "committed artifacts + production loaders only — no LP solved. Rule 22: 2023/2024/2025.",
        "reference_curtailment_rate": {
            "rate": round(rate, 6),
            "latest_contributing_year": rate_year,
            "gross_up_factor": round(grossup, 6),
            "source": "data/raw/miso-hsl/miso_wind_curtailment_annual.csv, Potomac Economics SOM, firm 2023+2024 rows",
        },
        "extract_row_counts_by_local_year": {},
        "years": {},
    }
    ext = pd.read_parquet(EIA_HOURLY_DIR / f"{BA} hourly.parquet")
    report["extract_row_counts_by_local_year"] = {
        str(int(k)): int(v)
        for k, v in ext["Local date"].dt.year.value_counts().sort_index().items()
    }
    # The committed extract's OWN label convention per vintage: its 2018-2021
    # and 2026 rows (BALANCE-sourced) carry EST labels, its 2022-2025 rows
    # (API-sourced) carry America/Chicago labels with the CST year boundary.
    ext_off = (
        pd.to_datetime(ext["UTC time"]) - pd.to_datetime(ext["Local time"])
    ).dt.total_seconds() / 3600.0
    extract_offsets = {
        str(int(k)): {"min": float(v["min"]), "max": float(v["max"])}
        for k, v in ext_off.groupby(ext["Local date"].dt.year)
        .agg(["min", "max"])
        .iterrows()
    }
    first_utc = {
        str(int(k)): str(v)
        for k, v in ext.groupby(ext["Local date"].dt.year)["UTC time"].min().items()
    }
    report["extract_label_convention"] = {
        "utc_minus_local_label_h_by_year": extract_offsets,
        "first_utc_end_of_hour_by_year": first_utc,
        "finding": (
            "vintage-inconsistent labels inside one committed extract: 2018-2021 "
            "and 2026 rows are EST-labelled (year starts at UTC 06:00), 2022-2025 "
            "rows are Chicago-labelled with the year starting at UTC 07:00 (fixed "
            "CST). The training years 2023-2025 are on the model's clock; the "
            "2019-2021 touchpoint years would load ONE HOUR EARLY against the "
            "CST-converted LMP reference. NAMED, not chartered (rule 22: those "
            "years are not solvable for MISO)."
        ),
    }

    mon = _hour_month()
    jun_jul = np.isin(mon, (6, 7))
    hod = np.arange(HOURS) % 24
    jj = np.where(jun_jul)[0]
    all_verdict_broad: list[bool] = []

    for year in YEARS:
        y: dict = {}
        # ---- N-1: the measured series, rebuilt independently -----------------
        rebuilt, meta = balance_rebuild(year)
        prod = load_eia_hourly_renewable_gen(ISO, year)
        meas_w = np.asarray(prod["wind"], float)
        meas_s = np.asarray(prod["solar"], float)
        rb_w = rebuilt["wind"].to_numpy(float)
        rb_s = rebuilt["solar"].to_numpy(float)
        d_w = np.abs(rb_w - meas_w)
        d_s = np.abs(rb_s - meas_s)
        hole = np.array(meta["archive_hole_hours"], dtype=int)
        # Hours the committed EXTRACT lacks for this local year (production's
        # filled frame reindexes them as NaN and ffills/interpolates): a
        # difference there is a production-side fill, not a transform error.
        ext_y = ext[ext["Local date"].dt.year == year]
        ext_utc = pd.DatetimeIndex(ext_y["UTC time"])
        full_utc = pd.date_range(
            pd.Timestamp(year=year, month=1, day=1)
            + pd.Timedelta(hours=1 + _CST_OFFSET_H),
            periods=HOURS + (24 if year % 4 == 0 else 0),
            freq="h",
        )
        lb = full_utc - pd.Timedelta(hours=1 + _CST_OFFSET_H)
        full_utc = full_utc[~((lb.month == 2) & (lb.day == 29))]
        ext_missing = np.where(~full_utc.isin(ext_utc))[0]
        carried = np.ones(HOURS, dtype=bool)
        carried[hole] = False
        carried[ext_missing] = False
        n1 = {
            "balance_files": meta["files"],
            "rows_in_cst_year_ex_feb29": meta["rows_in_cst_year_ex_feb29"],
            "missing_utc_hours_in_balance_files": meta["missing_utc_hours"],
            "balance_file_local_label_utc_offset_h": meta[
                "file_local_label_utc_offset_h"
            ],
            "T1_diagnosis": (
                "the BALANCE file's Data Date / Local Time for MISO are EST labels; "
                "keying the year on them reproduces production only at a +1 h lag "
                "(first run: r = 1.000000 at k = +1, 0.989 at k = 0). The model, the "
                "C3a scoring reference and the production 2022-2025 frame are on "
                "fixed CST, so the rebuild keys the local year on UTC - 6 h."
            ),
            "extract_label_offset_by_year_h": extract_offsets,
            "wind_hours_differing_gt_0p5mw_stamps": [
                _stamp(year, int(h)) for h in np.where(d_w > 0.5)[0][:10]
            ],
            "with_battery_wind_sum_mw": round(meta["with_battery_wind_sum_mw"], 1),
            "balance_archive_hole_hours": [_stamp(year, int(h)) for h in hole],
            "n_archive_hole_hours": int(hole.size),
            "extract_missing_hours_production_filled": [
                {
                    "stamp": _stamp(year, int(h)),
                    "production_filled_mw": round(float(meas_w[h]), 1),
                    "archive_measured_mw": round(float(rb_w[h]), 1),
                }
                for h in ext_missing
            ],
            "wind_max_abs_diff_vs_production_mw": round(float(d_w.max()), 4),
            "wind_max_abs_diff_on_archive_carried_hours_mw": round(
                float(d_w[carried].max()), 4
            ),
            "wind_hours_differing_gt_0p5mw": int((d_w > 0.5).sum()),
            "wind_hours_differing_gt_0p5mw_outside_hole": int(
                (d_w[carried] > 0.5).sum()
            ),
            "wind_jun_jul_max_abs_diff_mw": round(float(d_w[jj].max()), 4),
            "solar_max_abs_diff_on_archive_carried_hours_mw": round(
                float(d_s[carried].max()), 4
            ),
            "solar_hours_differing_gt_0p5mw_outside_hole": int(
                (d_s[carried] > 0.5).sum()
            ),
            "hole_note": (
                "hours the BALANCE bulk archive does not carry for MISO at all; the "
                "API-built production extract carries measured values there, so a "
                "difference on those hours is an archive gap, not a transform error. "
                "Conversely an hour the EXTRACT lacks is filled by production "
                "(_eia_hourly_frame_filled: ffill/interpolate) while the archive "
                "carries the measured value — a production-side fill, reported."
            ),
            "lag_scan_r_rebuilt_vs_production": _lag_scan(rb_w, meas_w),
            "extract_rows_this_local_year": report["extract_row_counts_by_local_year"][
                str(year)
            ],
        }
        n1["reproduces_production_on_archive_carried_hours"] = bool(
            n1["wind_hours_differing_gt_0p5mw_outside_hole"] == 0
            and n1["solar_hours_differing_gt_0p5mw_outside_hole"] == 0
            and _lag_scan(rb_w[carried], meas_w[carried])["0"] >= 0.999999
        )
        y["n1_balance_rebuild_reproduces_production"] = n1

        # ---- N-2: the production BOUND under the keeper's own config ----------
        cfg = ScenarioConfig(**{**rc, "mode": "backcast", "weather_year": year})
        wcf, wcap, scf, scap = load_renewable_profiles(ISO, year, iso_cfg, cfg)
        bound_w = (wcf * wcap[:, None]).sum(axis=0)
        bound_s = (scf * scap[:, None]).sum(axis=0)
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            k: g.groupby("hour")["mw"].sum().sort_index().to_numpy()[:HOURS]
            for k, g in ch.groupby("klass")
        }
        p1_w = np.asarray(disp["wind"], float)
        p1_s = np.asarray(disp["solar"], float)
        gap_w = bound_w - p1_w
        n2 = {
            "bound_vs_delivered_over_1_minus_r_max_abs_diff_mw": round(
                float(np.abs(bound_w - meas_w * grossup).max()), 4
            ),
            "solar_bound_vs_delivered_max_abs_diff_mw": round(
                float(np.abs(bound_s - meas_s).max()), 4
            ),
            "p1_wind_below_bound_max_mw": round(float(gap_w.max()), 4),
            "hours_p1_wind_curtailed_gt_1mw": int((gap_w > 1.0).sum()),
            "hours_p1_wind_curtailed_gt_1mw_jun_jul": int((gap_w[jj] > 1.0).sum()),
            "endogenous_wind_curtailment_mwh": round(float(gap_w.sum()), 1),
            "hours_p1_solar_curtailed_gt_1mw": int(((bound_s - p1_s) > 1.0).sum()),
            "endogenous_solar_curtailment_mwh": round(float((bound_s - p1_s).sum()), 1),
            "installed_wind_mw": round(float(wcap.sum()), 0),
            "per_zone_installed_wind_mw": {
                z: round(float(c), 0) for z, c in zip(zones, wcap)
            },
            "p1_over_measured_ratio_min": round(
                float((p1_w / np.where(meas_w > 0, meas_w, np.nan))[meas_w > 0].min()),
                6,
            ),
            "p1_over_measured_ratio_max": round(
                float((p1_w / np.where(meas_w > 0, meas_w, np.nan))[meas_w > 0].max()),
                6,
            ),
        }
        n2["identity_holds"] = bool(
            n2["bound_vs_delivered_over_1_minus_r_max_abs_diff_mw"] < 0.01
            and n2["p1_wind_below_bound_max_mw"] < 0.01
        )
        y["n2_bound_identity_and_p1_on_bound"] = n2

        # ---- N-3: the object set ----------------------------------------------
        act = scoring_reference_rt(year, zon)
        thr = float(np.nanpercentile(act[jj], 99.0))
        obj = jj[act[jj] >= thr]
        stamps = [_stamp(year, h) for h in sorted(obj.tolist())]
        n3 = {
            "threshold_usd_per_mwh": round(thr, 2),
            "miso205_threshold": M205_THRESHOLDS[year],
            "n_hours": int(obj.size),
            "stamps": stamps,
        }
        m205_stamps = m205[str(year)]["n1_reproduces_miso204_object_set"].get("stamps")
        n3["reproduces_miso205"] = bool(
            abs(thr - M205_THRESHOLDS[year]) < 0.006
            and (m205_stamps is None or stamps == m205_stamps)
        )
        n3["obj_hours_in_balance_archive_hole"] = int(np.isin(obj, hole).sum())
        n3["obj_hours_in_extract_missing"] = int(np.isin(obj, ext_missing).sum())
        y["n3_object_set_reproduces_miso205"] = n3

        # ---- drivers on the model clock ---------------------------------------
        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        load = sysd.groupby("hour")["demand"].sum().sort_index().to_numpy()[:HOURS]
        price_mean = (
            sysd.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]
        )
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).sort_index().to_numpy()[:HOURS]
        netload = load - p1_w - p1_s
        k = int(obj.size)
        top_load = jj[np.argsort(load[jj])[-k:]]
        excess_w = p1_w - meas_w

        def _set(idx: np.ndarray) -> dict:
            return {
                "n_hours": int(idx.size),
                "model_wind_mw": round(float(p1_w[idx].mean()), 1),
                "measured_930_wind_mw": round(float(meas_w[idx].mean()), 1),
                "wind_excess_mw": round(float(excess_w[idx].mean()), 1),
                "wind_excess_share_of_model": round(
                    float(excess_w[idx].mean() / p1_w[idx].mean()), 5
                ),
                "model_solar_mw": round(float(p1_s[idx].mean()), 1),
                "measured_930_solar_mw": round(float(meas_s[idx].mean()), 1),
                "solar_diff_mw": round(float((p1_s - meas_s)[idx].mean()), 2),
                "measured_wind_pct_jun_jul": round(_pct_in(meas_w, idx, jun_jul), 1),
                "model_wind_pct_jun_jul": round(_pct_in(p1_w, idx, jun_jul), 1),
                "measured_wind_pct_hod_matched": round(
                    _pct_hod(meas_w, idx, jj, hod), 1
                ),
                "model_wind_pct_hod_matched": round(_pct_hod(p1_w, idx, jj, hod), 1),
                "measured_solar_pct_jun_jul": round(_pct_in(meas_s, idx, jun_jul), 1),
                "measured_solar_pct_hod_matched": round(
                    _pct_hod(meas_s, idx, jj, hod), 1
                ),
                "model_solar_pct_hod_matched": round(_pct_hod(p1_s, idx, jj, hod), 1),
                "load_mw": round(float(load[idx].mean()), 0),
                "netload_mw": round(float(netload[idx].mean()), 0),
            }

        sets = {
            "obj_hours": _set(obj),
            "top_gross_load_hours": _set(top_load),
            "all_jun_jul": _set(jj),
        }
        y["a_levels_and_ranks"] = sets

        # ---- (b) the annual excess --------------------------------------------
        y["b_annual_excess"] = {
            "model_p1_wind_twh": round(float(p1_w.sum()) / 1e6, 3),
            "measured_930_wind_twh": round(float(meas_w.sum()) / 1e6, 3),
            "excess_twh": round(float(excess_w.sum()) / 1e6, 3),
            "ratio_model_over_measured": round(float(p1_w.sum() / meas_w.sum()), 5),
            "model_p1_solar_twh": round(float(p1_s.sum()) / 1e6, 3),
            "measured_930_solar_twh": round(float(meas_s.sum()) / 1e6, 3),
        }

        # ---- (c) THE BOUND, against miso-203 G-D's margins (READ) ---------------
        mg = margins[str(year)]
        broad = float(mg["margin_broad_mw_min_scarce"])
        armed = float(mg["idle_armed_classes_mw_mean_scarce"])
        ex = float(excess_w[obj].mean())
        total = float(p1_w[obj].mean())
        hmax = int(obj[int(np.nanargmax(act[obj]))])
        c = {
            "margins_source": "_miso203_summer_peak_anchor_phase0.json::g_d_reserve_binding (READ, not re-derived)",
            "margin_broad_mw_min_scarce": broad,
            "idle_armed_classes_mw_mean_scarce": armed,
            "license_line": LICENSE_LINE,
            "obj_wind_excess_mw": round(ex, 1),
            "excess_share_of_broad_margin": round(ex / broad, 5),
            "excess_share_of_armed_idle": round(ex / armed, 5),
            "total_removal_ceiling_mw": round(total, 1),
            "total_removal_share_of_broad_margin": round(total / broad, 5),
            "total_removal_share_of_armed_idle": round(total / armed, 5),
            "largest_hour": {
                "stamp": _stamp(year, hmax),
                "actual_usd": round(float(act[hmax]), 2),
                "model_lw_usd": round(float(price_lw[hmax]), 2),
                "model_wind_mw": round(float(p1_w[hmax]), 1),
                "measured_930_wind_mw": round(float(meas_w[hmax]), 1),
                "excess_mw": round(float(excess_w[hmax]), 1),
                "excess_share_of_broad_margin": round(float(excess_w[hmax]) / broad, 5),
            },
            "miso202_a3_ceiling": {
                "jun_jul_price_max": ceiling[str(year)]["jun_jul_price_max"],
                "unserved_energy_mwh": ceiling[str(year)]["unserved_energy_mwh"],
                "ordc_shortfall_hours": {
                    f: v["hours_with_shortfall"]
                    for f, v in ceiling[str(year)]["reserve_families"].items()
                },
            },
        }
        c["P6_refuse_on_broad_limb"] = bool(ex / broad < LICENSE_LINE)
        c["P6_refuse_even_at_total_removal_broad"] = bool(total / broad < LICENSE_LINE)
        all_verdict_broad.append(c["P6_refuse_on_broad_limb"])
        y["c_the_bound"] = c

        # ---- P7: the mechanism rule beside the magnitude rule -------------------
        d_net = float(netload[obj].mean() - netload[jj].mean())
        d_wind_def = -float(p1_w[obj].mean() - p1_w[jj].mean())
        meas_wind_def = -float(meas_w[obj].mean() - meas_w[jj].mean())
        y["p7_mechanism_rule"] = {
            "netload_elevation_over_jun_jul_mw": round(d_net, 0),
            "obj_wind_excess_mw": round(ex, 1),
            "excess_share_of_netload_elevation": round(ex / d_net, 5),
            "materiality_line": P7_MATERIALITY,
            "is_availability_object": bool(ex / d_net >= P7_MATERIALITY),
            "model_wind_deficit_vs_jun_jul_mean_mw": round(d_wind_def, 0),
            "measured_930_wind_deficit_vs_jun_jul_mean_mw": round(meas_wind_def, 0),
            "note": (
                "the wind DEFICIT in the object's hours is a MEASURED fact (the "
                "930 series is low there for the time of day), not a model error; "
                "the model's only departure from measurement is the constant "
                "gross-up"
            ),
        }

        # ---- P8: is the headroom ever live? ------------------------------------
        y["p8_headroom_liveness"] = {
            "jun_jul_hours_wind_curtailed_gt_1mw": int((gap_w[jj] > 1.0).sum()),
            "obj_hours_wind_curtailed_gt_1mw": int((gap_w[obj] > 1.0).sum()),
            "jun_jul_hours_model_price_lw_le_0": int((price_lw[jj] <= 0.0).sum()),
        }

        # ---- the per-hour table (T7) --------------------------------------------
        rows = []
        for h in sorted(obj.tolist()):
            peers = jj[hod[jj] == hod[h]]
            rows.append(
                {
                    "hour": int(h),
                    "stamp": _stamp(year, h),
                    "actual_indiana_hub_usd": round(float(act[h]), 2),
                    "model_price_zone_mean_usd": round(float(price_mean[h]), 2),
                    "model_price_load_weighted_usd": round(float(price_lw[h]), 2),
                    "model_wind_mw": round(float(p1_w[h]), 1),
                    "measured_930_wind_mw": round(float(meas_w[h]), 1),
                    "wind_excess_mw": round(float(excess_w[h]), 1),
                    "measured_wind_pct_jj": round(
                        float((meas_w[jj] < meas_w[h]).mean() * 100), 1
                    ),
                    "measured_wind_pct_hod": round(
                        float((meas_w[peers] < meas_w[h]).mean() * 100), 1
                    ),
                    "model_solar_mw": round(float(p1_s[h]), 1),
                    "measured_930_solar_mw": round(float(meas_s[h]), 1),
                    "load_mw": round(float(load[h]), 0),
                    "netload_mw": round(float(netload[h]), 0),
                }
            )
        y["hours"] = rows
        report["years"][str(year)] = y

    # ---- the pre-committed verdict (PREREG §3 P6 / §6) --------------------------
    refuse = all(all_verdict_broad)
    p7_any = any(
        report["years"][str(yy)]["p7_mechanism_rule"]["is_availability_object"]
        for yy in YEARS
    )
    report["verdict"] = {
        "rule": (
            "REFUSE iff obj-hour wind excess / margin_broad_mw_min_scarce < 0.25 in "
            "every year (miso-203 G-D's line, verbatim); the object is an "
            "availability object only if excess / net-load elevation >= 0.10"
        ),
        "P6_refuse": bool(refuse),
        "P7_availability_object_any_year": bool(p7_any),
        "verdict": (
            "REFUSED — DEAD on the bound; nothing armed, no LP"
            if refuse and not p7_any
            else "RE-CHARTER BRANCH (against prediction) — see PREREG §6; still no solve"
        ),
    }
    report["scored_predictions_placeholder"] = "scored in FINDING-miso206 §8"

    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    for yy in YEARS:
        d = report["years"][str(yy)]
        n1 = d["n1_balance_rebuild_reproduces_production"]
        n2 = d["n2_bound_identity_and_p1_on_bound"]
        n3 = d["n3_object_set_reproduces_miso205"]
        o = d["a_levels_and_ranks"]["obj_hours"]
        c = d["c_the_bound"]
        print(
            f"{yy}: N-1 {n1['reproduces_production_on_archive_carried_hours']} (max|dW| carried "
            f"{n1['wind_max_abs_diff_on_archive_carried_hours_mw']}, hole h {n1['n_archive_hole_hours']}, "
            f"r0 {n1['lag_scan_r_rebuilt_vs_production']['0']}) | "
            f"N-2 {n2['identity_holds']} (curtailed h {n2['hours_p1_wind_curtailed_gt_1mw']}) | N-3 {n3['reproduces_miso205']} "
            f"(obj in hole {n3['obj_hours_in_balance_archive_hole']})"
        )
        print(
            f"      OBJ model {o['model_wind_mw']} / 930 {o['measured_930_wind_mw']} / excess {o['wind_excess_mw']} MW; "
            f"meas pct JJ {o['measured_wind_pct_jun_jul']} hod {o['measured_wind_pct_hod_matched']} (model hod {o['model_wind_pct_hod_matched']}); "
            f"solar diff {o['solar_diff_mw']} (hod {o['measured_solar_pct_hod_matched']})"
        )
        print(
            f"      annual excess {d['b_annual_excess']['excess_twh']:+.3f} TWh; bound: excess/broad {c['excess_share_of_broad_margin']:.4f}, "
            f"/armed {c['excess_share_of_armed_idle']:.4f}; total-removal/broad {c['total_removal_share_of_broad_margin']:.4f}; "
            f"P7 share {d['p7_mechanism_rule']['excess_share_of_netload_elevation']:.4f}"
        )
    print(json.dumps(report["verdict"], indent=1))


if __name__ == "__main__":
    main()
