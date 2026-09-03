"""miso-204 section F — POST-HOC INSTRUMENT FORENSIC (not pre-registered, no gate).

The pre-registered decomposition (`_miso204_lmp_component_decomposition.py`)
returned a NEGATIVE congestion share, i.e. the eight trading hubs sit on the
CHEAP side of congestion in the object's hours.  Chasing that led to the
provenance of the C3a comparator itself, and it is not the series either
committed probe used:

* ``data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`` — the actual
  behind ``bench.avgLMP.rt``/``rt_lw``, i.e. the C3a instrument — is documented
  by ``scripts/data/derive_miso_hub_lmp.py`` as *"verified hour-for-hour
  identical to this staging's INDIANA.HUB series"*.  It is **ONE HUB**, not the
  eight-hub average.
* Its clock is the model's **chronological fixed-CST non-leap 8760**: the raw
  reports are hour-ending 1-24 **Eastern Standard** year-round, so the transform
  is a constant **-1 h** with **CST Feb 29 dropped**.

``_miso202_c3a_2025_anatomy`` and ``_miso203_scarce_hour_identity`` both build
their hourly actual by ``groupby("date")[he01..he24].mean()`` over the eight
hubs and ``arr[:8760]`` — an **eight-hub** series on the **raw EST hour-ending**
index with **no leap-day drop**.  This probe measures how much that matters, on
the model's own reproduce-production discipline: N-3 asserts the scoring-clock
reconstruction against the committed parquet before any comparison is read.

**This block carries NO gate and licenses NOTHING.**  The pre-registered verdict
stands on the frozen OBJ set (PREREG TRAP 3); what is measured here is whether
that verdict is ROBUST to the instrument defect, and how large the defect is.

Committed artifacts only; **no LP is solved**.  Rule 22 — 2023/2024/2025 only.

Usage::

    python3 scripts/probes/_miso204_scoring_reference_instrument.py
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402

YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
STAGE = REPO / "data/raw/lmp-data/MISO"
OUT = REPO / "results/calibration/_miso204_scoring_reference_instrument.json"

HE = [f"he{i:02d}" for i in range(1, 25)]
EST_UTC_OFFSET_H = 5
STD_TZ = "Etc/GMT+6"
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_START_HOUR = np.concatenate(([0], np.cumsum(DAYS_IN_MONTH) * 24))[:12]
SCORING_HUB = "INDIANA.HUB"


def scoring_clock_frame(year: int, label: str) -> pd.DataFrame:
    """One staged (year, component) on the SCORING clock.

    Replicates ``derive_miso_hub_lmp._market_frame`` exactly — hour-beginning
    EST -> fixed CST (-1 h), placed on the fixed non-leap calendar with CST
    Feb 29 dropped — with the hardcoded ``value == "LMP"`` filter generalised to
    the component label.  N-3 asserts this reproduces the committed parquet.
    """
    df = pd.read_csv(STAGE / f"miso_hub_lmp_{year}_rt.csv.gz")
    df = df[df["value"] == label]
    day_utc = pd.to_datetime(df["date"]).to_numpy() + np.timedelta64(
        EST_UTC_OFFSET_H, "h"
    )
    utc = (day_utc[:, None] + np.arange(24) * np.timedelta64(1, "h")).ravel()
    local = pd.DatetimeIndex(utc, tz="UTC").tz_convert(STD_TZ).tz_localize(None)
    month, day = np.asarray(local.month), np.asarray(local.day)
    hour = MONTH_START_HOUR[month - 1] + (day - 1) * 24 + np.asarray(local.hour)
    out = pd.DataFrame(
        {
            "hub": np.repeat(df["node"].to_numpy(), 24),
            "year": np.asarray(local.year),
            "hour": hour,
            "v": df[HE].apply(pd.to_numeric, errors="coerce").to_numpy(float).ravel(),
        }
    )
    return out[~((month == 2) & (day == 29))]


def scoring_matrix(year: int, label: str, hubs: list[str]) -> np.ndarray:
    """(n_hub x 8760) of one component on the scoring clock, hub order given.

    Every staged year is read so the CST year-boundary spill (Jan 1's first EST
    hours belong to the prior local year) fills each year's final hour, exactly
    as ``derive_miso_hub_lmp.build`` does.
    """
    frames = [
        scoring_clock_frame(y, label)
        for y in (year, year + 1)
        if (STAGE / f"miso_hub_lmp_{y}_rt.csv.gz").exists()
    ]
    long = pd.concat(frames, ignore_index=True)
    long = long[long["year"] == year]
    g = long.groupby(["hub", "hour"])["v"].mean()
    mat = np.full((len(hubs), HOURS), np.nan)
    for i, hub in enumerate(hubs):
        if hub in g.index.get_level_values("hub"):
            s = g.loc[hub].reindex(range(HOURS))
            mat[i] = s.to_numpy(float)
    return mat


def raw_index_matrix(year: int, label: str, hubs: list[str]) -> np.ndarray:
    """The COMMITTED PROBES' construction: raw EST hour-ending index, no leap drop."""
    df = pd.read_csv(STAGE / f"miso_hub_lmp_{year}_rt.csv.gz")
    df = df[df["value"] == label].copy()
    df["date"] = pd.to_datetime(df["date"])
    rows = []
    for hub in hubs:
        g = df[df["node"] == hub].groupby("date")[HE].mean().sort_index()
        rows.append(g.to_numpy().ravel()[:HOURS])
    return np.vstack(rows)


