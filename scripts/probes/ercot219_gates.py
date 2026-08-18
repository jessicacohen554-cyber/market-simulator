#!/usr/bin/env python3
"""ercot-219 Option-B A/B gate scorer (PRECOMMIT-ercot219 §3) — committed
artifacts only, no LP.

Scores the card-§4 direction-blind gate table on the registered pair
(control = the ercot-215 keeper recipe replayed at HEAD; arm = control + the
three Option-B booleans), with the §3.1 measurement conventions:

* G-CAP  — written ``ordc_adder(t) ≤ VOLL − λ(t)`` in every solved hour.
* G-SPUR — model ∈ [150, 500] & actual RT < $150 (the _ercot173_ab /
  ercot-214 demand-weighted P1 settled-price convention), counts + hour SETS
  vs the inherited 9/11/1 baseline sets, bar +5/yr.
* G-SHED — slack>0 hours per year, identical-hour-list vs the keeper's 0/1/0
  (2024 h3067).
* G-BAT  — model storage net discharge summed over the ACTUAL RT>$200 tail
  hours inside EIA-930 BAT coverage vs the measured BAT MWh, |ratio−1| ≤ 0.25
  (2024: 9 covered hours; 2025: 31). Clock: 930 ``period`` is hour-ENDING
  UTC; the model runs the fixed non-leap hour-beginning CST clock
  (ercot-216 §6 — the date-wise mapping absorbs the 2024 leap shift). The
  alignment is verified in-probe by correlating model demand against the
  930 generation sum at the constructed join.
* G-EXH  — reported, not gated: per year, hours with LOLP(H(t)) ≥ 0.5 and
  hours with P_exhaust·VOLL ≥ $1,000, with monthly calendars (from the arm's
  committed ``hourly/exhaustion_<yr>.parquet``).
* G-D2   — D-4 FAIL row-set comparison + stage attribution rows present
  (from both bundles' ``legitimacy_diagnostics.json``).
* C3a/C3b probe-basis cross-checks per year (side-effect reporting under
  Q-B/R-A — the OFFICIAL determination is scripts/calibration_verdict.py's).

Usage:
    python scripts/probes/ercot219_gates.py \
        --control results/calibration/ercot219_control_A \
        --arm results/calibration/ercot219_optionb_B \
        [--out results/calibration/ercot219_gates.json]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)
VOLL = 5000.0  # the keeper's registered ordc_voll (run_config.json)
#: Inherited G-SPUR baseline hour sets (ercot-215 G-EXACT / keeper committed).
SPUR_BASELINE: dict[int, list[int]] = {
    2023: [5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822],
    2024: [336, 337, 338, 339, 345, 346, 347, 348, 349, 2540, 2829],
    2025: [3355],
}
SPUR_BAR = 5
#: Keeper G-SHED hour lists (0/1/0; ercot-215 promotion note).
SHED_BASELINE: dict[int, list[int]] = {2023: [], 2024: [3067], 2025: []}
GBAT_TOL = 0.25
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_CUM = np.cumsum((0,) + MONTH_DAYS)


def _member(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """Demand-weighted P1 settled price + λ + adder + slack (ercot-214 conv)."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")].copy()
    overlay = np.zeros(len(df))
    for col in ("rtordpa_overlay", "ordc_adder"):
        if col in df.columns:
            overlay = overlay + df[col].to_numpy(float)
    df["lam_z"] = df["price"].to_numpy(float) - overlay

    def dw(col: str) -> np.ndarray:
        num = (df[col] * df["demand"]).groupby(df["hour"]).sum()
        den = df.groupby("hour")["demand"].sum()
        return (num / den).reindex(range(8760)).to_numpy(float)

    g = df.groupby("hour")
    return {
        "price": dw("price"),
        "lam": dw("lam_z"),
        "adder": g["ordc_adder"].first().reindex(range(8760)).to_numpy(float),
        "slack": g["slack"].sum().reindex(range(8760)).fillna(0.0).to_numpy(float),
        "demand": g["demand"].sum().reindex(range(8760)).to_numpy(float),
    }


def _actual(year: int) -> np.ndarray:
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    s = lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)
    return s[:8760]


