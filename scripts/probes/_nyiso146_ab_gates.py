#!/usr/bin/env python3
"""nyiso-146 — score the per-plant min-run A/B against its pre-registration.

Evaluates the kill gates of
``results/calibration/PREREG-nyiso146-perplant-min-run-2026-08-19.md`` on the
two committed bundles — no solve, no LP. Every quantity comes from bundle
artifacts: ``meta.json`` (K1), ``floors/<yr>_P1.npz`` (K2a — the persisted
floor matrix, bridge-attributed cells, mechanism code 20),
``hourly/unit_hourly_<yr>.parquet`` (K2b/K3 start counts at 0.05 x plant
capacity), ``legitimacy_diagnostics.json`` (K2a corroboration, K4).

* **K1 EXACTNESS** — exactly ONE ``scenario_config`` field differs, and it is
  ``nyiso_gas_bridge_plant_min_run``.
* **K2(a) FLOOR DELIVERY** — per-plant arm/control floor-volume ratios within
  ±25 % (relative) of the capture's predicted ratios, per-leg totals within
  ±5 % of the rebased predictions (PREREG §5, amended before the arm solved),
  and the D-4 corroboration (2539 binding energy rises, 2517 falls).
* **K2(b) STARTS** — Bethlehem's P1 starts fall ≥50 % in 2023, ≥10 % in
  2024/2025.
* **K3 THE OBJECT** — 2539 starts strictly fall and median run length rises
  in all years; no-degrade cohort within 1.5×control error + 5 starts;
  Flynn ≤ control + 25 %.
* **K4 D-4/D-2 (K6-prime form)** — zero new D-4 unit-conduct failures; the
  pre-registered forced-share rise escalates and clears only with zero new
  D-4 failures AND zero new D-1 shape misses.
* **K5** — pointer only: criterion verdicts belong to calibration_verdict.py.
* **K6(a)** — derive-side LOYO, measured and cleared ex ante in the prereg.

Writes ``results/calibration/_nyiso146_ab_gates.json``. Exit 0 whatever the
verdict — this reports, it does not gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CONTROL = REPO / "results/calibration/nyiso146_control"
ARM = REPO / "results/calibration/nyiso146_perplant_arm"
YEARS = (2023, 2024, 2025)
FLAG = "nyiso_gas_bridge_plant_min_run"
BRIDGE = "nyiso_gas_commitment_bridge"
BRIDGE_MECH_CODE = 20  # data.floor_mechanisms.MECH_NAMES index
PHASE0 = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
OUT = REPO / "results/calibration/_nyiso146_ab_gates.json"

# PREREG §5 K2(a): predicted per-plant arm/control floor ratios (capture
# basis, basis-robust) and the ±25 % relative band.
PRED_RATIO = {
    2539: {2023: 1.77, 2024: 1.23, 2025: 1.24},
    56234: {2023: 2.42, 2024: 3.84, 2025: 4.95},
    56940: {2023: 0.84, 2024: 0.61, 2025: 0.57},
    2517: {2023: 0.11, 2024: 0.32, 2025: 0.44},
    7314: {2023: 0.93, 2024: 0.96, 2025: 0.91},
}
RATIO_BAND = 0.25
# Rebased per-leg totals (TWh), ±5 %. Legs keyed by plant_group.
PRED_LEG_TWH = {
    ("CC_REGULAR", 2023): 2.4602,
    ("CC_REGULAR", 2024): 1.9179,
    ("CC_REGULAR", 2025): 1.4762,
    ("ST_GAS", 2023): 0.1196,
    ("ST_GAS", 2024): 0.1389,
    ("ST_GAS", 2025): 0.1124,
}
LEG_TOL = 0.05

NO_DEGRADE = (
    [(56940, y) for y in YEARS]
    + [(55405, y) for y in YEARS]
    + [(56196, y) for y in YEARS]
    + [(2511, y) for y in YEARS]
    + [(2500, y) for y in YEARS]
    + [(50292, y) for y in YEARS]
    + [(57185, 2024), (57185, 2025), (56234, 2024), (56234, 2025)]
)


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _bridge_floor_by_plant(bundle: Path, year: int) -> dict[int, float]:
    """{plant_code: bridge-attributed floor GWh} plus per-class totals."""
    z = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
    mg = np.where(z["mechanism"] == BRIDGE_MECH_CODE, z["min_gen"], 0.0)
    pc = z["plant_code"]
    out: dict[int, float] = {}
    for code in np.unique(pc):
        rows = np.flatnonzero(pc == code)
        v = float(mg[rows].sum()) / 1e3
        if v > 0.0:
            out[int(code)] = v
    return out


def _bridge_floor_by_class(bundle: Path, year: int) -> dict[str, float]:
    z = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
    mg = np.where(z["mechanism"] == BRIDGE_MECH_CODE, z["min_gen"], 0.0)
    pg = z["plant_group"]
    return {
        str(k): float(mg[np.flatnonzero(pg == k)].sum()) / 1e6
        for k in np.unique(pg)
        if str(k)
    }


def _plant_starts(bundle: Path, year: int, code: int) -> tuple[int, float] | None:
    """(starts, median run h) at 0.05 x plant capacity from unit_hourly."""
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "unit_id", "hour", "mw", "cap_mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    if df.empty:
        return None
    cap = float(df.groupby("unit_id")["cap_mw"].max().sum())
    series = df.groupby("hour")["mw"].sum().sort_index().to_numpy()
    on = series > 0.05 * cap
    r = _runs(on)
    lens = [e - s for s, e in r]
    return len(r), (float(np.median(lens)) if lens else 0.0)


def _metered_starts() -> dict[tuple[int, int], int]:
    rec = json.loads(PHASE0.read_text())
    out = {}
    for p in rec["plants"]:
        for year, n in zip(YEARS, p.get("plant_runs_by_year") or []):
            out[(int(p["plant_code"]), year)] = int(n)
    return out


def _bridge_rows(diag: dict) -> list[dict]:
    return [
        r
        for r in diag["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct" and BRIDGE in str(r.get("floor", ""))
    ]


def k1(mc: dict, ma: dict) -> dict:
    keys = set(mc) | set(ma)
    provenance = {"timestamp", "note", "run_id", "git", "git_sha", "basis_sha",
                  "out_dir", "label"}
    solve_diff = sorted(
        k for k in keys if mc.get(k) != ma.get(k) and k not in provenance
    )
    return {
        "gate": "K1 exactness",
        "solve_field_diffs": solve_diff,
        "flag_control": mc.get(FLAG),
        "flag_arm": ma.get(FLAG),
        "passed": solve_diff == [FLAG] and bool(ma.get(FLAG)) and not mc.get(FLAG),
    }


def k2a(dc: dict, da: dict) -> dict:
    rows, ok = [], True
    for code, by_year in PRED_RATIO.items():
        for year, pred in by_year.items():
            c = _bridge_floor_by_plant(CONTROL, year).get(code, 0.0)
            a = _bridge_floor_by_plant(ARM, year).get(code, 0.0)
            ratio = a / c if c > 0 else float("inf")
            hit = c > 0 and abs(ratio - pred) <= RATIO_BAND * pred
            ok = ok and hit
            rows.append({"plant": code, "year": year, "ctl_gwh": round(c, 2),
                         "arm_gwh": round(a, 2), "ratio": round(ratio, 3),
                         "predicted_ratio": pred, "ok": hit})
    legs = []
    for (klass, year), pred in sorted(PRED_LEG_TWH.items(), key=lambda x: (x[0][1], x[0][0])):
        got = _bridge_floor_by_class(ARM, year).get(klass, 0.0)
        hit = abs(got - pred) <= LEG_TOL * pred
        ok = ok and hit
        legs.append({"leg": klass, "year": year, "predicted_twh": pred,
                     "measured_twh": round(got, 4), "within_5pct": hit})
    rc, ra = _bridge_rows(dc), _bridge_rows(da)

    def _plant_year(rows_, code, year):
        return sum(
            float(r["floored_twh"]) for r in rows_
            if int(r["plant"]) == code and int(r["year"]) == year
        )

    corr = []
    for year in YEARS:
        c39, a39 = _plant_year(rc, 2539, year), _plant_year(ra, 2539, year)
        c17, a17 = _plant_year(rc, 2517, year), _plant_year(ra, 2517, year)
        rise = a39 > c39
        fall = a17 < c17 or (c17 == 0.0 and a17 == 0.0)
        ok = ok and rise and fall
        corr.append({"year": year, "2539_ctl": round(c39, 4), "2539_arm": round(a39, 4),
                     "2517_ctl": round(c17, 4), "2517_arm": round(a17, 4),
                     "rise_2539": rise, "fall_2517": fall})
    return {"gate": "K2a floor delivery", "per_plant": rows, "per_leg": legs,
            "d4_corroboration": corr, "passed": ok}


def k2b_k3() -> tuple[dict, dict]:
    metered = _metered_starts()
    beth, ok2b, ok3a = [], True, True
    for year in YEARS:
        c = _plant_starts(CONTROL, year, 2539)
        a = _plant_starts(ARM, year, 2539)
        drop = (c[0] - a[0]) / c[0] if c and c[0] else 0.0
        bar = 0.50 if year == 2023 else 0.10
        ok2b = ok2b and drop >= bar
        ok3a = ok3a and a[0] < c[0] and a[1] > c[1]
        beth.append({"year": year, "ctl_starts": c[0], "arm_starts": a[0],
                     "metered": metered.get((2539, year)),
                     "drop_frac": round(drop, 3), "bar": bar,
                     "ctl_median_run_h": c[1], "arm_median_run_h": a[1]})
    cohort, ok3b = [], True
    for code, year in NO_DEGRADE:
        c = _plant_starts(CONTROL, year, code)
        a = _plant_starts(ARM, year, code)
        m = metered.get((code, year))
        if c is None or a is None or m is None:
            cohort.append({"plant": code, "year": year, "skipped": "no series"})
            continue
        ce, ae = abs(c[0] - m), abs(a[0] - m)
        allowed = 1.5 * ce + 5
        hit = ae <= allowed
        ok3b = ok3b and hit
        cohort.append({"plant": code, "year": year, "metered": m,
                       "ctl_starts": c[0], "arm_starts": a[0],
                       "ctl_err": ce, "arm_err": ae,
                       "allowed": round(allowed, 1), "ok": hit})
    flynn, ok3c = [], True
    for year in YEARS:
        c = _plant_starts(CONTROL, year, 7314)
        a = _plant_starts(ARM, year, 7314)
        hit = a[0] <= c[0] * 1.25
        ok3c = ok3c and hit
        flynn.append({"year": year, "ctl_starts": c[0], "arm_starts": a[0],
                      "metered": metered.get((7314, year)), "ok": hit})
    k2b = {"gate": "K2b Bethlehem start bands", "years": beth, "passed": ok2b}
    k3 = {"gate": "K3 object + no-degrade", "bethlehem": beth,
          "no_degrade": cohort, "flynn": flynn,
          "passed": ok3a and ok3b and ok3c,
          "legs": {"a_2539": ok3a, "b_cohort": ok3b, "c_flynn": ok3c}}
    return k2b, k3


def k4(dc: dict, da: dict) -> dict:
    def fails(diag):
        return {
            (int(r["year"]), str(r["floor"]), str(r["plant"]))
            for r in diag["diagnostics"]["D4"]["rows"]
            if str(r.get("verdict", "")).upper() == "FAIL"
        }

    fc, fa = fails(dc), fails(da)
    new_d4 = sorted(fa - fc)

    def shares(diag):
        return {
            (int(r["year"]), str(r["mechanism"]), str(r["class"])): float(
                r["share_of_class"]
            )
            for r in diag["diagnostics"]["D2"]["rows"]
        }

    sc, sa = shares(dc), shares(da)
    rises = sorted(
        (
            {"key": list(k), "ctl": round(sc.get(k, 0.0), 4), "arm": round(v, 4)}
            for k, v in sa.items()
            if v > sc.get(k, 0.0) + 1e-6
        ),
        key=lambda r: r["key"],
    )

    def d1_miss(diag):
        return {
            (int(r["year"]), str(r["class"]))
            for r in diag["diagnostics"]["D1"]["rows"]
            if str(r.get("verdict", "")).lower() not in ("pass", "exempt", "skip")
        }

    m_c, m_a = d1_miss(dc), d1_miss(da)
    new_d1 = sorted(m_a - m_c)
    escalated = bool(rises)
    cleared = not new_d4 and not new_d1
    return {
        "gate": "K4 D-4/D-2 (K6-prime)",
        "control_d4_failures": len(fc),
        "arm_d4_failures": len(fa),
        "new_d4_failures": new_d4,
        "cleared_d4": sorted(fc - fa),
        "forced_share_rises": rises,
        "escalated": escalated,
        "new_d1_misses": new_d1,
        "passed": (not new_d4) and ((not escalated) or cleared),
    }


def main() -> int:
    mc, ma = _meta(CONTROL), _meta(ARM)
    dc, da = _diag(CONTROL), _diag(ARM)
    g_k2b, g_k3 = k2b_k3()
    result = {
        "session": "nyiso-146",
        "control": CONTROL.name,
        "arm": ARM.name,
        "gates": [
            k1(mc, ma),
            k2a(dc, da),
            g_k2b,
            g_k3,
            k4(dc, da),
            {
                "gate": "K5 gated criteria",
                "note": "declared only by scripts/calibration_verdict.py "
                "--run-id on the registered arms; recorded there",
                "passed": None,
            },
            {
                "gate": "K6a derive-side LOYO",
                "note": "measured and cleared ex ante in the prereg (2539 LOO "
                "p25 = 137/47/167.75 h; side-stability >= 2/3 for all 16 live "
                "plants)",
                "passed": True,
            },
        ],
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    for g in result["gates"]:
        state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
        print(f"{state:9s} {g['gate']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