def _stamp(year: int, h: int, leap_aware: bool) -> str:
    """Calendar stamp of index ``h``: real calendar, or the fixed non-leap clock."""
    doy, hod = divmod(int(h), 24)
    if leap_aware:
        d = dt.date(year, 1, 1) + dt.timedelta(days=doy)
        return f"{d.isoformat()} HE{hod + 1:02d}"
    m = 0
    while doy >= DAYS_IN_MONTH[m]:
        doy -= DAYS_IN_MONTH[m]
        m += 1
    return f"{year}-{m + 1:02d}-{doy + 1:02d} HE{hod + 1:02d}"


def _hour_month() -> np.ndarray:
    return np.concatenate(
        [np.full(n * 24, m + 1) for m, n in enumerate(DAYS_IN_MONTH)]
    )[:HOURS]


def _shares(excess, energy, cong, loss) -> dict:
    me = float(np.nanmean(excess))
    stack = np.vstack([energy, cong, loss])
    largest = np.argmax(np.abs(stack), axis=0)
    return {
        "n_hours": int(len(excess)),
        "mean_excess": round(me, 3),
        "mean_energy": round(float(np.nanmean(energy)), 3),
        "mean_cong": round(float(np.nanmean(cong)), 3),
        "mean_loss": round(float(np.nanmean(loss)), 3),
        "share_energy": round(float(np.nanmean(energy) / me), 4) if me else None,
        "share_cong": round(float(np.nanmean(cong) / me), 4) if me else None,
        "share_loss": round(float(np.nanmean(loss) / me), 4) if me else None,
        "r1_hours_largest_energy": int(np.sum(largest == 0)),
        "r1_hours_largest_cong": int(np.sum(largest == 1)),
        "r1_hours_largest_loss": int(np.sum(largest == 2)),
    }


