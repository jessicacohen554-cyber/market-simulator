"""ercot-240: root-cause adjudication of the event-hour demand gap (zero-solve).

Charter: FINDING-ercot239-missedevents-phase0-2026-08-30.md section 6 OBJECT 2
(owner 2026-08-30 PM charter) — the +651..+873 MW EIA-930-vs-model demand gap
in 12 of the 14 missed-event 2023 hours. Candidates measured, per
``docs/PRECOMMIT-ercot240-eventhour-demandgap-2026-08-30.md`` (pushed and
blob-verified before this probe ran):

* (d) comparison-frame identity — the gap IS the netted DC-tie import the
  demand loader folds into served demand (M-1);
* (b) EIA-930-vs-MIS settlement boundary — ``Demand`` vs the native-load
  record (M-2);
* (c) weather-hour alignment — lag scans by DST regime + the shares-parser
  wall-clock offset (M-3);
* (a) 4CP / load-resource response in the demand source (M-4).

ZERO-SOLVE. Reads only committed artifacts and raw measured inputs: the
keeper sidecar ``results/calibration/ercot236_k33_clip/hourly/system_2023.parquet``,
the EIA-930 wide extract ``data/raw/eia-930-hourly/ERCO hourly.parquet``, the
ERCOT MIS native-load record
``data/raw/zone-specific-demand/ERCOT_Native_Load_2023.xlsx`` (NP3-565-CD),
the committed actuals parquet (RT price, conditioning only), and the
committed ercot-239 JSON. The model demand series is recomputed through the
engine's own loader (``market_sim.data.eia930.demand.load_demand`` with the
keeper's exact kwargs) and gated against the sidecar (V-1), so the
decomposition is of the keeper's own input. Model/actual price constructions
are byte-identical to ``scripts/probes/ercot239_missedevents_phase0.py``.

Run:
    python scripts/probes/ercot240_eventhour_demandgap.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot236_k33_clip"
ACTUALS = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
EIA_WIDE = REPO / "data" / "raw" / "eia-930-hourly" / "ERCO hourly.parquet"
NATIVE_XLSX = (
    REPO / "data" / "raw" / "zone-specific-demand" / "ERCOT_Native_Load_2023.xlsx"
)
E239_JSON = REPO / "results" / "calibration" / "ercot239_missedevents_phase0.json"
OUT_JSON = REPO / "results" / "calibration" / "ercot240_eventhour_demandgap.json"

#: The committed 14-hour missed-event family (ercot-239 V-0 population).
EXPECT_HOURS = sorted(
    [2058, 2971, 4623, 4626, 5369, 5484, 5777, 5943, 5945, 6399, 7001, 7145, 7480]
    + [4578]
)

#: Precommit section 3 fixed ex-ante tolerances (MW).
IDENT_TOL_MW = 25.0
IDENT_REFUTE_MW = 100.0
MATERIAL_MW = 300.0
V1_TOL_MW = 0.5

#: M-3(ii) local best-lag construction: lags scanned, context window half-width.
LOCAL_LAGS = range(-3, 4)
LOCAL_WINDOW_H = 36

#: Non-leap cumulative month-start hours (ercot-239 convention).
_CUM = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24

#: Native weather-zone column -> EIA-930 ERCO ``Subregion`` column (M-2 panel).
_SUBREGION_MAP = {
    "COAST": "Subregion COAS",
    "EAST": "Subregion EAST",
    "FWEST": "Subregion FWES",
    "NORTH": "Subregion NRTH",
    "NCENT": "Subregion NCEN",
    "SOUTH": "Subregion SOUT",
    "SCENT": "Subregion SCEN",
    "WEST": "Subregion WEST",
}


def _series() -> tuple[np.ndarray, np.ndarray]:
    """(model lw price NaN->0, actual rt) for 2023, len 8760 — ercot-239 verbatim."""
    df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    rng = range(8760)
    m = np.nan_to_num((num / den).reindex(rng).to_numpy(float))
    a = pd.read_parquet(ACTUALS)
    a = a[a["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    return m, a


def _eia_hourly() -> pd.DataFrame:
    """EIA-930 wide ERCO rows on the model's non-leap local-year 2023 clock.

    ercot-239 verbatim: EIA-930 stamps hours as hour-ending, so a row belongs
    to the local date one hour before its local timestamp; ordered by UTC.
    Positional index = hour-of-year 0..8759.
    """
    df = pd.read_parquet(EIA_WIDE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    local = utc.dt.tz_convert("America/Chicago").dt.tz_localize(None)
    hour_ending = local - pd.Timedelta(hours=1)
    keep = (hour_ending.dt.year == 2023) & ~(
        (hour_ending.dt.month == 2) & (hour_ending.dt.day == 29)
    )
    out = df[keep].assign(_utc=utc[keep]).sort_values("_utc").reset_index(drop=True)
    assert len(out) == 8760, f"EIA-930 local-2023 rows = {len(out)} != 8760"
    return out


def _sidecar_demand() -> np.ndarray:
    """Keeper sidecar per-hour system demand (P1, sum of zones), len 8760."""
    df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    s = df.groupby("hour")["demand"].sum().reindex(range(8760))
    assert not s.isna().any(), "sidecar demand has missing hours"
    return s.to_numpy(float)


def _loader_demand() -> np.ndarray:
    """The engine's own demand input under the keeper's exact demand kwargs."""
    from market_sim.data.eia930.demand import load_demand

    zonal = load_demand(
        "ERCOT",
        2023,
        td_loss_factor=0.0,
        include_interchange=True,
        ercot_tie_zonal_interchange=True,
    )
    return zonal.sum(axis=0)


def _native_frame(eia: pd.DataFrame) -> pd.DataFrame:
    """Native-load rows tz-joined onto the 930 frame's positional clock.

    Precommit section 2 join convention: parse the hour-ending labels
    (``MM/DD/YYYY HH:00``, HE 01-24, fall-back duplicate marked ``DST``),
    tz-localize America/Chicago (plain fall-back ``02:00`` = first/CDT pass,
    ``02:00 DST`` = second/CST pass), convert to UTC hour-ending, and require
    an exact 1:1 match with the extract's ``UTC time`` axis. Returns the
    native frame reordered to positional hour-of-year 0..8759, with a
    ``wall_hoy`` column carrying the shares-parser month/day/hour formula
    index for M-3(iii).
    """
    x = pd.read_excel(NATIVE_XLSX)
    he = x["Hour Ending"].astype(str)
    parts = he.str.split(" ", n=1, expand=True)
    date = pd.to_datetime(parts[0], format="mixed", dayfirst=False)
    hh = parts[1].str.slice(0, 2).astype(int)
    dst_flag = parts[1].str.contains("DST", na=False)
    # Hour-ending naive local stamp; HE 24:00 rolls to next-day 00:00.
    # Localize the HOUR-BEGINNING stamps: the hour-ending label of the interval
    # that ends exactly AT a DST transition is not a resolvable wall time (it
    # is skipped in spring and lands on the transition instant in fall), while
    # every interval-BEGINNING stamp exists once — except the fall-back
    # duplicate, which is genuinely ambiguous and resolved by the file's own
    # marker (plain '02:00' = first/CDT pass, '02:00 DST' = second/CST pass).
    # The hour-ending UTC axis is then the localized beginning + 1 h, and the
    # monotone/axis-equality gates below verify the join end-to-end
    # (precommit section 2 join convention).
    naive_hb = date + pd.to_timedelta(hh - 1, "h")
    localized = naive_hb.dt.tz_localize(
        "America/Chicago", ambiguous=(~dst_flag).to_numpy(), nonexistent="raise"
    )
    utc_he = localized.dt.tz_convert("UTC") + pd.Timedelta(hours=1)
    diffs = utc_he.diff().dropna()
    assert (diffs == pd.Timedelta(hours=1)).all(), (
        "native UTC axis not strictly +1h monotone"
    )
    eia_utc = pd.DatetimeIndex(pd.to_datetime(eia["UTC time"], utc=True))
    assert len(x) == len(eia_utc) == 8760, (
        f"native rows {len(x)} vs frame {len(eia_utc)}"
    )
    assert (pd.DatetimeIndex(utc_he) == eia_utc).all(), (
        "native UTC axis != EIA-930 frame UTC axis"
    )
    out = x.copy()
    # Shares-parser formula index (scripts/data/curate_zonal_shares.py
    # parse_ercot_shares): wall-clock month/day/(HE-1) on the non-leap grid.
    out["wall_hoy"] = (
        np.array(_CUM)[date.dt.month.to_numpy() - 1]
        + (date.dt.day.to_numpy() - 1) * 24
        + (hh.to_numpy() - 1)
    )
    out["utc_he"] = utc_he
    return out.reset_index(drop=True)


def _pctl(vals: np.ndarray, x: float) -> float:
    """Percentile of x within vals (NaN-dropped)."""
    v = vals[~np.isnan(vals)]
    return round(float((v <= x).mean() * 100.0), 1)


def _dist(v: np.ndarray) -> dict:
    """Compact NaN-aware distribution summary."""
    return {
        "mean": round(float(np.nanmean(v)), 1),
        "p5": round(float(np.nanpercentile(v, 5)), 1),
        "p50": round(float(np.nanpercentile(v, 50)), 1),
        "p95": round(float(np.nanpercentile(v, 95)), 1),
    }


def _best_lag_corr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> dict:
    """Correlation of a[t] vs b[t+lag] over mask hours, lags -3..+3."""
    out = {}
    idx = np.where(mask)[0]
    idx = idx[(idx >= 3) & (idx <= 8756)]
    for lag in LOCAL_LAGS:
        x, y = a[idx], b[idx + lag]
        keep = np.isfinite(x) & np.isfinite(y)
        out[str(lag)] = round(float(np.corrcoef(x[keep], y[keep])[0, 1]), 4)
    best = max(out, key=out.get)
    return {"corr": out, "best_lag": int(best)}


def main() -> None:
    # ---- V-0: population identity (precommit section 1) ----
    m, a = _series()
    pop = sorted(int(h) for h in np.where((m < 200.0) & (a >= 500.0))[0])
    assert pop == EXPECT_HOURS, f"V-0 FAIL population {pop} != {EXPECT_HOURS}"
    e239 = json.loads(E239_JSON.read_text())
    assert sorted(r["h"] for r in e239["rows"]) == EXPECT_HOURS, (
        "V-0 FAIL ercot-239 row list mismatch"
    )

    eia = _eia_hourly()
    d930 = eia["Demand"].to_numpy(float)
    ti = eia["Total interchange"].to_numpy(float)
    netgen = eia["Net generation"].to_numpy(float)
    months = np.searchsorted(_CUM, np.arange(8760), side="right")
    ev = np.array(EXPECT_HOURS)
    assert np.isfinite(d930[ev]).all() and np.isfinite(ti[ev]).all(), (
        "NaN Demand/TI at an event hour"
    )

    # ---- V-1: loader identity (precommit section 1) ----
    d_side = _sidecar_demand()
    d_load = _loader_demand()
    v1_max = float(np.abs(d_load - d_side).max())
    assert v1_max <= V1_TOL_MW, f"V-1 FAIL max |loader - sidecar| = {v1_max:.3f} MW"

    # ---- M-1: identity decomposition (candidate d) ----
    gap = d930 - d_side
    r = gap + ti
    fin = np.isfinite(r)
    abs_r = np.abs(r[fin])
    gt1 = np.where(fin & (np.abs(r) > 1.0))[0]
    gt25 = np.where(fin & (np.abs(r) > 25.0))[0]
    identity_share = 1.0 - float(np.abs(r[ev]).sum() / np.abs(gap[ev]).sum())
    m1 = {
        "residual_abs": {
            "p50": round(float(np.percentile(abs_r, 50)), 2),
            "p95": round(float(np.percentile(abs_r, 95)), 2),
            "p99": round(float(np.percentile(abs_r, 99)), 2),
            "max": round(float(abs_r.max()), 2),
        },
        "hours_abs_gt_1mw": int(len(gt1)),
        "hours_abs_gt_25mw": int(len(gt25)),
        "gt_25mw_hours": [int(h) for h in gt25[:20]],
        "nan_hours_930": int((~np.isfinite(d930)).sum() + (~np.isfinite(ti)).sum()),
        "identity_share_event_hours": round(identity_share, 4),
        "event_hours_within_tol": int((np.abs(r[ev]) <= IDENT_TOL_MW).sum()),
        "event_hours_refuting": int((np.abs(r[ev]) > IDENT_REFUTE_MW).sum()),
        "year_gap_mean_vs_mean_import": {
            "gap_mean": round(float(np.nanmean(gap)), 1),
            "minus_ti_mean": round(float(-np.nanmean(ti)), 1),
        },
    }

    # ---- M-2: settlement-boundary wedge (candidate b) ----
    native = _native_frame(eia)
    nat_tot = native["ERCOT"].to_numpy(float)
    w = d930 - nat_tot
    local_he = pd.DatetimeIndex(native["utc_he"]).tz_convert("America/Chicago")
    hodl = ((local_he - pd.Timedelta(hours=1)).hour).to_numpy()  # interval-beginning
    is_cdt = np.array(
        [off == pd.Timedelta(hours=-5) for off in local_he.map(lambda t: t.utcoffset())]
    )
    deciles = np.searchsorted(
        np.nanpercentile(nat_tot, np.arange(10, 100, 10)), nat_tot, side="right"
    )
    ctrl_rows = {}
    for h in EXPECT_HOURS:
        hd = np.abs(((hodl - hodl[h]) + 12) % 24 - 12)
        ctrl = (
            (months == months[h])
            & (hd <= 2)
            & (np.abs(nat_tot - nat_tot[h]) <= 0.03 * nat_tot[h])
            & (a < 100.0)
            & ~np.isin(np.arange(8760), ev)
        )
        ctrl_rows[h] = np.where(ctrl)[0]
    sub_panel = {}
    for nz, sz in _SUBREGION_MAP.items():
        dz = native[nz].to_numpy(float) - eia[sz].to_numpy(float)
        sub_panel[nz] = {
            "median_abs": round(float(np.nanmedian(np.abs(dz))), 1),
            "max_abs": round(float(np.nanmax(np.abs(dz))), 1),
            "coverage_hours": int(np.isfinite(dz).sum()),
        }
    sub_sum = sum(eia[sz].to_numpy(float) for sz in _SUBREGION_MAP.values())
    m2 = {
        "wedge_year": _dist(w),
        "wedge_by_month": {
            int(mo): round(float(np.nanmedian(w[months == mo])), 1)
            for mo in range(1, 13)
        },
        "wedge_by_native_decile": {
            int(d): round(float(np.nanmedian(w[deciles == d])), 1) for d in range(10)
        },
        "event_wedge_median": round(float(np.nanmedian(w[ev])), 1),
        "event_wedge_abs_median": round(float(np.nanmedian(np.abs(w[ev]))), 1),
        "subregion_vs_native_zone": sub_panel,
        "subregion_sum_vs_demand": {
            "median_abs": round(float(np.nanmedian(np.abs(sub_sum - d930))), 1),
            "max_abs": round(float(np.nanmax(np.abs(sub_sum - d930))), 1),
        },
        "native_vs_930_corr": round(
            float(
                np.corrcoef(
                    nat_tot[np.isfinite(nat_tot) & np.isfinite(d930)],
                    d930[np.isfinite(nat_tot) & np.isfinite(d930)],
                )[0, 1]
            ),
            5,
        ),
    }

    # ---- M-3: weather-hour alignment (candidate c) ----
    regimes = {
        "cst_early": ~is_cdt & (np.arange(8760) < 4000),
        "cdt": is_cdt,
        "cst_late": ~is_cdt & (np.arange(8760) >= 4000),
        "full_year": np.ones(8760, bool),
    }
    m3 = {
        "model_vs_930": {
            k: _best_lag_corr(d_side, d930, msk) for k, msk in regimes.items()
        },
        "native_vs_930": {
            k: _best_lag_corr(nat_tot, d930, msk) for k, msk in regimes.items()
        },
        "shares_parser_offset": {
            reg: {
                str(int(off)): int(cnt)
                for off, cnt in zip(
                    *np.unique(
                        (native["wall_hoy"].to_numpy() - np.arange(8760))[msk],
                        return_counts=True,
                    )
                )
            }
            for reg, msk in (("cst", ~is_cdt), ("cdt", is_cdt))
        },
    }
    ev_local, ramp_rows = {}, {}
    for h in EXPECT_HOURS:
        wmask = np.zeros(8760, bool)
        wmask[max(0, h - LOCAL_WINDOW_H) : min(8760, h + LOCAL_WINDOW_H + 1)] = True
        ev_local[h] = _best_lag_corr(nat_tot, d930, wmask)["best_lag"]
        back = d930[h] - d930[h - 1] if h >= 1 else np.nan
        fwd = d930[h + 1] - d930[h] if h <= 8758 else np.nan
        ramp_rows[h] = {
            "ramp_back": round(float(back), 0),
            "ramp_fwd": round(float(fwd), 0),
            "gap_over_ramp_back": round(float(gap[h] / back), 2) if back else None,
            "gap_over_ramp_fwd": round(float(gap[h] / fwd), 2) if fwd else None,
        }
    n_c_hours = sum(
        1
        for h in EXPECT_HOURS
        if ev_local[h] != 0
        and any(
            abs(ramp_rows[h][f"ramp_{d}"]) >= MATERIAL_MW
            and ramp_rows[h][f"gap_over_ramp_{d}"] is not None
            and 0.5 <= abs(gap[h] / ramp_rows[h][f"ramp_{d}"]) <= 2.0
            for d in ("back", "fwd")
        )
    )
    m3["event_local_best_lag"] = {int(h): int(v) for h, v in ev_local.items()}
    m3["event_lag_nonzero_with_ramp_support"] = n_c_hours

    # ---- M-4: 4CP / load-resource response (candidate a) ----
    daily_peak = pd.Series(nat_tot).groupby(np.arange(8760) // 24).max()
    top_days = {
        mo: set(
            daily_peak[
                np.unique(np.where(months == mo)[0] // 24)
            ].nlargest(8).index
        )
        for mo in (6, 7, 8, 9)
    }
    in_w = np.array(
        [
            months[t] in top_days
            and (t // 24) in top_days[months[t]]
            and hodl[t] in (15, 16, 17)
            for t in range(8760)
        ]
    )
    same_cell = np.array(
        [months[t] in (6, 7, 8, 9) and hodl[t] in (15, 16, 17) for t in range(8760)]
    )
    dip_n = np.full(8760, np.nan)
    dip_d = np.full(8760, np.nan)
    dip_n[1:-1] = 0.5 * (nat_tot[:-2] + nat_tot[2:]) - nat_tot[1:-1]
    dip_d[1:-1] = 0.5 * (d930[:-2] + d930[2:]) - d930[1:-1]
    price_bins = {
        "lt_50": a < 50.0,
        "50_100": (a >= 50.0) & (a < 100.0),
        "100_500": (a >= 100.0) & (a < 500.0),
        "ge_500": a >= 500.0,
    }
    m4 = {
        "wedge_4cp_window_median": round(float(np.nanmedian(w[in_w])), 1),
        "wedge_nonwindow_samecell_median": round(
            float(np.nanmedian(w[same_cell & ~in_w])), 1
        ),
        "window_hours": int(in_w.sum()),
        "wedge_by_price_bin": {
            k: {
                "median": round(float(np.nanmedian(w[msk])), 1),
                "n": int(msk.sum()),
            }
            for k, msk in price_bins.items()
        },
    }

    # ---- M-5: context panel (report-only) ----
    resid930 = netgen - ti - d930
    m5 = {
        "identity_930_abs": {
            "p50": round(float(np.nanmedian(np.abs(resid930))), 1),
            "p95": round(float(np.nanpercentile(np.abs(resid930), 95)), 1),
        },
    }

    rows = []
    for h in EXPECT_HOURS:
        ctrl = ctrl_rows[h]
        w_ctrl = float(np.nanmedian(w[ctrl])) if len(ctrl) else np.nan
        rows.append(
            {
                "h": int(h),
                "month": int(months[h]),
                "hod_local": int(hodl[h]),
                "gap_mw": round(float(gap[h]), 1),
                "minus_ti_mw": round(float(-ti[h]), 1),
                "identity_residual_mw": round(float(r[h]), 1),
                "wedge_930_minus_native_mw": round(float(w[h]), 1)
                if np.isfinite(w[h])
                else None,
                "wedge_ctrl_median_mw": round(w_ctrl, 1)
                if np.isfinite(w_ctrl)
                else None,
                "wedge_excess_mw": round(float(w[h] - w_ctrl), 1)
                if np.isfinite(w[h]) and np.isfinite(w_ctrl)
                else None,
                "n_controls": int(len(ctrl)),
                "dip_native_mw": round(float(dip_n[h]), 1),
                "dip_930_mw": round(float(dip_d[h]), 1),
                "local_best_lag": int(ev_local[h]),
                "ramps": ramp_rows[h],
                "ties_mw": {
                    ba: round(float(eia[ba].iloc[h]), 1)
                    for ba in ("CEN", "CFE", "SWPP")
                    if pd.notna(eia[ba].iloc[h])
                },
                "import_pctl_in_controls": _pctl(-ti[ctrl], float(-ti[h]))
                if len(ctrl)
                else None,
                "identity_930_residual_mw": round(float(resid930[h]), 1),
            }
        )

    ev_w = np.array([row["wedge_excess_mw"] or 0.0 for row in rows])
    adjudication = {
        "A_d_identity_carries": bool(
            m1["event_hours_within_tol"] >= 12
            and m1["identity_share_event_hours"] >= 0.95
        ),
        "A_d_refuted": bool(m1["event_hours_refuting"] > 0),
        "A_b_carries": bool(
            abs(m2["event_wedge_median"]) >= MATERIAL_MW
            and abs(float(np.nanmedian(ev_w))) >= MATERIAL_MW
        ),
        "A_c_carries": bool(
            any(
                m3[k][reg]["best_lag"] != 0
                for k in ("model_vs_930", "native_vs_930")
                for reg in ("cst_early", "cdt", "cst_late", "full_year")
            )
            or n_c_hours >= 7
        ),
        "A_a_carries": bool(
            abs(
                m4["wedge_4cp_window_median"]
                - m4["wedge_nonwindow_samecell_median"]
            )
            >= MATERIAL_MW
            or abs(
                m4["wedge_by_price_bin"]["ge_500"]["median"]
                - m4["wedge_by_price_bin"]["lt_50"]["median"]
            )
            >= MATERIAL_MW
        ),
    }

    res = {
        "session": "ercot-240",
        "keeper": "2026-08-25-236-swcap-clip-k33",
        "precommit": "docs/PRECOMMIT-ercot240-eventhour-demandgap-2026-08-30.md",
        "v0_identity": {"hours": EXPECT_HOURS, "pass": True},
        "v1_loader_identity_max_abs_mw": round(v1_max, 4),
        "conventions": {
            "gap": "EIA-930 Demand (raw extract) minus keeper sidecar system demand",
            "interchange_sign": "EIA-930: positive = net export",
            "native_join": (
                "hour-ending labels tz-localized America/Chicago (fall-back "
                "'02:00 DST' = second/CST pass) -> UTC, matched 1:1 to the "
                "extract's UTC time axis"
            ),
            "local_best_lag": (
                f"corr over +-{LOCAL_WINDOW_H} h context window, lags -3..+3"
            ),
            "wedge": "w = 930 Demand - native ERCOT total (tz-joined clock)",
            "controls": (
                "same month, local hod +-2, native load +-3%, actual RT < $100, "
                "event hours excluded"
            ),
            "4cp_window": "Jun-Sep top-8 native-peak days per month, HE 16-18",
        },
        "thresholds": {
            "identity_tol_mw": IDENT_TOL_MW,
            "identity_refute_mw": IDENT_REFUTE_MW,
            "material_mw": MATERIAL_MW,
            "v1_tol_mw": V1_TOL_MW,
        },
        "m1_identity": m1,
        "m2_boundary": m2,
        "m3_alignment": m3,
        "m4_response": m4,
        "m5_context": m5,
        "rows": rows,
        "adjudication": adjudication,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    headline = {
        "v1_max_abs_mw": res["v1_loader_identity_max_abs_mw"],
        "m1": {
            "identity_share": m1["identity_share_event_hours"],
            "within_tol": m1["event_hours_within_tol"],
            "refuting": m1["event_hours_refuting"],
            "year_hours_abs_gt_1mw": m1["hours_abs_gt_1mw"],
        },
        "m2": {
            "event_wedge_median": m2["event_wedge_median"],
            "year_wedge_p50": m2["wedge_year"]["p50"],
        },
        "m3_best_lags": {
            k: {reg: m3[k][reg]["best_lag"] for reg in regimes}
            for k in ("model_vs_930", "native_vs_930")
        },
        "m4": m4,
        "adjudication": adjudication,
        "per_hour": [
            {
                "h": row["h"],
                "gap": row["gap_mw"],
                "-TI": row["minus_ti_mw"],
                "r": row["identity_residual_mw"],
                "w": row["wedge_930_minus_native_mw"],
                "w_excess": row["wedge_excess_mw"],
            }
            for row in rows
        ],
    }
    print(json.dumps(headline, indent=1))


if __name__ == "__main__":
    main()
