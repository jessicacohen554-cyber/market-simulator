"""ercot-239: Phase-0 DRIVER characterization of the 14-hour missed-event family.

ZERO-SOLVE. Reads only committed artifacts and raw measured inputs — the
keeper sidecars under ``results/calibration/ercot236_k33_clip/hourly/``, the
committed actuals ``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet``,
the EIA-930 wide extract ``data/raw/eia-930-hourly/ERCO hourly.parquet``, and
the CAMPD outage records ``data/raw/campd-unit-outages.csv`` /
``data/raw/ercot-outages.csv`` — and attributes each of the 14 entirely-missed
2023 scarcity hours (FINDING-ercot237 section 3 leg U1 + corner hour h4578) to
its measured drivers: net-load gap, net-load ramp, outages, tie flows. No
lever, no gate change, no matrix stamp: measurement only, per
``docs/PRECOMMIT-ercot239-missedevents-phase0-2026-08-30.md`` (pushed and
blob-verified before this probe ran).

Model/actual price constructions are byte-identical to
``scripts/probes/ercot237_bandswap_phase0.py::_series``. V-0 identity gate:
the recomputed population {h : model < 200 and actual >= 500} must be exactly
the 14 hours named in the committed ercot-237 record, or the probe hard-stops
with no result written (precommit section 1).

Run:
    python scripts/probes/ercot239_missedevents_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot236_k33_clip"
ACTUALS = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
EIA_WIDE = REPO / "data" / "raw" / "eia-930-hourly" / "ERCO hourly.parquet"
CAMPD_UNIT = REPO / "data" / "raw" / "campd-unit-outages.csv"
ERCOT_HOURLY_OUT = REPO / "data" / "raw" / "ercot-outages.csv"
ERCOT237_JSON = REPO / "results" / "calibration" / "ercot237_bandswap_phase0.json"
OUT_JSON = REPO / "results" / "calibration" / "ercot239_missedevents_phase0.json"

#: The committed ercot-237 population (FINDING-ercot237 section 3 U1 + h4578)
#: — the V-0 identity expectation for {h : model < 200 and actual >= 500}.
EXPECT_HOURS = sorted(
    [2058, 2971, 4623, 4626, 5369, 5484, 5777, 5943, 5945, 6399, 7001, 7145, 7480]
    + [4578]
)

#: Overlay eligibility floor (src/market_sim/data/outages.py UNIT_OUTAGE_MIN_DAYS).
OVERLAY_MIN_DAYS = 5

#: Precommit M-5 fixed ex-ante attribution thresholds.
NETLOAD_GAP_MW = 1500.0
RAMP_PCTL = 90.0
OUTAGE_PCTL = 90.0
SHORT_OUTAGE_MW = 1000.0
TIE_EXPORT_MW = 300.0

#: Non-leap cumulative month-start hours (render_calibration_html._CUM).
_CUM = np.cumsum([0] + [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24

#: Fossil-thermal sidecar classes (stack-depth measurement, precommit M-2).
THERMAL = (
    "CC_CHP", "CC_REGULAR", "COAL_LIGNITE", "COAL_PRB",
    "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS", "oil",
)


def _series() -> tuple[np.ndarray, np.ndarray]:
    """(model lw price NaN->0, actual rt) for 2023, len 8760 — ercot-237 verbatim."""
    df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "system_2023.parquet")
    df = df[(df["year"] == 2023) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    rng = range(8760)
    m = np.nan_to_num((num / den).reindex(rng).to_numpy(float))
    a = pd.read_parquet(ACTUALS)
    a = a[a["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    return m, a


def _model_hourly() -> dict[str, np.ndarray]:
    """Model-side hourly panels from the keeper sidecars (P1, len-8760 arrays)."""
    rng = range(8760)
    sys_df = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "system_2023.parquet")
    sys_df = sys_df[(sys_df["year"] == 2023) & (sys_df["pass"] == "P1")]
    g = sys_df.groupby("hour")

    def _s(series: pd.Series) -> np.ndarray:
        return np.nan_to_num(series.reindex(rng).to_numpy(float))

    ch = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "class_hourly_2023.parquet")
    ch = ch[(ch["year"] == 2023) & (ch["pass"] == "P1")]

    def _k(mask: pd.Series) -> np.ndarray:
        return _s(ch[mask].groupby("hour")["mw"].sum())

    st = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "storage_2023.parquet")
    st = st[(st["year"] == 2023) & (st["pass"] == "P1")]
    sg = st.groupby("hour")
    return {
        "demand": _s(g["demand"].sum()),
        "slack": _s(g["slack"].sum()),
        "dump": _s(g["dump"].sum()),
        "reserve_price": _s(g["reserve_price"].max()),
        "ordc_adder": _s(g["ordc_adder"].max()),
        "price_max": _s(g["price"].max()),
        "price_min": _s(g["price"].min()),
        "wind": _k(ch["klass"] == "wind"),
        "solar": _k(ch["klass"] == "solar"),
        "thermal": _k(ch["klass"].isin(THERMAL)),
        "storage_net": _s(sg["discharge_mw"].sum()) - _s(sg["charge_mw"].sum()),
    }


def _eia_hourly() -> pd.DataFrame:
    """EIA-930 wide ERCO rows on the model's non-leap local-year 2023 clock.

    Mirrors ``src/market_sim/data/eia930/frames.py`` row selection: EIA-930
    stamps hours as hour-ending, so a row belongs to the local date one hour
    before its local timestamp; local Feb 29 dropped (2023 non-leap anyway);
    ordered by UTC. Positional index = hour-of-year 0..8759.
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