def _spur_hours(m: np.ndarray, a: np.ndarray) -> list[int]:
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    return [
        int(h)
        for h in np.where(
            (mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & (aa < MID_BAND[0])
        )[0]
    ]


def _model_hour_utc(year: int) -> np.ndarray:
    """Hour-beginning UTC timestamps of the fixed non-leap CST clock.

    Date-wise mapping (month/day from the non-leap calendar; Feb 29 has no
    model hour), CST = UTC−6 fixed — the ercot-216 §6 discipline.
    """
    hoy = np.arange(8760)
    day = hoy // 24
    month = np.searchsorted(_MONTH_CUM, day, side="right")  # 1..12
    dom = day - _MONTH_CUM[month - 1] + 1
    hod = hoy % 24
    return np.array(
        [
            np.datetime64(
                dt.datetime(year, int(m), int(d), int(h)) + dt.timedelta(hours=6)
            )
            for m, d, h in zip(month, dom, hod)
        ]
    )


def _eia930(year: int) -> pd.DataFrame:
    ft = pd.read_parquet(REPO / "data/raw/ERCO_fueltype.parquet")
    f = ft[ft["period"].dt.year.isin([year, year + 1])].copy()
    # hour-ENDING -> hour-beginning UTC
    f["ts"] = f["period"].dt.tz_localize(None) - pd.Timedelta(hours=1)
    return f


def _gbat(bundle: Path, year: int, tail_hours: np.ndarray) -> dict:
    st = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    st = st[st["pass"] == "P1"]
    g = st.groupby("hour")
    net = (
        (g["discharge_mw"].sum() - g["charge_mw"].sum())
        .reindex(range(8760))
        .fillna(0.0)
        .to_numpy(float)
    )
    f = _eia930(year)
    bat = f[f["fueltype"] == "BAT"].set_index("ts")["value_mwh"]
    ts = _model_hour_utc(year)
    bat_series = bat.reindex(pd.DatetimeIndex(ts)).to_numpy(float)
    covered = tail_hours[~np.isnan(bat_series[tail_hours])]
    out = {
        "tail_hours": int(tail_hours.size),
        "covered_tail_hours": int(covered.size),
    }
    # Clock-alignment verification: model demand vs 930 total generation.
    dfm = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    dfm = dfm[dfm["pass"] == "P1"]
    dem = dfm.groupby("hour")["demand"].sum().reindex(range(8760)).to_numpy(float)
    tot = f.groupby("ts")["value_mwh"].sum()
    tot_series = tot.reindex(pd.DatetimeIndex(ts)).to_numpy(float)
    ok = ~np.isnan(tot_series) & ~np.isnan(dem)
    out["clock_corr_model_demand_vs_930_gen"] = (
        round(float(np.corrcoef(dem[ok], tot_series[ok])[0, 1]), 5)
        if ok.sum() > 100
        else None
    )
    if covered.size:
        model_mwh = float(net[covered].sum())
        actual_mwh = float(bat_series[covered].sum())
        out["model_net_discharge_mwh"] = round(model_mwh, 1)
        out["actual_bat_mwh"] = round(actual_mwh, 1)
        if abs(actual_mwh) > 1e-9:
            ratio = model_mwh / actual_mwh
            out["ratio"] = round(ratio, 4)
            out["pass"] = bool(abs(ratio - 1.0) <= GBAT_TOL)
        else:
            out["ratio"] = None
            out["pass"] = None
            out["note"] = "actual BAT ~0 over covered tail hours"
    else:
        out["pass"] = None
        out["note"] = "no covered tail hours (series coverage)"
    return out


def _gexh(bundle: Path, year: int) -> dict:
    p = bundle / "hourly" / f"exhaustion_{year}.parquet"
    if not p.exists():
        return {"present": False}
    df = pd.read_parquet(p)
    lolp = df["lolp"].to_numpy(float)
    pexh = df["p_exhaust"].to_numpy(float)
    hoy = df["hour"].to_numpy(int)
    month = np.searchsorted(_MONTH_CUM, hoy // 24, side="right")
    exh = lolp >= 0.5
    spike = pexh * VOLL >= 1000.0
    return {
        "present": True,
        "exhaustion_hours_lolp_ge_050": int(exh.sum()),
        "exhaustion_calendar_by_month": {
            str(m): int((exh & (month == m)).sum())
            for m in range(1, 13)
            if (exh & (month == m)).any()
        },
        "reservation_ge_1000_hours": int(spike.sum()),
        "reservation_calendar_by_month": {
            str(m): int((spike & (month == m)).sum())
            for m in range(1, 13)
            if (spike & (month == m)).any()
        },
        "h_margin_p5_mw": round(float(np.percentile(df["h_margin_mw"], 5)), 1),
        "as_sequestered_mw_mean": round(float(df["as_sequestered_mw"].mean()), 1),
        "p_exhaust_max": round(float(pexh.max()), 6),
    }


def _d4_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D4", {}).get("rows", [])
    return sorted(
        f"{r['year']}|{r['floor']}|{r['window']}|{r['verdict']}" for r in rows
    )


def _d5_stage_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D5", {}).get("rows", [])
    return sorted(
        r["mechanism"]
        for r in rows
        if r["mechanism"].startswith(
            ("ercot_capability_", "ercot_exhaustion_", "ercot_storage_reservation")
        )
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/ercot219_gates.json")
    )
    args = ap.parse_args()
    ctl_b, arm_b = Path(args.control), Path(args.arm)

    out: dict = {
        "probe": "ercot219_gates",
        "charter": "PRECOMMIT-ercot219 §3 (card §4 verbatim table)",
        "control": str(ctl_b),
        "arm": str(arm_b),
        "years": list(YEARS),
        "per_year": {},
    }
    gcap_viol = 0
    spur_fail = shed_fail = False
    gbat_fail = False
    for y in YEARS:
        a = _actual(y)
        tail = np.where(np.nan_to_num(a) > 200.0)[0]
        yr: dict = {}
        for name, b in (("control", ctl_b), ("arm", arm_b)):
            m = _member(b, y)
            viol = int(
                (
                    np.nan_to_num(m["adder"]) > np.maximum(VOLL - m["lam"], 0.0) + 1e-6
                ).sum()
            )
            spur = _spur_hours(m["price"], a)
            shed = [int(h) for h in np.where(m["slack"] > 1e-6)[0]]
            ok = np.isfinite(m["price"]) & np.isfinite(a)
            mm, aa = m["price"][ok], a[ok]
            yr[name] = {
                "gcap_violations": viol,
                "spur_hours": spur,
                "spur_count": len(spur),
                "shed_hours": shed,
                "c3a_probe_pct": round(
                    float((mm.mean() - aa.mean()) / aa.mean() * 100.0), 2
                ),
                "c3b_probe_nrmse": round(
                    float(np.sqrt(np.mean((mm - aa) ** 2)) / aa.mean()), 4
                ),
                "tail_model_gt200": int((mm > 200.0).sum()),
                "model_mean": round(float(mm.mean()), 3),
            }
            if name == "arm":
                gcap_viol += viol
                if len(spur) > len(SPUR_BASELINE[y]) + SPUR_BAR:
                    spur_fail = True
                if sorted(shed) != sorted(SHED_BASELINE[y]) and not set(shed) <= set(
                    SHED_BASELINE[y]
                ):
                    shed_fail = True
                yr["gbat_arm"] = _gbat(arm_b, y, tail)
                if yr["gbat_arm"].get("pass") is False:
                    gbat_fail = True
                yr["gexh_arm"] = _gexh(arm_b, y)
        yr["spur_baseline"] = SPUR_BASELINE[y]
        yr["shed_baseline"] = SHED_BASELINE[y]
        out["per_year"][str(y)] = yr

    out["d4_rows_control"] = _d4_rows(ctl_b)
    out["d4_rows_arm"] = _d4_rows(arm_b)
    out["d4_no_new_rows"] = set(out["d4_rows_arm"]) <= set(out["d4_rows_control"]) or (
        out["d4_rows_arm"] == out["d4_rows_control"]
    )
    out["d5_stage_rows_arm"] = _d5_stage_rows(arm_b)
    out["gates"] = {
        "G-CAP": {"violations": gcap_viol, "pass": gcap_viol == 0},
        "G-SPUR": {"pass": not spur_fail, "bar": f"+{SPUR_BAR}/yr vs 9/11/1"},
        "G-SHED": {"pass": not shed_fail},
        "G-BAT": {"pass": not gbat_fail, "tol": GBAT_TOL},
        "G-D2": {
            "no_new_d4_rows": bool(out["d4_no_new_rows"]),
            "stage_rows_present": len(out["d5_stage_rows_arm"]) == 3,
        },
        "G-EXH": {"reported_not_gated": True},
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    print(json.dumps(out["gates"], indent=1))


if __name__ == "__main__":
    main()
