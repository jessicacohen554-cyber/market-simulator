#!/usr/bin/env python3
"""nyiso-110 A/B gate scorer — PREREG-nyiso110-spin-online-peak-formation.

Evaluates the pre-registered construction gates (K1–K6) and kill gates
(P1/P2/P4 preview; P3/P5 are read authoritatively from the registration
post-steps) for the flag-only ``nyiso_spin_reserve_online`` arm against its
same-HEAD zero-delta control, plus the REPORTED-never-gated amplitude
movement. The authoritative criterion verdicts come from
``calibration_verdict.py`` at registration; this scorer is the prereg's own
gate instrument.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso110_spin_online_ab.py \
        --control results/calibration/nyiso110_control_A \
        --arm results/calibration/nyiso110_spinonline_B \
        --keeper results/calibration/nyiso109_zonalanchor_B \
        --out results/calibration/_nyiso110_spin_online_ab.json
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
YEARS = (2023, 2024, 2025)
HOURS = 8760
MODEL_ZONES = (
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
)
TROUGH = (1, 2, 3, 4, 5)
PEAK = (17, 18, 19)


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 zonal price/demand/reserve pivot for one year."""
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[(s["zone"].isin(MODEL_ZONES)) & (s["pass"] == "P1")]
    price = s.pivot_table(index="hour", columns="zone", values="price")[
        list(MODEL_ZONES)
    ].reindex(range(HOURS))
    dem = s.pivot_table(index="hour", columns="zone", values="demand")[
        list(MODEL_ZONES)
    ].reindex(range(HOURS))
    rp = s.pivot_table(index="hour", columns="zone", values="reserve_price")[
        list(MODEL_ZONES)
    ].reindex(range(HOURS))
    return price, dem, rp


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    return c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")