def _peer_pctl(vals: np.ndarray, h: int, months: np.ndarray) -> float:
    """Percentile of vals[h] within its month x hod+-1 peer set (precommit M-1)."""
    hod = np.arange(8760) % 24
    peers = (months == months[h]) & (np.abs(((hod - hod[h]) + 12) % 24 - 12) <= 1)
    x = vals[peers]
    x = x[~np.isnan(x)]
    return round(float((x <= vals[h]).mean() * 100.0), 1)


def _pctl(vals: np.ndarray, x: float) -> float:
    """Percentile of x within vals (NaN-dropped)."""
    v = vals[~np.isnan(vals)]
    return round(float((v <= x).mean() * 100.0), 1)


def _outage_legs(dates: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """(overlay-eligible daily MW frame, joined hourly events, join stats).

    Leg (i): campd-unit-outages.csv rows with duration_days >= OVERLAY_MIN_DAYS,
    date-grain coverage start <= d <= end — an approximation to the solve's
    derate input (before fleet matching), labelled as such in the JSON.
    Leg (ii): ercot-outages.csv all-duration hourly events, capacity joined on
    (facility_id, unit_id) exact match, else the facility's mean unit capacity
    (flagged estimated).
    """
    cu = pd.read_csv(CAMPD_UNIT, parse_dates=["outage_start", "outage_end"])
    cu = cu[(cu["outage_end"].dt.year >= 2023) & (cu["outage_start"].dt.year <= 2023)]
    eo = pd.read_csv(ERCOT_HOURLY_OUT, parse_dates=["outage_start", "outage_stop"])
    eo = eo[(eo["outage_stop"].dt.year >= 2023) & (eo["outage_start"].dt.year <= 2023)]

    cap = cu.drop_duplicates(["facility_id", "unit_id"])[
        ["facility_id", "unit_id", "unit_capacity_mw"]
    ]
    fac_mean = cap.groupby("facility_id")["unit_capacity_mw"].mean()
    eo = eo.merge(
        cap,
        left_on=["oris_code", "unit"],
        right_on=["facility_id", "unit_id"],
        how="left",
    )
    exact = eo["unit_capacity_mw"].notna()
    eo.loc[~exact, "unit_capacity_mw"] = eo.loc[~exact, "oris_code"].map(fac_mean)
    joined = eo["unit_capacity_mw"].notna()
    stats = {
        "events_2023": int(len(eo)),
        "joined_exact": int(exact.sum()),
        "joined_facility_mean": int((joined & ~exact).sum()),
        "unjoined": int((~joined).sum()),
    }
    return cu[cu["duration_days"] >= OVERLAY_MIN_DAYS], eo[joined], stats


def main() -> None:
    m, a = _series()
    pop = np.where((m < 200.0) & (a >= 500.0))[0]
    # V-0 identity gate — hard stop unless the population is exactly the
    # committed ercot-237 record (precommit section 1).
    assert sorted(int(h) for h in pop) == EXPECT_HOURS, (
        f"V-0 FAIL population {sorted(int(h) for h in pop)} != {EXPECT_HOURS}"
    )
    # Precommit Amendment 1: the ercot-237 JSON carries no hour list for the
    # lt_200|ge_1000 cell (its recording rule covered only cells touching the
    # middle bands) — cross-check the 13-h U1 list plus that cell's COUNT; the
    # corner hour h4578 is carried by FINDING-ercot237 section 3 and by the
    # recomputed-population equality asserted above.
    e237 = json.loads(ERCOT237_JSON.read_text())
    ref = sorted(r["h"] for r in e237["cell_hours"]["lt_200|500_1000"])
    assert ref == [h for h in EXPECT_HOURS if h != 4578], (
        f"V-0 FAIL ercot-237 U1 record {ref}"
    )
    assert e237["joint_band_matrix"]["lt_200|ge_1000"] == 1, (
        "V-0 FAIL ercot-237 lt_200|ge_1000 count != 1"
    )

    months = np.searchsorted(_CUM, np.arange(8760), side="right")
    mdl = _model_hourly()
    eia = _eia_hourly()

    act_d = eia["Demand"].to_numpy(float)
    act_w = eia["NG: WND"].to_numpy(float)
    act_s = eia["NG: SUN"].to_numpy(float)
    act_nl = act_d - np.nan_to_num(act_w) - np.nan_to_num(act_s)
    interchange = eia["Total interchange"].to_numpy(float)
    ramp1 = np.full(8760, np.nan)
    ramp3 = np.full(8760, np.nan)
    ramp1[1:] = act_nl[1:] - act_nl[:-1]
    ramp3[3:] = act_nl[3:] - act_nl[:-3]

    # Alignment check (precommit section 5 trigger if it fails): the model
    # demand must correlate with EIA-930 demand best at lag 0.
    lags = {
        lag: float(np.corrcoef(mdl["demand"][3:-3], act_d[3 + lag : 8757 + lag])[0, 1])
        for lag in (-2, -1, 0, 1, 2)
    }
    assert max(lags, key=lags.get) == 0, f"alignment FAIL: lag corr {lags}"

    mdl_nl = mdl["demand"] - mdl["wind"] - mdl["solar"]

    overlay, joined_ev, join_stats = _outage_legs(eia["Local date"])
    day_dates = pd.to_datetime("2023-01-01") + pd.to_timedelta(np.arange(365), "D")
    overlay_daily = np.array(
        [
            overlay[
                (overlay["outage_start"] <= d) & (d <= overlay["outage_end"])
            ]["unit_capacity_mw"].sum()
            for d in day_dates
        ]
    )
    # Hourly all-duration outage MW (leg ii): naive-local hour-beginning stamps,
    # coverage start <= ts <= stop (the source labels a 1-h event start == stop).
    hour_ts = pd.Series(
        pd.to_datetime("2023-01-01") + pd.to_timedelta(np.arange(8760), "h")
    )
    ev = joined_ev
    hourly_out = np.zeros(8760)
    hourly_short = np.zeros(8760)
    is_short = (ev["outage_stop"] - ev["outage_start"]) < pd.Timedelta(
        days=OVERLAY_MIN_DAYS
    )
    for start, stop, cap_mw, short in zip(
        ev["outage_start"], ev["outage_stop"], ev["unit_capacity_mw"], is_short
    ):
        i0 = max(0, int((start - hour_ts[0]).total_seconds() // 3600))
        i1 = min(8759, int((stop - hour_ts[0]).total_seconds() // 3600))
        if i1 >= 0 and i0 <= 8759:
            hourly_out[i0 : i1 + 1] += cap_mw
            if short:
                hourly_short[i0 : i1 + 1] += cap_mw

    rf = pd.read_parquet(KEEPER_BUNDLE / "hourly" / "reserve_family_2023.parquet")
    rf = rf[(rf["year"] == 2023) & (rf["pass"] == "P1")]

    rows = []
    for h in EXPECT_HOURS:
        day = int(h // 24)
        fam = rf[rf["hour"] == h]
        gap = float(act_nl[h] - mdl_nl[h])
        comp = {
            "demand": float(act_d[h] - mdl["demand"][h]),
            "wind": float(mdl["wind"][h] - np.nan_to_num(act_w[h])),
            "solar": float(mdl["solar"][h] - np.nan_to_num(act_s[h])),
        }
        drivers = []
        if gap >= NETLOAD_GAP_MW:
            drivers.append(
                "netload_gap:" + max(comp, key=lambda k: comp[k])
            )
        month_ramp3 = ramp3[months == months[h]]
        if not np.isnan(ramp3[h]) and ramp3[h] >= np.nanpercentile(
            month_ramp3, RAMP_PCTL
        ):
            drivers.append("ramp")
        if hourly_out[h] >= np.percentile(hourly_out, OUTAGE_PCTL) or (
            hourly_short[h] >= SHORT_OUTAGE_MW
        ):
            drivers.append("outage")
        if interchange[h] >= TIE_EXPORT_MW:
            drivers.append("tie_export")
        rows.append(
            {
                "h": h,
                "month": int(months[h]),
                "hod": int(h % 24),
                "model": round(float(m[h]), 2),
                "actual": round(float(a[h]), 2),
                "actual_side": {
                    "demand": round(float(act_d[h]), 0),
                    "wind": round(float(np.nan_to_num(act_w[h])), 0),
                    "solar": round(float(np.nan_to_num(act_s[h])), 0),
                    "net_load": round(float(act_nl[h]), 0),
                    "ramp1": round(float(ramp1[h]), 0),
                    "ramp3": round(float(ramp3[h]), 0),
                    "interchange": round(float(interchange[h]), 0),
                    "ties": {
                        ba: round(float(eia[ba].iloc[h]), 0)
                        for ba in ("CEN", "CFE", "SWPP")
                        if ba in eia.columns and pd.notna(eia[ba].iloc[h])
                    },
                    "net_load_pctl_year": _pctl(act_nl, act_nl[h]),
                    "net_load_pctl_peers": _peer_pctl(act_nl, h, months),
                    "ramp3_pctl_month": _pctl(month_ramp3, ramp3[h]),
                },
                "model_side": {
                    "demand": round(float(mdl["demand"][h]), 0),
                    "wind": round(float(mdl["wind"][h]), 0),
                    "solar": round(float(mdl["solar"][h]), 0),
                    "net_load": round(float(mdl_nl[h]), 0),
                    "thermal": round(float(mdl["thermal"][h]), 0),
                    "thermal_pctl_month": _pctl(
                        mdl["thermal"][months == months[h]], mdl["thermal"][h]
                    ),
                    "storage_net": round(float(mdl["storage_net"][h]), 0),
                    "slack": round(float(mdl["slack"][h]), 1),
                    "dump": round(float(mdl["dump"][h]), 1),
                    "reserve_price": round(float(mdl["reserve_price"][h]), 2),
                    "ordc_adder": round(float(mdl["ordc_adder"][h]), 2),
                    "reserve_shortfall_mw": round(float(fam["shortfall_mw"].sum()), 1),
                    "max_family_dual": round(float(fam["dual"].max()), 2)
                    if len(fam)
                    else 0.0,
                },
                "netload_gap_mw": round(gap, 0),
                "gap_components_mw": {k: round(v, 0) for k, v in comp.items()},
                "outage": {
                    "overlay_daily_mw": round(float(overlay_daily[day]), 0),
                    "overlay_daily_pctl_year": _pctl(
                        overlay_daily.astype(float), float(overlay_daily[day])
                    ),
                    "hourly_all_mw": round(float(hourly_out[h]), 0),
                    "hourly_all_pctl_year": _pctl(hourly_out, float(hourly_out[h])),
                    "hourly_short_mw": round(float(hourly_short[h]), 0),
                },
                "drivers": drivers if drivers else ["UNATTRIBUTED"],
            }
        )

    # Prior grading (precommit section 3) — computed, judged in the FINDING.
    n_ramp = sum("ramp" in r["drivers"] for r in rows)
    n_gap = sum(any(d.startswith("netload_gap") for d in r["drivers"]) for r in rows)
    gap_wind = sum("netload_gap:wind" in r["drivers"] for r in rows)
    n_tie = sum("tie_export" in r["drivers"] for r in rows)
    non_aug = [r for r in rows if r["month"] != 8]
    p5_n = sum(r["outage"]["overlay_daily_pctl_year"] >= 75.0 for r in non_aug)
    priors = {
        "P1_not_near_miss": {
            "all_zero_shortfall": all(
                r["model_side"]["reserve_shortfall_mw"] == 0.0 for r in rows
            ),
            "all_dual_le_5": all(
                r["model_side"]["max_family_dual"] <= 5.0 for r in rows
            ),
        },
        "P2_ramp_hours": {"n": n_ramp, "declared_ge": 8},
        "P3_tie_export_hours": {"n": n_tie, "declared_le": 3},
        "P4_netload_gap_hours": {
            "n": n_gap,
            "declared_ge": 5,
            "wind_largest_component": gap_wind,
        },
        "P5_nonaug_outage_p75": {
            "n": p5_n,
            "of": len(non_aug),
            "declared_ge": 5,
        },
    }

    res = {
        "session": "ercot-239",
        "keeper": "2026-08-25-236-swcap-clip-k33",
        "precommit": "docs/PRECOMMIT-ercot239-missedevents-phase0-2026-08-30.md",
        "v0_identity": {"hours": EXPECT_HOURS, "pass": True},
        "alignment_lag_corr": {str(k): round(v, 4) for k, v in lags.items()},
        "conventions": {
            "interchange_sign": "EIA-930: positive = net exports",
            "tie_columns": "CEN/CFE/SWPP = interchange with that BA, positive = export",
            "outage_leg_i": (
                "campd-unit-outages.csv duration_days >= 5, date-grain "
                "start <= d <= end; approximation to the solve derate input "
                "(before fleet matching)"
            ),
            "outage_leg_ii": (
                "ercot-outages.csv all durations, naive-local hour stamps, "
                "coverage start <= ts <= stop; capacity via (facility_id, "
                "unit_id) exact join else facility mean (estimated)"
            ),
        },
        "outage_join_stats": join_stats,
        "attribution_thresholds": {
            "netload_gap_mw": NETLOAD_GAP_MW,
            "ramp_pctl_month": RAMP_PCTL,
            "outage_pctl_year": OUTAGE_PCTL,
            "short_outage_mw": SHORT_OUTAGE_MW,
            "tie_export_mw": TIE_EXPORT_MW,
        },
        "rows": rows,
        "driver_counts": {
            "netload_gap": n_gap,
            "ramp": n_ramp,
            "outage": sum("outage" in r["drivers"] for r in rows),
            "tie_export": n_tie,
            "unattributed": sum(r["drivers"] == ["UNATTRIBUTED"] for r in rows),
        },
        "priors": priors,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    headline = {
        "driver_counts": res["driver_counts"],
        "priors": priors,
        "per_hour": [
            {
                "h": r["h"],
                "month": r["month"],
                "hod": r["hod"],
                "actual": r["actual"],
                "model": r["model"],
                "gap": r["netload_gap_mw"],
                "ramp3_pctl": r["actual_side"]["ramp3_pctl_month"],
                "outage_pctl": r["outage"]["hourly_all_pctl_year"],
                "drivers": r["drivers"],
            }
            for r in rows
        ],
    }
    print(json.dumps(headline, indent=1))


if __name__ == "__main__":
    main()
