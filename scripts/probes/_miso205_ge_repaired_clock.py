"""miso-205 phase 0 — miso-203's G-E driver characterisation, RE-DONE on the REPAIRED instrument.

miso-204 section F established that ``_miso203_scarce_hour_identity`` (and
``_miso202_c3a_2025_anatomy`` blocks a2/a4) build their hourly actual as an
**eight-hub equal-weighted mean on the RAW EST hour-ending index**, while the
series C3a is scored against — ``actual_lmp_hourly_MISO.parquet``, i.e.
``bench.avgLMP.rt``/``rt_lw`` — is **INDIANA.HUB on the model's fixed-CST
non-leap 8760**.  The defect is a constant −1 h plus a further −24 h after
Feb 28 of a leap year.  It is invisible in the annual mean (so **C3a itself is
unaffected**) and fatal to hour-matching: MISO RT's lag-1 autocorrelation is
only 0.39 / 0.37 / 0.44, so only 2 / 1 / 4 of miso-203's 15 hours are in the
top 1 % of the series C3a actually scores.

miso-203's §8 **hour-of-day** claims were corrected by miso-204 §6.5 and are
inherited here.  Its **driver** characterisation — 11.6 GW less load but only
2.2 GW less net load, solar 11,435 → 1,859 MW, net-load p94.3, zero of 15
top-15 load or dry-bulb hours — was computed on the misaligned hour set and is
therefore **UNMEASURED**, neither re-affirmed nor refuted.  This probe measures
it on the repaired instrument.

The drivers themselves (keeper ``hourly/`` sidecars, ``iso_zone_hourly_drybulb``)
are already on the model's clock and are **unaffected** by the LMP defect —
only the hour SET moves.  The raw ``data/raw/lmp-data/MISO/*.csv.gz`` staging is
**NOT** re-derived here; that re-derivation is the defect.

PREREG ``results/calibration/PREREG-miso205-ge-repaired-clock-2026-09-03.md``,
pushed at ``fc8006d9`` before any adjudicating statistic.  Gates N-1, N-2 are
reproduction PRE-CONDITIONS; G-A/G-B/G-C/G-D answer the charter; G-E re-checks
the location argument; G-F re-measures the seam object on the right hours and is
**model-side descriptive only**.

Every input is a committed artifact; **no LP is solved**.  Rule 22
``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    python3 scripts/probes/_miso205_ge_repaired_clock.py
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
from market_sim.data.eia_loader import iso_zone_hourly_drybulb  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
SYSREF = REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet"
ANCHORS = REPO / "results/calibration/_miso203_summer_peak_anchor_phase0.json"
BASELINE = REPO / "results/calibration/_miso203_scarce_hour_identity.json"
OUT = REPO / "results/calibration/_miso205_ge_repaired_clock.json"

SCORING_HUB = "INDIANA.HUB"
RENEW = ("wind", "solar")
MONTH_LENS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

# miso-204 §6.5 / §6.4, published — the PRE-COMMITTED N-1 reference.
M204_MEAN_HOD = {2023: 11.67, 2024: 15.73, 2025: 15.87}
M204_IN_H18_21 = {2023: 1, 2024: 3, 2025: 4}
M204_IN_H15_18 = {2023: 1, 2024: 9, 2025: 11}
M204_2025_STAMPS = [
    "2025-06-17 HE18",
    "2025-06-23 HE18",
    "2025-06-23 HE19",
    "2025-06-24 HE11",
    "2025-06-24 HE12",
    "2025-06-24 HE16",
    "2025-06-24 HE17",
    "2025-06-24 HE18",
    "2025-06-24 HE19",
    "2025-07-15 HE16",
    "2025-07-22 HE18",
    "2025-07-28 HE18",
    "2025-07-28 HE19",
    "2025-07-28 HE20",
    "2025-07-30 HE14",
]
# _miso203_summer_peak_anchor_phase0.json g_a_anchor 2025 — the TRAP 5 assertion.
M203_ANCHOR_2025 = {
    "MISO-West": 32.249,
    "MISO-Plains": 33.34,
    "MISO-Illinois": 32.701,
    "MISO-Indiana": 33.018,
    "MISO-East": 31.902,
    "MISO-South": 35.674,
}
DRIVER_KEYS = (
    "load_mw",
    "wind_mw",
    "solar_mw",
    "netload_mw",
    "netload_3h_ramp_mw",
    "iso_drybulb_c",
    "hour_of_day_mean",
)
# G-F: the P1 dispatch classes miso-202 §2 A-4 reported, seam first.
SEAM_CLASSES = ("import", "CT_PEAKER", "ST_GAS", "COAL_PRB", "wind", "solar")


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


def scoring_reference_rt(year: int, zon: pd.DataFrame) -> np.ndarray:
    """INDIANA.HUB RT on the model's clock — the series C3a is scored against.

    Read from the COMMITTED zonal parquet, never re-derived from the raw
    staging: that re-derivation is the miso-204 defect.
    """
    s = zon[(zon.year == year) & (zon.hub == SCORING_HUB)].sort_values("hour")
    arr = np.full(HOURS, np.nan)
    idx = s["hour"].to_numpy(int)
    keep = idx < HOURS
    arr[idx[keep]] = s["rt"].to_numpy(float)[keep]
    return arr


def _pctile_rank(series: np.ndarray, idx: np.ndarray, within: np.ndarray) -> float:
    """Mean percentile rank of ``idx`` within the ``within`` population."""
    pop = series[within]
    return float(np.mean([(pop < series[i]).mean() for i in idx]) * 100.0)


def main() -> None:  # noqa: PLR0915
    zon = pd.read_parquet(ZONAL)
    sysref = pd.read_parquet(SYSREF)
    anchors = json.loads(ANCHORS.read_text())["g_a_anchor"]
    baseline = json.loads(BASELINE.read_text())["years"]

    # ---- TRAP 5: the anchors are READ, and asserted, never re-derived --------
    anchor_ok = all(
        abs(anchors["2025"][z]["t_ref_c"] - v) < 5e-4
        for z, v in M203_ANCHOR_2025.items()
    )

    report: dict = {
        "charter": (
            "miso-205 phase 0 — miso-203's G-E driver characterisation RE-DONE on "
            "the repaired instrument (INDIANA.HUB on the model's fixed-CST "
            "non-leap 8760, read from the committed zonal parquet). miso-203's "
            "hour-of-day claims were corrected by miso-204 §6.5 and are inherited; "
            "its DRIVER claims were computed on the misaligned hour set and are "
            "UNMEASURED — neither re-affirmed nor refuted. This probe measures them."
        ),
        "prereg": "results/calibration/PREREG-miso205-ge-repaired-clock-2026-09-03.md @ fc8006d9",
        "keeper": "2026-09-03-miso-202-unitclip",
        "basis": "committed artifacts only — no LP solved. Rule 22: 2023/2024/2025.",
        "instrument": (
            "OBJ = top 1% of Jun-Jul hours of actual_lmp_hourly_zonal_MISO.parquet "
            "hub=INDIANA.HUB col=rt. Drivers from the keeper's hourly/ sidecars and "
            "iso_zone_hourly_drybulb — already on the model clock, unaffected by the "
            "LMP defect; only the hour SET moves."
        ),
        "trap5_anchors_read_not_derived": {
            "reproduces_miso203_g_a_anchor_2025": bool(anchor_ok),
            "anchors_2025": {
                z: anchors["2025"][z]["t_ref_c"] for z in M203_ANCHOR_2025
            },
        },
        "years": {},
    }

    mon = _hour_month()
    jun_jul = np.isin(mon, (6, 7))
    summer = np.isin(mon, (6, 7, 8, 9))
    hod = np.arange(HOURS) % 24
    zones = [z.name for z in get_iso_config(ISO).zones]
    jj = np.where(jun_jul)[0]

    for year in YEARS:
        y: dict = {}
        act = scoring_reference_rt(year, zon)

        # ---- TRAP 7: NaN accounting before any cut is taken -----------------
        s_ref = sysref[sysref.year == year].sort_values("hour")["rt"].to_numpy()
        n_nan_jj = int(np.isnan(act[jj]).sum())
        y["trap7_scoring_reference_coverage"] = {
            "n_nan_jun_jul": n_nan_jj,
            "n_nan_full_year": int(np.isnan(act).sum()),
            "max_abs_diff_vs_actual_lmp_hourly_MISO": (
                float(np.nanmax(np.abs(act[: len(s_ref)] - s_ref)))
                if len(s_ref) == HOURS
                else None
            ),
            "note": (
                "the C3a system reference IS this hub (miso-204 §6.1); the residual "
                "here is float32 rounding in the committed parquet"
            ),
        }

        thr = float(np.nanpercentile(act[jj], 99.0))
        obj = jj[act[jj] >= thr]
        k = int(obj.size)

        # ---- N-1: reproduce miso-204's published object set ------------------
        n1 = {
            "n_hours": k,
            "mean_hour_of_day": round(float(hod[obj].mean()), 2),
            "miso204_mean_hour_of_day": M204_MEAN_HOD[year],
            "in_h18_21": int(np.sum((hod[obj] >= 18) & (hod[obj] <= 21))),
            "miso204_in_h18_21": M204_IN_H18_21[year],
            "in_h15_18": int(np.sum((hod[obj] >= 15) & (hod[obj] <= 18))),
            "miso204_in_h15_18": M204_IN_H15_18[year],
            "threshold_usd_per_mwh": round(thr, 2),
        }
        n1["reproduces_miso204"] = bool(
            abs(n1["mean_hour_of_day"] - M204_MEAN_HOD[year]) <= 0.01
            and n1["in_h18_21"] == M204_IN_H18_21[year]
            and n1["in_h15_18"] == M204_IN_H15_18[year]
        )
        stamps = [_stamp(year, h) for h in sorted(obj.tolist())]
        if year == 2025:
            n1["stamps_match_miso204_table"] = bool(stamps == M204_2025_STAMPS)
            n1["stamps"] = stamps
        y["n1_reproduces_miso204_object_set"] = n1

        # ---- drivers, exactly miso-203's construction ------------------------
        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        load = sysd.groupby("hour")["demand"].sum().sort_index().to_numpy()[:HOURS]
        price_zone_mean = (
            sysd.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]
        )
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).sort_index().to_numpy()[:HOURS]

        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            kk: g.groupby("hour")["mw"].sum().sort_index().to_numpy()[:HOURS]
            for kk, g in ch.groupby("klass")
        }
        vre = np.zeros(HOURS)
        for r in RENEW:
            if r in disp:
                vre += np.asarray(disp[r], float)
        netload = load - vre

        temps = {}
        for z in zones:
            t = iso_zone_hourly_drybulb(ISO, year, HOURS, zone=z)
            if t is not None:
                temps[z] = np.asarray(t, float)
        iso_t = (
            np.mean(np.vstack(list(temps.values())), axis=0)
            if temps
            else np.zeros(HOURS)
        )

        ramp3 = np.full(HOURS, np.nan)
        ramp3[3:] = netload[3:] - netload[:-3]

        def _drivers(idx: np.ndarray) -> dict:
            return {
                "load_mw": round(float(load[idx].mean()), 0),
                "wind_mw": round(
                    float(
                        np.asarray(disp.get("wind", np.zeros(HOURS)), float)[idx].mean()
                    ),
                    0,
                ),
                "solar_mw": round(
                    float(
                        np.asarray(disp.get("solar", np.zeros(HOURS)), float)[
                            idx
                        ].mean()
                    ),
                    0,
                ),
                "netload_mw": round(float(netload[idx].mean()), 0),
                "netload_3h_ramp_mw": round(float(np.nanmean(ramp3[idx])), 0),
                "iso_drybulb_c": round(float(iso_t[idx].mean()), 1),
                "hour_of_day_mean": round(float(hod[idx].mean()), 1),
            }

        top_load = jj[np.argsort(load[jj])[-k:]]

        # ---- N-2: the comparison set is miso-203's own, unchanged ------------
        mine_top = _drivers(top_load)
        theirs_top = baseline[str(year)]["driver_contrast"]["top_gross_load_hours"]
        n2_diffs = {
            kk: round(float(mine_top[kk] - theirs_top[kk]), 3) for kk in DRIVER_KEYS
        }
        y["n2_comparison_set_unchanged"] = {
            "mine": mine_top,
            "miso203_committed": theirs_top,
            "diffs": n2_diffs,
            "reproduces_exactly": bool(all(abs(v) < 0.51 for v in n2_diffs.values())),
            "note": (
                "the top-15 gross-load set is defined on MODEL drivers and does not "
                "move with the clock repair; a mismatch would mean the driver "
                "pipeline differs and no contrast below is comparable"
            ),
        }

        # ---- G-A / G-B: drivers and the contrast ----------------------------
        y["g_a_g_b_driver_contrast"] = {
            "obj_hours_REPAIRED": _drivers(obj),
            "obj_hours_miso203_COMMITTED_defective": baseline[str(year)][
                "driver_contrast"
            ]["scarce_hours"],
            "top_gross_load_hours": mine_top,
            "all_jun_jul": _drivers(jj),
        }

        ranks = {
            "load_pctile_in_jun_jul": round(_pctile_rank(load, obj, jun_jul), 1),
            "netload_pctile_in_jun_jul": round(_pctile_rank(netload, obj, jun_jul), 1),
            "drybulb_pctile_in_jun_jul": round(_pctile_rank(iso_t, obj, jun_jul), 1),
            "load_pctile_in_summer": round(_pctile_rank(load, obj, summer), 1),
            "netload_pctile_in_summer": round(_pctile_rank(netload, obj, summer), 1),
            "drybulb_pctile_in_summer": round(_pctile_rank(iso_t, obj, summer), 1),
        }
        y["g_a_mean_ranks"] = {
            "repaired": ranks,
            "miso203_committed_defective": baseline[str(year)]["mean_ranks"],
        }

        # ---- G-C: overlaps ---------------------------------------------------
        def _topk(series: np.ndarray, n: int) -> set:
            return set(jj[np.argsort(series[jj])[-n:]].tolist())

        overlap = {
            "n_obj": k,
            "n_also_in_top_load_hours": len(set(obj.tolist()) & _topk(load, k)),
            "n_also_in_top_netload_hours": len(set(obj.tolist()) & _topk(netload, k)),
            "n_also_in_top_drybulb_hours": len(set(obj.tolist()) & _topk(iso_t, k)),
        }
        y["g_c_overlap_with_driver_extremes"] = {
            "repaired": overlap,
            "miso203_committed_defective": baseline[str(year)][
                "overlap_with_driver_extremes"
            ],
        }

        y["hour_of_day_histogram"] = {
            str(int(x)): int(c)
            for x, c in zip(*np.unique(hod[obj], return_counts=True))
        }
        y["n_distinct_days"] = int(len(set((obj // 24).tolist())))

        # ---- G-E: the LOCATION argument, re-checked --------------------------
        loc = {}
        n_below = 0
        gaps = []
        for z in zones:
            if z not in temps or z not in anchors[str(year)]:
                continue
            t_ref = float(anchors[str(year)][z]["t_ref_c"])
            gap = float(temps[z][obj].mean() - t_ref)
            gaps.append(gap)
            n_below += int(gap < 0)
            loc[z] = {
                "t_ref_c": round(t_ref, 2),
                "obj_hour_mean_c": round(float(temps[z][obj].mean()), 2),
                "obj_hour_max_c": round(float(temps[z][obj].max()), 2),
                "obj_minus_ref_c": round(gap, 2),
            }
        y["g_e_location_recheck"] = {
            "zones": loc,
            "n_zones_below_anchor": n_below,
            "n_zones": len(gaps),
            "mean_gap_c": round(float(np.mean(gaps)), 2) if gaps else None,
        }

        # ---- G-F: the seam object, re-measured (MODEL-SIDE DESCRIPTIVE) ------
        other_jj = np.array(sorted(set(jj.tolist()) - set(obj.tolist())))
        seam = {}
        for cls in SEAM_CLASSES:
            if cls not in disp:
                continue
            arr = np.asarray(disp[cls], float)
            seam[cls] = {
                "obj_mean_mw": round(float(arr[obj].mean()), 1),
                "other_jun_jul_mean_mw": round(float(arr[other_jj].mean()), 1),
                "excess_mw": round(float(arr[obj].mean() - arr[other_jj].mean()), 1),
            }
        y["g_f_seam_and_class_dispatch"] = {
            "label": (
                "MODEL-SIDE DESCRIPTIVE ONLY — no committed hourly MISO interchange "
                "actual exists, so this is NOT a residual against a benchmark "
                "(miso-202 §2 A-4's own labelling). Licenses nothing."
            ),
            "basis": "OBJ hours vs the other Jun-Jul hours, P1",
            "n_other_jun_jul_hours": int(other_jj.size),
            "classes": seam,
            "miso202_committed_defective_import_excess_mw": 3844.4,
        }

        # ---- the per-hour table ---------------------------------------------
        rows = []
        for h in sorted(obj.tolist()):
            rows.append(
                {
                    "hour": int(h),
                    "stamp": _stamp(year, h),
                    "actual_indiana_hub_usd": round(float(act[h]), 2),
                    "model_price_zone_mean_usd": round(float(price_zone_mean[h]), 2),
                    "model_price_load_weighted_usd": round(float(price_lw[h]), 2),
                    "load_mw": round(float(load[h]), 0),
                    "load_pctile_jj": round(
                        float((load[jj] < load[h]).mean() * 100), 1
                    ),
                    "solar_mw": round(
                        float(np.asarray(disp.get("solar", np.zeros(HOURS)), float)[h]),
                        0,
                    ),
                    "netload_mw": round(float(netload[h]), 0),
                    "netload_pctile_jj": round(
                        float((netload[jj] < netload[h]).mean() * 100), 1
                    ),
                    "netload_3h_ramp_mw": round(float(ramp3[h]), 0),
                    "iso_drybulb_c": round(float(iso_t[h]), 1),
                    "drybulb_pctile_jj": round(
                        float((iso_t[jj] < iso_t[h]).mean() * 100), 1
                    ),
                }
            )
        # ---- H-1: POST-HOC, NOT PRE-REGISTERED. Which driver actually
        # elevates net load in the OBJ hours, and is the renewable anomaly in
        # SOLAR or in WIND? The pre-registered C10 rule measures the ramp's
        # MAGNITUDE and is silent on its CAUSE; this block supplies the cause.
        wind_a = np.asarray(disp.get("wind", np.zeros(HOURS)), float)
        sol_a = np.asarray(disp.get("solar", np.zeros(HOURS)), float)
        d_net = float(netload[obj].mean() - netload[jj].mean())
        d_load = float(load[obj].mean() - load[jj].mean())
        d_wind = -float(wind_a[obj].mean() - wind_a[jj].mean())
        d_sol = -float(sol_a[obj].mean() - sol_a[jj].mean())

        def _hod_matched_pctile(series: np.ndarray) -> float:
            """Mean percentile of each OBJ hour within Jun-Jul hours of the SAME
            hour-of-day — the diurnal cycle removed, so a low value means the
            driver was anomalous FOR THAT TIME OF DAY, not merely off-peak."""
            out = []
            for h in obj:
                peers = jj[hod[jj] == hod[h]]
                out.append(float((series[peers] < series[h]).mean() * 100.0))
            return float(np.mean(out))

        y["h1_netload_elevation_decomposition__POSTHOC"] = {
            "label": (
                "POST-HOC, NOT PRE-REGISTERED, no gate. The C10 decision rule "
                "measures the ramp's magnitude and is silent on its cause; this "
                "block supplies the cause."
            ),
            "netload_excess_over_all_jun_jul_mw": round(d_net, 0),
            "from_load_mw": round(d_load, 0),
            "from_wind_deficit_mw": round(d_wind, 0),
            "from_solar_deficit_mw": round(d_sol, 0),
            "share_load": round(d_load / d_net, 4) if d_net else None,
            "share_wind_deficit": round(d_wind / d_net, 4) if d_net else None,
            "share_solar_deficit": round(d_sol / d_net, 4) if d_net else None,
            "solar_pctile_in_jun_jul": round(_pctile_rank(sol_a, obj, jun_jul), 1),
            "wind_pctile_in_jun_jul": round(_pctile_rank(wind_a, obj, jun_jul), 1),
            "solar_pctile_hod_matched": round(_hod_matched_pctile(sol_a), 1),
            "wind_pctile_hod_matched": round(_hod_matched_pctile(wind_a), 1),
            "load_pctile_hod_matched": round(_hod_matched_pctile(load), 1),
            "drybulb_pctile_hod_matched": round(_hod_matched_pctile(iso_t), 1),
        }

        # ---- H-2: POST-HOC. The single largest-price OBJ hour's identity.
        hmax = int(obj[int(np.nanargmax(act[obj]))])
        y["h2_largest_hour__POSTHOC"] = {
            "stamp": _stamp(year, hmax),
            "actual_indiana_hub_usd": round(float(act[hmax]), 2),
            "model_price_load_weighted_usd": round(float(price_lw[hmax]), 2),
            "load_pctile_jj": round(float((load[jj] < load[hmax]).mean() * 100), 1),
            "netload_pctile_jj": round(
                float((netload[jj] < netload[hmax]).mean() * 100), 1
            ),
            "drybulb_pctile_jj": round(
                float((iso_t[jj] < iso_t[hmax]).mean() * 100), 1
            ),
            "solar_mw": round(float(sol_a[hmax]), 0),
            "solar_mean_all_jun_jul_mw": round(float(sol_a[jj].mean()), 0),
        }

        y["hours"] = rows
        y["jun_jul_peaks_for_reference"] = {
            "max_load_mw": round(float(load[jj].max()), 0),
            "max_netload_mw": round(float(netload[jj].max()), 0),
            "max_iso_drybulb_c": round(float(iso_t[jj].max()), 1),
        }
        report["years"][str(year)] = y

    # ---- G-D: the claim-by-claim verdict, decision rules fixed in the PREREG -
    d25 = report["years"]["2025"]
    obj25 = d25["g_a_g_b_driver_contrast"]["obj_hours_REPAIRED"]
    top25 = d25["g_a_g_b_driver_contrast"]["top_gross_load_hours"]
    jj25 = d25["g_a_g_b_driver_contrast"]["all_jun_jul"]
    r25 = d25["g_a_mean_ranks"]["repaired"]
    o25 = d25["g_c_overlap_with_driver_extremes"]["repaired"]
    load_gap = top25["load_mw"] - obj25["load_mw"]
    nl_gap = top25["netload_mw"] - obj25["netload_mw"]
    ramp_excess = obj25["netload_3h_ramp_mw"] - jj25["netload_3h_ramp_mw"]
    e25 = report["years"]["2025"]["g_e_location_recheck"]
    n_below_all = sum(
        report["years"][str(y)]["g_e_location_recheck"]["n_zones_below_anchor"]
        for y in YEARS
    )
    n_zones_all = sum(
        report["years"][str(y)]["g_e_location_recheck"]["n_zones"] for y in YEARS
    )

    def _verdict(survives: bool, refuted: bool) -> str:
        return "SURVIVES" if survives else ("REFUTED" if refuted else "PARTLY")

    c3 = _verdict(load_gap >= 8000 and nl_gap <= 4000, load_gap < 8000)
    c4 = _verdict(obj25["solar_mw"] <= 3500, obj25["solar_mw"] > 6000)
    c5 = _verdict(
        o25["n_also_in_top_load_hours"] == 0, o25["n_also_in_top_load_hours"] >= 2
    )
    c6 = _verdict(
        o25["n_also_in_top_drybulb_hours"] == 0, o25["n_also_in_top_drybulb_hours"] >= 2
    )
    c7 = _verdict(
        o25["n_also_in_top_netload_hours"] <= 6, o25["n_also_in_top_netload_hours"] >= 9
    )
    c8 = _verdict(
        r25["netload_pctile_in_jun_jul"] >= 90.0
        and r25["netload_pctile_in_jun_jul"] > r25["load_pctile_in_jun_jul"],
        r25["netload_pctile_in_jun_jul"] < 90.0
        or r25["netload_pctile_in_jun_jul"] < r25["load_pctile_in_jun_jul"],
    )
    c10 = _verdict(ramp_excess >= 2000, ramp_excess < 2000)
    ge = (
        "SURVIVES"
        if (n_below_all >= 15 and (e25["mean_gap_c"] or 0) < 0)
        else (
            "REFUTED"
            if n_below_all <= 9 or (e25["mean_gap_c"] or 0) >= 0
            else "WEAKENED"
        )
    )

    report["g_d_verdicts_on_miso203_section8"] = {
        "decision_rules": "fixed in PREREG §3 G-D before any statistic was computed",
        "C3_load_vs_netload_gap": {
            "claim": "11.6 GW less gross load, but only 2.2 GW less net load",
            "load_gap_mw": round(float(load_gap), 0),
            "netload_gap_mw": round(float(nl_gap), 0),
            "miso203_load_gap_mw": 11572,
            "miso203_netload_gap_mw": 2205,
            "verdict": c3,
        },
        "C4_solar_collapse": {
            "claim": "solar collapses 11,435 -> 1,859 MW",
            "obj_solar_mw": obj25["solar_mw"],
            "top_load_solar_mw": top25["solar_mw"],
            "miso203_obj_solar_mw": 1859,
            "verdict": c4,
        },
        "C5_zero_top_load_hours": {
            "claim": "zero of 15 are top-15 load hours",
            "overlap": o25["n_also_in_top_load_hours"],
            "verdict": c5,
        },
        "C6_zero_top_drybulb_hours": {
            "claim": "zero of 15 are top-15 dry-bulb hours",
            "overlap": o25["n_also_in_top_drybulb_hours"],
            "verdict": c6,
        },
        "C7_four_top_netload_hours": {
            "claim": "only 4 of 15 are top-15 net-load hours",
            "overlap": o25["n_also_in_top_netload_hours"],
            "verdict": c7,
        },
        "C8_netload_object_not_load_object": {
            "claim": "net load p94.3 > load p88.4",
            "netload_pctile": r25["netload_pctile_in_jun_jul"],
            "load_pctile": r25["load_pctile_in_jun_jul"],
            "verdict": c8,
        },
        "C10_evening_netload_ramp": {
            "claim": "the tail is an EVENING NET-LOAD RAMP",
            "obj_ramp_mw": obj25["netload_3h_ramp_mw"],
            "all_jun_jul_ramp_mw": jj25["netload_3h_ramp_mw"],
            "excess_mw": round(float(ramp_excess), 0),
            "verdict": c10,
        },
        "G_E_location_argument": {
            "claim": (
                "any capability-removal mechanism keyed to heat or peak load is "
                "aimed at hours the object is not in"
            ),
            "n_zone_years_below_anchor": n_below_all,
            "n_zone_years": n_zones_all,
            "mean_gap_2025_c": e25["mean_gap_c"],
            "verdict": ge,
        },
        "inherited_from_miso204_not_readjudicated": {
            "C1_13_of_15_in_h18_21": "ALREADY CORRECTED to 4/15 (miso-204 §6.5)",
            "C2_monotone_migration_14.4_17.1_18.3": (
                "ALREADY CORRECTED to 11.67 -> 15.73 -> 15.87: one large step then FLAT"
            ),
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}")
    for yr in YEARS:
        d = report["years"][str(yr)]
        n1 = d["n1_reproduces_miso204_object_set"]
        print(
            f"{yr}: N-1 reproduces={n1['reproduces_miso204']} "
            f"(hod {n1['mean_hour_of_day']} vs {n1['miso204_mean_hour_of_day']}), "
            f"N-2 reproduces={d['n2_comparison_set_unchanged']['reproduces_exactly']}"
        )
    print(json.dumps(report["g_d_verdicts_on_miso203_section8"], indent=1))


if __name__ == "__main__":
    main()