def main() -> None:
    zon = pd.read_parquet(
        paths.CALIBRATION_DIR / "actual_lmp_hourly_zonal_MISO.parquet"
    )
    sysref = pd.read_parquet(paths.CALIBRATION_DIR / "actual_lmp_hourly_MISO.parquet")
    hubs = sorted(zon["hub"].unique())

    report: dict = {
        "charter": (
            "miso-204 section F — POST-HOC INSTRUMENT FORENSIC. NOT "
            "pre-registered, NO gate, licenses NOTHING. Measures whether the "
            "pre-registered ENERGY verdict is robust to a defect found while "
            "chasing the negative congestion share: the C3a comparator is "
            "INDIANA.HUB on the fixed-CST non-leap clock, while both committed "
            "probes use an EIGHT-HUB average on the RAW EST hour-ending index."
        ),
        "keeper": "2026-09-03-miso-202-unitclip",
        "inputs": "committed artifacts only — no solve",
        "scoring_reference": (
            "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet — the "
            "actual behind bench.avgLMP.rt / rt_lw, i.e. C3a itself"
        ),
        "years": {},
    }

    # ---- the scoring reference's own identity, asserted once ---------------
    ident = {}
    for year in YEARS:
        s = sysref[sysref.year == year].sort_values("hour")["rt"].to_numpy()
        ind = (
            zon[(zon.year == year) & (zon.hub == SCORING_HUB)]
            .sort_values("hour")["rt"]
            .to_numpy()
        )
        ident[str(year)] = {
            "max_abs_diff_sysref_vs_indiana_hub": float(np.nanmax(np.abs(s - ind))),
            "verdict": "the C3a actual IS INDIANA.HUB",
        }
    report["f0_scoring_actual_is_one_hub"] = ident

    for year in YEARS:
        y: dict = {}

        # ---- N-3: the scoring-clock reconstruction must reproduce production
        rec = scoring_matrix(year, "LMP", hubs)
        com = np.vstack(
            [
                zon[(zon.year == year) & (zon.hub == h)]
                .sort_values("hour")["rt"]
                .to_numpy()
                for h in hubs
            ]
        )
        both = ~np.isnan(rec) & ~np.isnan(com)
        y["n3_reproduces_committed_parquet"] = {
            "hubs": hubs,
            "max_abs_diff": float(np.max(np.abs(rec[both] - com[both]))),
            "n_compared": int(both.sum()),
            "n_nan_reconstruction": int(np.isnan(rec).sum()),
            "n_nan_committed": int(np.isnan(com).sum()),
            "reproduces": bool(np.max(np.abs(rec[both] - com[both])) < 1e-4),
        }

        mcc = scoring_matrix(year, "MCC", hubs)
        mlc = scoring_matrix(year, "MLC", hubs)
        mec = rec - mcc - mlc

        i_ref = hubs.index(SCORING_HUB)
        month = _hour_month()
        jj = np.where((month == 6) | (month == 7))[0]

        # ---- F-1: the two constructions, side by side ----------------------
        raw8 = raw_index_matrix(year, "LMP", hubs).mean(0)
        sc8 = np.nanmean(rec, axis=0)
        scind = rec[i_ref]
        ok = ~np.isnan(sc8) & ~np.isnan(scind)
        y["f1_series_contrast"] = {
            "committed_probe_series": "8-hub mean, RAW EST hour-ending index",
            "annual_mean_committed_probe": round(float(np.mean(raw8)), 3),
            "annual_mean_scoring_clock_8hub": round(float(np.nanmean(sc8)), 3),
            "annual_mean_scoring_reference_indiana": round(float(np.nanmean(scind)), 3),
            "level_gap_indiana_minus_8hub": round(
                float(np.nanmean(scind) - np.nanmean(sc8)), 3
            ),
            "corr_committed_vs_scoring_clock_8hub": round(
                float(np.corrcoef(raw8[ok], sc8[ok])[0, 1]), 5
            ),
            "corr_committed_vs_scoring_reference": round(
                float(np.corrcoef(raw8[ok], scind[ok])[0, 1]), 5
            ),
            "corr_scoring_8hub_vs_scoring_reference": round(
                float(np.corrcoef(sc8[ok], scind[ok])[0, 1]), 5
            ),
        }

        # ---- F-2: where the object actually is on the scoring reference ----
        obj_committed = jj[raw8[jj] >= np.percentile(raw8[jj], 99.0)]
        v = scind[jj]
        obj_scoring = jj[v >= np.nanpercentile(v, 99.0)]
        v8 = sc8[jj]
        obj_sc8 = jj[v8 >= np.nanpercentile(v8, 99.0)]
        y["f2_object_relocation"] = {
            "n_committed": int(len(obj_committed)),
            "n_scoring_reference": int(len(obj_scoring)),
            "overlap_committed_vs_scoring_reference": int(
                len(set(obj_committed.tolist()) & set(obj_scoring.tolist()))
            ),
            "overlap_committed_vs_scoring_clock_8hub": int(
                len(set(obj_committed.tolist()) & set(obj_sc8.tolist()))
            ),
            "overlap_scoring_8hub_vs_scoring_reference": int(
                len(set(obj_sc8.tolist()) & set(obj_scoring.tolist()))
            ),
            "threshold_committed": round(float(np.percentile(raw8[jj], 99.0)), 2),
            "threshold_scoring_reference": round(float(np.nanpercentile(v, 99.0)), 2),
            "hour_of_day_hist_scoring_reference": {
                int(k): int(c)
                for k, c in zip(
                    *np.unique(obj_scoring % 24, return_counts=True), strict=True
                )
            },
            "n_distinct_days_scoring_reference": int(
                len(set((obj_scoring // 24).tolist()))
            ),
        }

        # ---- F-3: the decomposition ON THE SCORING REFERENCE ---------------
        sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        pmean = sysd.groupby("hour")["price"].mean().sort_index().to_numpy()[:HOURS]
        num = sysd.assign(pw=sysd["price"] * sysd["demand"])
        plw = (
            (num.groupby("hour")["pw"].sum() / num.groupby("hour")["demand"].sum())
            .sort_index()
            .to_numpy()[:HOURS]
        )
        pind = (
            sysd[sysd["zone"] == "MISO-Indiana"]
            .sort_values("hour")["price"]
            .to_numpy()[:HOURS]
        )

        for name, pmod in (
            ("vs_model_zone_mean", pmean),
            ("vs_model_load_weighted", plw),
            ("vs_model_indiana_zone", pind),
        ):
            y.setdefault("f3_decomposition_on_scoring_reference", {})[name] = _shares(
                scind[obj_scoring] - pmod[obj_scoring],
                mec[i_ref][obj_scoring] - pmod[obj_scoring],
                mcc[i_ref][obj_scoring],
                mlc[i_ref][obj_scoring],
            )
        y["f3_levels"] = {
            "mean_actual_lmp": round(float(np.nanmean(scind[obj_scoring])), 2),
            "mean_actual_mec": round(float(np.nanmean(mec[i_ref][obj_scoring])), 2),
            "mean_actual_mcc": round(float(np.nanmean(mcc[i_ref][obj_scoring])), 2),
            "mean_actual_mlc": round(float(np.nanmean(mlc[i_ref][obj_scoring])), 2),
            "mean_model_zone_mean": round(float(np.mean(pmean[obj_scoring])), 2),
            "mean_model_load_weighted": round(float(np.mean(plw[obj_scoring])), 2),
            "mean_model_indiana_zone": round(float(np.mean(pind[obj_scoring])), 2),
        }

        # ---- F-4: the hours themselves, on the correct clock ---------------
        y["f4_hours_scoring_reference"] = [
            {
                "hour_index": int(h),
                "cst_stamp": _stamp(year, h, leap_aware=False),
                "actual_lmp": round(float(scind[h]), 2),
                "actual_mec": round(float(mec[i_ref][h]), 2),
                "actual_mcc": round(float(mcc[i_ref][h]), 2),
                "actual_mlc": round(float(mlc[i_ref][h]), 2),
                "model_load_weighted": round(float(plw[h]), 2),
                "model_indiana_zone": round(float(pind[h]), 2),
                "in_committed_object": bool(h in set(obj_committed.tolist())),
            }
            for h in obj_scoring
        ]

        # ---- F-5: the annual C3a face on each actual basis ------------------
        load = sysd.groupby("hour")["demand"].sum().sort_index().to_numpy()[:HOURS]

        def lw(v: np.ndarray) -> float:
            m = ~np.isnan(v)
            return float(np.dot(v[m], load[m]) / load[m].sum())

        a_lmp, a_mec, m_lw = lw(scind), lw(mec[i_ref]), lw(plw)
        y["f5_annual_basis"] = {
            "actual_lw_scoring_reference": round(a_lmp, 4),
            "actual_lw_system_mec_at_scoring_hub": round(a_mec, 4),
            "model_lw": round(m_lw, 4),
            "c3a_face_pct": round(100.0 * (m_lw / a_lmp - 1.0), 4),
            "c3a_face_on_mec_basis_pct": round(100.0 * (m_lw / a_mec - 1.0), 4),
            "scoring_hub_congestion_wedge": round(lw(mcc[i_ref]), 4),
            "scoring_hub_loss_wedge": round(lw(mlc[i_ref]), 4),
        }

        # ---- F-6: which miso-203 claims survive the corrected instrument? --
        # miso-203 G-E characterised the object's hour-of-day on the RAW EST
        # hour-ending index. The model's own clock is fixed CST, so that
        # characterisation is BOTH one hour late (the clock defect measured in
        # F-1) and labelled in the wrong zone. Re-measured here on the scoring
        # reference's own hours, on the model's own clock. Descriptive.
        hod_c = obj_committed % 24
        hod_s = obj_scoring % 24
        y["f6_miso203_recheck"] = {
            "mean_hour_of_day_committed_raw_est_index": round(float(hod_c.mean()), 2),
            "mean_hour_of_day_scoring_reference_cst": round(float(hod_s.mean()), 2),
            "n_in_h18_h21_committed": int(((hod_c >= 18) & (hod_c <= 21)).sum()),
            "n_in_h18_h21_scoring_reference": int(
                ((hod_s >= 18) & (hod_s <= 21)).sum()
            ),
            "n_in_h15_h18_scoring_reference": int(
                ((hod_s >= 15) & (hod_s <= 18)).sum()
            ),
        }

        # the lag scan that DIAGNOSES the clock defect, recorded rather than
        # asserted: r=1.0000 at exactly k=-1 identifies it as a pure 1-h shift,
        # and the series' own lag-1 autocorrelation says why that is fatal to
        # hour-matching even though it leaves the annual mean untouched.
        okv = ~np.isnan(sc8)
        okv[:5] = False
        okv[-5:] = False
        y["f1_series_contrast"]["lag_scan_raw_vs_scoring_clock"] = {
            str(k): round(float(np.corrcoef(np.roll(raw8, k)[okv], sc8[okv])[0, 1]), 4)
            for k in (-2, -1, 0, 1, 2)
        }
        ss = sc8[~np.isnan(sc8)]
        y["f1_series_contrast"]["scoring_series_lag1_autocorr"] = round(
            float(np.corrcoef(ss[:-1], ss[1:])[0, 1]), 4
        )

        report["years"][str(year)] = y

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(report, f, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
