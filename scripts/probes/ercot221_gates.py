"""ercot-221 A/B gate scorer — the PRECOMMIT-ercot221 §4 direction-blind table.

Adapted from the committed ercot219_gates.py (identical constructions for
G-CAP / G-SPUR / G-SHED / G-BAT / G-D2; the G-EXH reporter is replaced by the
adaptive-sidecar reporter G-ADA). C3a/C3b probe-basis numbers are side-effect
reporting under Q-B FINAL / R-A — never a gate; G-OWNER is judged from the
official registration scorecard, reported here on the probe basis.

Usage:
    python scripts/probes/ercot221_gates.py --control <bundle> --arm <bundle>
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
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)
VOLL = 5000.0
MID_BAND = (150.0, 500.0)
#: G-SPUR baselines — LIDLESS (ercot-225 card Option A, owner-signed
#: 2026-08-26): the gated count is S_nolid = #{model >= 150 & actual < 150};
#: a gate whose purpose is "no new spurious high-price hours" must not be
#: escapable by overshooting the band top. Re-minted 9/12/1 from the
#: `ercot215_decontam_B` committed sidecars (the card §2/§7; verified
#: against results/calibration/ercot225_gspur_bandtop_reread.json): the
#: 2024 +1 over the old banded 9/11/1 is h3068 (May 8 2024 20:00 CST, the
#: standing band-top-blind hour in every lineage, card §4c). The hour
#: IDENTITIES simultaneously repair the card §6 hygiene defect — the prior
#: lists here did not match the baseline bundle's own hours on this file's
#: own construction (counts agreed; identities did not).
SPUR_BASELINE: dict[int, list[int]] = {
    2023: [5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822],
    2024: [336, 337, 338, 339, 345, 346, 347, 348, 349, 2540, 2829, 3068],
    2025: [3355],
}
SPUR_BAR = 5
SHED_BASELINE: dict[int, list[int]] = {2023: [], 2024: [3067], 2025: []}
GBAT_TOL = 0.25
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_CUM = np.cumsum((0,) + MONTH_DAYS)


def _member(bundle: Path, year: int) -> dict[str, np.ndarray]:
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
    return lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]


def _spur_hours(m: np.ndarray, a: np.ndarray) -> list[int]:
    """The GATED spurious set — LIDLESS since the ercot-225 Option A
    signature (owner, 2026-08-26): model >= $150 & actual < $150, no upper
    bound, so pricing a phantom hour past the band top cannot remove it
    from the count. The band/top split stays reported via
    :func:`_spur_decomposition`."""
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    return [int(h) for h in np.where((mm >= MID_BAND[0]) & (aa < MID_BAND[0]))[0]]


def _spur_decomposition(m: np.ndarray, a: np.ndarray) -> dict:
    """The KEPT report decomposition (ercot-225 card Option A): S_band =
    the former banded count (model in [150, 500]), S_top = the overshoot
    past the band top (model > 500)."""
    mm = np.nan_to_num(m)
    aa = np.nan_to_num(a, nan=1e9)
    lo = aa < MID_BAND[0]
    band = np.where((mm >= MID_BAND[0]) & (mm <= MID_BAND[1]) & lo)[0]
    top = np.where((mm > MID_BAND[1]) & lo)[0]
    return {
        "s_band": int(band.size),
        "s_top": int(top.size),
        "s_top_hours": [int(h) for h in top],
    }


def _model_hour_utc(year: int) -> np.ndarray:
    hoy = np.arange(8760)
    day = hoy // 24
    month = np.searchsorted(_MONTH_CUM, day, side="right")
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


def _gada(bundle: Path, year: int) -> dict:
    p = bundle / "hourly" / f"adaptive_{year}.parquet"
    if not p.exists():
        return {"present": False}
    df = pd.read_parquet(p)
    ph = df["p_hat_day"].to_numpy(float)
    fl = df["floor_usd"].to_numpy(float)
    hoy = df["hour"].to_numpy(int)
    month = np.searchsorted(_MONTH_CUM, hoy // 24, side="right")
    day_spike = df.groupby(hoy // 24)["s_model_day"].first()
    active = fl >= 1000.0
    return {
        "present": True,
        "model_spike_days": int(day_spike.sum()),
        "p_hat_max": round(float(ph.max()), 4),
        "floor_ge_1000_hours": int(active.sum()),
        "floor_ge_1000_by_month": {
            str(m): int((active & (month == m)).sum())
            for m in range(1, 13)
            if (active & (month == m)).any()
        },
        "floor_max_usd": round(float(fl.max()), 1),
    }


def _d4_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D4", {}).get("rows", [])
    return sorted(
        f"{r['year']}|{r['floor']}|{r['window']}|{r['verdict']}" for r in rows
    )


def _d5_adaptive_rows(bundle: Path) -> list[str]:
    d = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    rows = d["diagnostics"].get("D5", {}).get("rows", [])
    return sorted(
        r["mechanism"]
        for r in rows
        if r["mechanism"].startswith("ercot_storage_adaptive")
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/ercot221_gates.json")
    )
    args = ap.parse_args()
    ctl_b, arm_b = Path(args.control), Path(args.arm)

    out: dict = {
        "probe": "ercot221_gates",
        "charter": "PRECOMMIT-ercot221 §4 (card-§4-inherited table)",
        "control": str(ctl_b),
        "arm": str(arm_b),
        "years": list(YEARS),
        "per_year": {},
    }
    gcap_viol = 0
    spur_fail = shed_fail = gbat_fail = False
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
                "spur_decomposition": _spur_decomposition(m["price"], a),
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
                yr["gada_arm"] = _gada(arm_b, y)
        yr["spur_baseline"] = SPUR_BASELINE[y]
        yr["shed_baseline"] = SHED_BASELINE[y]
        out["per_year"][str(y)] = yr

    out["d4_rows_control"] = _d4_rows(ctl_b)
    out["d4_rows_arm"] = _d4_rows(arm_b)
    out["d4_no_new_rows"] = set(out["d4_rows_arm"]) <= set(out["d4_rows_control"]) or (
        out["d4_rows_arm"] == out["d4_rows_control"]
    )
    out["d5_adaptive_rows_arm"] = _d5_adaptive_rows(arm_b)
    out["gates"] = {
        "G-CAP": {"violations": gcap_viol, "pass": gcap_viol == 0},
        "G-SPUR": {
            "pass": not spur_fail,
            "bar": f"+{SPUR_BAR}/yr vs 9/12/1 (LIDLESS, ercot-225 Option A "
            "owner-signed 2026-08-26; band/top decomposition reported)",
        },
        "G-SHED": {"pass": not shed_fail},
        "G-BAT": {"pass": not gbat_fail, "tol": GBAT_TOL},
        "G-D2": {
            "no_new_d4_rows": bool(out["d4_no_new_rows"]),
            "adaptive_row_present": len(out["d5_adaptive_rows_arm"]) == 1,
        },
        "G-ADA": {"reported_not_gated": True},
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {args.out}")
    print(json.dumps(out["gates"], indent=1))


if __name__ == "__main__":
    main()
