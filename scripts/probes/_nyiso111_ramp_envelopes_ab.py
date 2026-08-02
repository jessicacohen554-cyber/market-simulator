#!/usr/bin/env python3
"""nyiso-111 A/B gate scorer — PREREG-nyiso111-ramp-envelopes-2026-08-02.

Evaluates the pre-registered construction gates (K1-K6) and the kill gates it
can measure directly (P1, P3, P5; P2/P4 are read authoritatively from
``calibration_verdict`` / ``legitimacy_diagnostics`` at registration) for the
single-delta ``ramp_limits=True`` arm against its same-HEAD zero-delta control,
plus the REPORTED-never-gated amplitude movement.

Structure follows ``_nyiso110_spin_online_ab.py``; the ramp-specific legs (K3
liveness and K6 effectiveness) reuse the pre-check probe's own loader-backed
measurement so the MW compared against are exactly the rows the LP imposed.

Usage:
    PYTHONPATH=.:src python scripts/probes/_nyiso111_ramp_envelopes_ab.py \
        --control results/calibration/nyiso111_control_A \
        --arm results/calibration/nyiso111_rampenv_B \
        --keeper results/calibration/nyiso109_zonalanchor_B \
        --out results/calibration/_nyiso111_ramp_envelopes_ab.json
"""

from __future__ import annotations

import argparse
import gzip
import importlib.util
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