def _lw_price(price: pd.DataFrame, dem: pd.DataFrame) -> np.ndarray:
    w = dem.to_numpy(float)
    return np.average(price.to_numpy(float), weights=w, axis=1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", default="results/calibration/nyiso110_control_A")
    ap.add_argument("--arm", default="results/calibration/nyiso110_spinonline_B")
    ap.add_argument("--keeper", default="results/calibration/nyiso109_zonalanchor_B")
    ap.add_argument("--out", default="results/calibration/_nyiso110_spin_online_ab.json")
    args = ap.parse_args(argv)
    ctrl, arm, keeper = Path(args.control), Path(args.arm), Path(args.keeper)

    out: dict = {"control": str(ctrl), "arm": str(arm), "keeper": str(keeper)}

    # K1 / K4 — flag fidelity + single delta.
    cfg_c = json.loads((ctrl / "run_config.json").read_text())["scenario_config"]
    cfg_a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diff = {
        k: (cfg_c.get(k), cfg_a.get(k))
        for k in sorted(set(cfg_c) | set(cfg_a))
        if cfg_c.get(k) != cfg_a.get(k)
    }
    out["K1_K4"] = {
        "config_diff": diff,
        "pass": diff == {"nyiso_spin_reserve_online": (False, True)},
    }

    # K2 — control vs committed keeper, strict byte basis on class-hour MW.
    k2 = {}
    for y in YEARS:
        a = _class_hourly(ctrl, y)
        b = _class_hourly(keeper, y)
        cols = sorted(set(a.columns) | set(b.columns))
        a = a.reindex(columns=cols).fillna(0.0)
        b = b.reindex(columns=cols).fillna(0.0)
        k2[str(y)] = float(np.abs(a.to_numpy() - b.to_numpy()).max())
    out["K2"] = {"max_abs_class_hour_delta_mw": k2, "pass": max(k2.values()) == 0.0}

    # K3 — liveness: arm reserve dual hours > 0 per year (and control's).
    k3 = {}
    for y in YEARS:
        _, _, rp_a = _system(arm, y)
        _, _, rp_c = _system(ctrl, y)
        ra = rp_a.to_numpy(float).mean(axis=1)
        rc = rp_c.to_numpy(float).mean(axis=1)
        k3[str(y)] = {
            "arm_hours_gt0": int((ra > 1e-9).sum()),
            "control_hours_gt0": int((rc > 1e-9).sum()),
            "arm_peak_window_mean": round(
                float(ra[np.isin(np.arange(HOURS) % 24, PEAK)].mean()), 4
            ),
            "arm_max": round(float(ra.max()), 2),
        }
    out["K3"] = {
        "per_year": k3,
        "pass": all(v["arm_hours_gt0"] >= 500 for v in k3.values()),
    }

    # K6 — direction: no zone's lambda falls > $0.01 anywhere.
    k6 = {}
    for y in YEARS:
        p_a, _, _ = _system(arm, y)
        p_c, _, _ = _system(ctrl, y)
        d = p_a.to_numpy(float) - p_c.to_numpy(float)
        k6[str(y)] = {
            "max_fall": round(float(d.min()), 4),
            "max_rise": round(float(d.max()), 4),
            "mean_delta": round(float(d.mean()), 4),
        }
    out["K6"] = {
        "per_year": k6,
        "pass": all(v["max_fall"] >= -0.01 for v in k6.values()),
    }

    # P1 / P2 — C3a preview (rt_lw basis: model LW annual mean vs bench rt_lw).
    c3a = {}
    for y in YEARS:
        bench = json.load(gzip.open(REPO / "frontend/data/backcast/bench/NYISO" / f"{y}.json.gz"))
        rt_lw = float(bench["bench"]["avgLMP"]["rt_lw"])
        row = {}
        for label, b in (("control", ctrl), ("arm", arm)):
            price, dem, _ = _system(b, y)
            m = float(np.average(_lw_price(price, dem), weights=dem.sum(axis=1)))
            row[label] = round((m / rt_lw - 1.0) * 100.0, 3)
        row["actual_rt_lw"] = rt_lw
        c3a[str(y)] = row
    out["P1_P2_c3a_preview"] = {
        "per_year": c3a,
        "P1_pass": c3a["2023"]["arm"] <= 10.0,
        "P2_pass": all(abs(c3a[str(y)]["arm"]) <= 10.0 for y in (2024, 2025)),
    }

    # P4 — the nyiso-84 overnight GT-forcing signature.
    p4 = {}
    hod = np.arange(HOURS) % 24
    night = np.isin(hod, TROUGH)
    for y in YEARS:
        ca = _class_hourly(arm, y)
        cc = _class_hourly(ctrl, y)
        gt = [c for c in ("CT_PEAKER", "CT_CHP") if c in ca.columns]
        ea = float(ca[gt].to_numpy()[night].sum())
        ec = float(cc[gt].to_numpy()[night].sum())
        p4[str(y)] = {
            "arm_overnight_gt_mwh": round(ea, 1),
            "control_overnight_gt_mwh": round(ec, 1),
            "pct_change": round((ea / ec - 1.0) * 100.0, 3) if ec else None,
        }
    out["P4"] = {
        "per_year": p4,
        "pass": all(
            v["pct_change"] is not None and v["pct_change"] <= 10.0 for v in p4.values()
        ),
    }

    # REPORTED (never gated): swing / amplitude movement + energy deltas.
    rep = {}
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
    )
    for y in YEARS:
        hub = act[act["year"] == y].set_index("hour").reindex(range(HOURS))
        row = {}
        for label, b in (("control", ctrl), ("arm", arm)):
            price, dem, _ = _system(b, y)
            m = _lw_price(price, dem)
            t, p = np.isin(hod, TROUGH), np.isin(hod, PEAK)
            for basis in ("da", "rt"):
                a = hub[basis].to_numpy(float)
                ok = np.isfinite(a)
                sw_m = float(m[ok & p].mean() - m[ok & t].mean())
                sw_a = float(a[ok & p].mean() - a[ok & t].mean())
                row[f"{label}_{basis}_swing_share"] = round(sw_m / sw_a, 4)
                row[f"{label}_{basis}_peak_error"] = round(
                    float(m[ok & p].mean() - a[ok & p].mean()), 3
                )
        ca, cc = _class_hourly(arm, y), _class_hourly(ctrl, y)
        cols = sorted(set(ca.columns) | set(cc.columns))
        de = {
            c: round((ca.get(c, 0).sum() - cc.get(c, 0).sum()) / 1e6, 4)
            for c in cols
        }
        row["class_energy_delta_twh"] = {k: v for k, v in de.items() if abs(v) > 1e-4}
        rep[str(y)] = row
    out["reported"] = rep

    gates = [out["K1_K4"]["pass"], out["K2"]["pass"], out["K6"]["pass"]]
    kills = [out["P1_P2_c3a_preview"]["P1_pass"], out["P1_P2_c3a_preview"]["P2_pass"], out["P4"]["pass"]]
    out["summary"] = {
        "construction_gates_pass": all(gates),
        "K3_live": out["K3"]["pass"],
        "kills_clear_preview": all(kills),
        "note": "P3 (C1) and P5 (forced share) are read from calibration_verdict/"
        "legitimacy_diagnostics at registration — authoritative criteria come "
        "from the production scorer, never from this preview.",
    }

    dest = Path(args.out)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["summary"], indent=1))
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