def _precheck_module():
    spec = importlib.util.spec_from_file_location(
        "_nyiso111_precheck", Path(__file__).with_name("_nyiso111_ramp_envelope_precheck.py")
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _system(bundle: Path, year: int):
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[(s["zone"].isin(MODEL_ZONES)) & (s["pass"] == "P1")]
    price = s.pivot_table(index="hour", columns="zone", values="price")[list(MODEL_ZONES)].reindex(range(HOURS))
    dem = s.pivot_table(index="hour", columns="zone", values="demand")[list(MODEL_ZONES)].reindex(range(HOURS))
    slack = s.pivot_table(index="hour", columns="zone", values="slack")[list(MODEL_ZONES)].reindex(range(HOURS))
    dump = s.pivot_table(index="hour", columns="zone", values="dump")[list(MODEL_ZONES)].reindex(range(HOURS))
    return price, dem, slack, dump


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    return c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")


def _lw_price(price: pd.DataFrame, dem: pd.DataFrame) -> np.ndarray:
    return np.average(price.to_numpy(float), weights=dem.to_numpy(float), axis=1)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", default="results/calibration/nyiso111_control_A")
    ap.add_argument("--arm", default="results/calibration/nyiso111_rampenv_B")
    ap.add_argument("--keeper", default="results/calibration/nyiso109_zonalanchor_B")
    ap.add_argument("--out", default="results/calibration/_nyiso111_ramp_envelopes_ab.json")
    ap.add_argument("--skip-ramp-legs", action="store_true", help="skip K3/K6 (they rebuild a fleet per year)")
    args = ap.parse_args(argv)
    ctrl, arm, keeper = Path(args.control), Path(args.arm), Path(args.keeper)

    out: dict = {"control": str(ctrl), "arm": str(arm), "keeper": str(keeper)}

    # K1 — single delta.
    cfg_c = json.loads((ctrl / "run_config.json").read_text())["scenario_config"]
    cfg_a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diff = {k: (cfg_c.get(k), cfg_a.get(k)) for k in sorted(set(cfg_c) | set(cfg_a)) if cfg_c.get(k) != cfg_a.get(k)}
    out["K1"] = {"config_diff": diff, "pass": diff == {"ramp_limits": (False, True)}}

    # K2 — control integrity against the committed keeper (<= 1.0 MW).
    k2 = {}
    for y in YEARS:
        a, b = _class_hourly(ctrl, y), _class_hourly(keeper, y)
        cols = sorted(set(a.columns) | set(b.columns))
        a = a.reindex(columns=cols).fillna(0.0)
        b = b.reindex(columns=cols).fillna(0.0)
        k2[str(y)] = float(np.abs(a.to_numpy() - b.to_numpy()).max())
    out["K2"] = {"max_abs_class_hour_delta_mw": k2, "pass": max(k2.values()) <= 1.0}

    # K5 — span.
    span_c = json.loads((ctrl / "meta.json").read_text())["years"]
    span_a = json.loads((arm / "meta.json").read_text())["years"]
    out["K5"] = {
        "control_years": span_c,
        "arm_years": span_a,
        "pass": sorted(span_c) == sorted(span_a) == [2023, 2024, 2025],
    }

    # K3 / K6 — liveness and effectiveness, on the loader's own rows.
    if not args.skip_ramp_legs:
        pc = _precheck_module()
        k36 = {}
        for y in YEARS:
            rc = pc.measure(REPO / args.keeper if not Path(args.keeper).is_absolute() else keeper, ctrl, y)
            ra = pc.measure(REPO / args.keeper if not Path(args.keeper).is_absolute() else keeper, arm, y)
            drop = (
                None
                if not rc.get("infeasible_ramp_mwh_total")
                else round(100.0 * (1.0 - ra["infeasible_ramp_mwh_total"] / rc["infeasible_ramp_mwh_total"]), 2)
            )
            k36[str(y)] = {
                "groups": rc.get("n_groups_with_rows"),
                "enveloped_capacity_mw": rc.get("enveloped_capacity_mw"),
                "control_crossings": rc.get("crossings_up", 0) + rc.get("crossings_dn", 0),
                "arm_crossings": ra.get("crossings_up", 0) + ra.get("crossings_dn", 0),
                "control_infeasible_mwh": rc.get("infeasible_ramp_mwh_total"),
                "arm_infeasible_mwh": ra.get("infeasible_ramp_mwh_total"),
                "infeasible_drop_pct": drop,
                "control_crossing_share_pct": rc.get("crossing_share_pct"),
                "arm_crossing_share_pct": ra.get("crossing_share_pct"),
            }
        out["K3"] = {
            "per_year": {y: {"groups": v["groups"], "enveloped_capacity_mw": v["enveloped_capacity_mw"]} for y, v in k36.items()},
            "pass": all(v["groups"] >= 40 and v["enveloped_capacity_mw"] >= 15000 for v in k36.values()),
        }
        out["K6"] = {
            "per_year": k36,
            "pass": all(v["infeasible_drop_pct"] is not None and v["infeasible_drop_pct"] >= 70.0 for v in k36.values()),
        }

    # P1 — C3a band preview (rt_lw basis).
    c3a = {}
    for y in YEARS:
        bench = json.load(gzip.open(REPO / "frontend/data/backcast/bench/NYISO" / f"{y}.json.gz"))
        rt_lw = float(bench["bench"]["avgLMP"]["rt_lw"])
        row = {"actual_rt_lw": rt_lw}
        for label, b in (("control", ctrl), ("arm", arm)):
            price, dem, _, _ = _system(b, y)
            m = float(np.average(_lw_price(price, dem), weights=dem.sum(axis=1)))
            row[label] = round((m / rt_lw - 1.0) * 100.0, 3)
        c3a[str(y)] = row
    out["P1_c3a"] = {"per_year": c3a, "pass": all(abs(c3a[str(y)]["arm"]) <= 10.0 for y in YEARS)}

    # P3 — C3c: model hours above $300 (system.parquet basis, max zone and LW).
    p3 = {}
    for y in YEARS:
        row = {}
        for label, b in (("control", ctrl), ("arm", arm)):
            price, dem, _, _ = _system(b, y)
            row[f"{label}_hours_gt300_maxzone"] = int((price.to_numpy(float).max(axis=1) > 300.0).sum())
            row[f"{label}_hours_gt300_lw"] = int((_lw_price(price, dem) > 300.0).sum())
        p3[str(y)] = row
    out["P3_c3c"] = {
        "per_year": p3,
        "pass": all(
            p3[str(y)]["arm_hours_gt300_maxzone"] >= p3[str(y)]["control_hours_gt300_maxzone"] for y in YEARS
        ),
        "note": "actual >$300 counts are 10/12/42; the keeper models 3/0/7. The gate is "
        "'the arm does not move FURTHER from actual', i.e. arm >= control given the model under-produces.",
    }

    # P5 — feasibility.
    p5 = {}
    for y in YEARS:
        row = {}
        for label, b in (("control", ctrl), ("arm", arm)):
            _, _, sl, du = _system(b, y)
            row[f"{label}_slack_mwh"] = round(float(np.nansum(sl.to_numpy(float))), 3)
            row[f"{label}_dump_mwh"] = round(float(np.nansum(du.to_numpy(float))), 3)
        p5[str(y)] = row
    out["P5_feasibility"] = {
        "per_year": p5,
        "pass": all(p5[str(y)]["arm_slack_mwh"] <= 1e-6 and p5[str(y)]["arm_dump_mwh"] <= 1e-6 for y in YEARS),
    }

    # REPORTED, never gated: amplitude + class energy deltas.
    rep = {}
    act = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
    hod = np.arange(HOURS) % 24
    for y in YEARS:
        hub = act[act["year"] == y].set_index("hour").reindex(range(HOURS))
        row = {}
        for label, b in (("control", ctrl), ("arm", arm)):
            price, dem, _, _ = _system(b, y)
            m = _lw_price(price, dem)
            t, p = np.isin(hod, TROUGH), np.isin(hod, PEAK)
            for basis in ("da", "rt"):
                a = hub[basis].to_numpy(float)
                ok = np.isfinite(a)
                sw_m = float(m[ok & p].mean() - m[ok & t].mean())
                sw_a = float(a[ok & p].mean() - a[ok & t].mean())
                row[f"{label}_{basis}_swing_share"] = round(sw_m / sw_a, 4)
                row[f"{label}_{basis}_peak_error"] = round(float(m[ok & p].mean() - a[ok & p].mean()), 3)
                row[f"{label}_{basis}_trough_error"] = round(float(m[ok & t].mean() - a[ok & t].mean()), 3)
        ca, cc = _class_hourly(arm, y), _class_hourly(ctrl, y)
        cols = sorted(set(ca.columns) | set(cc.columns))
        de = {c: round(float(ca.get(c, 0).sum() - cc.get(c, 0).sum()) / 1e6, 4) for c in cols}
        row["class_energy_delta_twh"] = {k: v for k, v in de.items() if abs(v) > 1e-4}
        rep[str(y)] = row
    out["reported"] = rep

    ks = [out["K1"]["pass"], out["K2"]["pass"], out["K5"]["pass"]]
    if "K3" in out:
        ks += [out["K3"]["pass"], out["K6"]["pass"]]
    out["summary"] = {
        "construction_gates_pass": all(ks),
        "kills_clear_preview": all(
            [out["P1_c3a"]["pass"], out["P3_c3c"]["pass"], out["P5_feasibility"]["pass"]]
        ),
        "note": "P2 (C1) and P4 (C8 forced share) are read from calibration_verdict / "
        "legitimacy_diagnostics at registration; the authoritative criterion verdicts "
        "come from the registration pipeline, not from this scorer.",
    }

    o = Path(args.out)
    if not o.is_absolute():
        o = REPO / o
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "reported"}, indent=1)[:6000])
    print(f"\nwrote {o}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
