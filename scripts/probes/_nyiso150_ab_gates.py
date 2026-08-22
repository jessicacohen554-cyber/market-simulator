#!/usr/bin/env python3
"""nyiso-150 — score ARM C′ (cc_reserve_duty_split re-arm) and ARM W
(nyiso_iroquois_winter_spread) against PREREG-nyiso150.

Evaluates the kill gates of
``results/calibration/PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md``
on the solved bundles plus the arms' solve logs — no solve, no LP. Each arm is
ONE ``scenario_config`` field against the control
(``nyiso150_control``, the keeper recipe replayed at HEAD); the two are scored
independently. The C-K5 / W-K5 criteria legs are recorded by the session from
``calibration_verdict.py`` on the registered runs (this probe reports the
bundle-side gates).

Writes ``results/calibration/_nyiso150_ab_gates.json``. Exit 0 whatever the
verdict — this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/nyiso149_armF"
CONTROL = REPO / "results/calibration/nyiso150_control"
ARM_C = REPO / "results/calibration/nyiso150_armC"
ARM_W = REPO / "results/calibration/nyiso150_armW"
REF = REPO / "data/raw/_validation-source/actual_lmp.json"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
PHASE0_MINRUN = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
OUT = REPO / "results/calibration/_nyiso150_ab_gates.json"

YEARS = (2023, 2024, 2025)
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
DOWNSTATE = ("Capital_Hudson", "NYC", "Long_Island")
FLAG_C = "cc_reserve_duty_split"
FLAG_W = "nyiso_iroquois_winter_spread"

# PREREG §3 (verbatim nyiso-146b §C): frozen cohort and object plants.
COHORT = (10620, 7784, 50744, 54593, 54592, 10621, 54034)
OBJECT_PLANTS = (50744, 54592, 54593, 7784)
NO_DEGRADE = (
    [(56940, y) for y in YEARS]
    + [(55405, y) for y in YEARS]
    + [(56196, y) for y in YEARS]
    + [(2511, y) for y in YEARS]
    + [(2500, y) for y in YEARS]
    + [(50292, y) for y in YEARS]
    + [(57185, 2024), (57185, 2025), (56234, 2024), (56234, 2025)]
)

# PREREG §4 W-K3(a): gated winter months (the nyiso-82 decisively-fixed
# three); Jan-2025 and the summer months are reported, never gated.
GATED_WINTER = [(2023, 2), (2024, 12), (2025, 2)]
REPORTED_MONTHS = [(2025, 1), (2025, 6), (2025, 7), (2025, 12), (2024, 1), (2024, 7), (2023, 1), (2023, 12)]


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))].copy()


def _zone_month(df: pd.DataFrame, year: int) -> pd.DataFrame:
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df = df.copy()
    df["month"] = df["hour"].map(dict(enumerate(idx.month)))
    return df.groupby(["zone", "month"])["price"].mean().unstack("month")


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _plant_starts(bundle: Path, year: int, code: int) -> tuple[int, float] | None:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "unit_id", "hour", "mw", "cap_mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    if df.empty:
        return None
    cap = float(df.groupby("unit_id")["cap_mw"].max().sum())
    s = df.groupby("hour")["mw"].sum().sort_index().to_numpy()
    on = s > 0.05 * cap
    r = _runs(on)
    lens = [e - s0 for s0, e in r]
    return len(r), (float(np.median(lens)) if lens else 0.0)


def _plant_energy(bundle: Path, year: int, code: int) -> float:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    return float(df["mw"].sum()) / 1e3 if not df.empty else 0.0


def _e923_gwh() -> dict[tuple[int, int], float]:
    d = pd.read_parquet(E923)
    d = d[(d["ba_code"] == "NYIS") & (d["year"].isin(YEARS))]
    g = d.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
    return {(int(p), int(y)): v / 1e3 for (p, y), v in g.items()}


def _metered_starts() -> dict[tuple[int, int], int]:
    rec = json.loads(PHASE0_MINRUN.read_text())
    out = {}
    for p in rec["plants"]:
        for year, n in zip(YEARS, p.get("plant_runs_by_year") or []):
            out[(int(p["plant_code"]), year)] = int(n)
    return out


def _d4_fails(diag: dict) -> set[tuple]:
    return {
        (int(r["year"]), str(r["floor"]), str(r["plant"]))
        for r in diag["diagnostics"]["D4"]["rows"]
        if str(r.get("verdict", "")).upper() == "FAIL"
    }


def _d2_shares(diag: dict) -> dict:
    return {
        (int(r["year"]), str(r["mechanism"]), str(r["class"])): float(
            r["share_of_class"]
        )
        for r in diag["diagnostics"]["D2"]["rows"]
    }


def _d1_miss(diag: dict) -> set:
    return {
        (int(r["year"]), str(r["class"]))
        for r in diag["diagnostics"]["D1"]["rows"]
        if str(r.get("verdict", "")).lower() not in ("pass", "exempt", "skip")
    }


def _k1(mc: dict, ma: dict, flag: str) -> dict:
    provenance = {"timestamp", "note", "run_id", "git", "git_sha", "basis_sha",
                  "out_dir", "label"}
    diff = sorted(
        k for k in set(mc) | set(ma)
        if mc.get(k) != ma.get(k) and k not in provenance
    )
    return {
        "gate": f"K1 exactness ({flag})",
        "solve_field_diffs": diff,
        "passed": diff == [flag] and bool(ma.get(flag)) and not mc.get(flag),
    }


def _k4(dc: dict, da: dict, tag: str) -> dict:
    fc, fa = _d4_fails(dc), _d4_fails(da)
    new_d4 = sorted(fa - fc)
    sc, sa = _d2_shares(dc), _d2_shares(da)
    rises = sorted(
        (
            {"key": list(k), "ctl": round(sc.get(k, 0.0), 4), "arm": round(v, 4)}
            for k, v in sa.items()
            if v > sc.get(k, 0.0) + 1e-6
        ),
        key=lambda r: r["key"],
    )
    new_d1 = sorted(_d1_miss(da) - _d1_miss(dc))
    escalated = bool(rises)
    return {
        "gate": f"{tag}-K4 D-4/D-2 (K6-prime)",
        "new_d4_failures": new_d4,
        "cleared_d4": sorted(fc - fa),
        "forced_share_rises": rises,
        "escalated": escalated,
        "new_d1_misses": new_d1,
        "passed": (not new_d4) and ((not escalated) or not new_d1),
    }


def ident_gate() -> dict:
    """Control replay reproduces the registered keeper bit-exactly (prices)."""
    worst = 0.0
    for year in YEARS:
        a = _system(KEEPER, year).sort_values(["zone", "hour"])["price"].to_numpy()
        b = _system(CONTROL, year).sort_values(["zone", "hour"])["price"].to_numpy()
        worst = max(worst, float(np.abs(a - b).max()))
    return {"gate": "IDENT control == keeper", "max_abs_dprice": worst,
            "passed": worst == 0.0}


def score_arm_c(arm_log: Path) -> list[dict]:
    mc, ma = _meta(CONTROL), _meta(ARM_C)
    dc, da = _diag(CONTROL), _diag(ARM_C)
    gates = [_k1(mc, ma, FLAG_C)]
    log_txt = arm_log.read_text()
    armed = "cc_reserve_duty_split armed: 7 measured reserve-duty" in log_txt
    e923 = _e923_gwh()
    rows, ok = [], armed
    for code in OBJECT_PLANTS:
        for year in YEARS:
            c = _plant_energy(CONTROL, year, code)
            a = _plant_energy(ARM_C, year, code)
            act = e923.get((code, year))
            fall = (c - a) / c if c > 0 else 0.0
            gated = year in (2023, 2024)
            hit = (fall >= 0.80) if gated else None
            if gated:
                ok = ok and bool(hit)
            rows.append({"plant": code, "year": year, "ctl_gwh": round(c, 1),
                         "arm_gwh": round(a, 1),
                         "e923_gwh": round(act, 1) if act else None,
                         "fall": round(fall, 3), "gated": gated, "ok": hit})
    gates.append({"gate": "C-K2 liveness (cohort armed + >=80% collapse)",
                  "cohort_log_line": armed, "object_plants": rows, "passed": ok})
    metered = _metered_starts()
    cohort, ok3 = [], True
    for code, year in NO_DEGRADE + [(2539, y) for y in YEARS] + [(7314, y) for y in YEARS]:
        c = _plant_starts(CONTROL, year, code)
        a = _plant_starts(ARM_C, year, code)
        m = metered.get((code, year))
        if c is None or a is None or m is None:
            cohort.append({"plant": code, "year": year, "skipped": True})
            continue
        ce, ae = abs(c[0] - m), abs(a[0] - m)
        hit = ae <= 1.5 * ce + 5
        ok3 = ok3 and hit
        cohort.append({"plant": code, "year": year, "metered": m, "ctl": c[0],
                       "arm": a[0], "ok": hit})
    beth_energy = [
        {"year": y, "ctl_gwh": round(_plant_energy(CONTROL, y, 2539), 1),
         "arm_gwh": round(_plant_energy(ARM_C, y, 2539), 1),
         "e923_gwh": round(e923.get((2539, y), 0.0), 1)}
        for y in YEARS
    ]
    gates.append({"gate": "C-K3 no-degrade", "rows": cohort,
                  "bethlehem_energy_reported": beth_energy, "passed": ok3})
    gates.append(_k4(dc, da, "C"))
    gates.append({"gate": "C-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    # C-K6 gate-side: C-K2 per-year legs are the 2023/2024 rows above.
    k2rows = [r for g in gates if g["gate"].startswith("C-K2")
              for r in g["object_plants"]]
    per_year_ok = all(
        r["ok"] for r in k2rows if r["gated"]
    )
    gates.append({"gate": "C-K6 LOYO (gate-side: C-K2 per-year)",
                  "passed": per_year_ok})
    return gates


def score_arm_w() -> list[dict]:
    ref = json.loads(REF.read_text())["NYISO"]
    mc, ma = _meta(CONTROL), _meta(ARM_W)
    dc, da = _diag(CONTROL), _diag(ARM_W)
    gates = [_k1(mc, ma, FLAG_W)]

    # Pre-compute zone-month tables for control and arm.
    zm_c, zm_a, act = {}, {}, {}
    for year in YEARS:
        zm_c[year] = _zone_month(_system(CONTROL, year), year)
        zm_a[year] = _zone_month(_system(ARM_W, year), year)
        act[year] = ref[str(year)]["zones"]

    # W-K2(c): LP liveness — DJF mean |dLMP| > $1/MWh (pooled over years).
    deltas = []
    for year in YEARS:
        for m in (1, 2, 12):
            for z in ZONES:
                deltas.append(abs(zm_a[year].loc[z, m] - zm_c[year].loc[z, m]))
    djf_mean = float(np.mean(deltas))
    gates.append({"gate": "W-K2c LP liveness (DJF mean |dLMP|)",
                  "djf_mean_abs_dlmp": round(djf_mean, 3),
                  "passed": djf_mean > 1.0})

    # W-K3(a): gated winter months — spread recovery >=30 %, overshoot kill.
    rows, ok_a = [], True
    for (year, m) in GATED_WINTER + [(y, mm) for (y, mm) in REPORTED_MONTHS]:
        gated = (year, m) in GATED_WINTER
        uw_c = float(zm_c[year].loc["Upstate_West", m])
        uw_a = float(zm_a[year].loc["Upstate_West", m])
        uw_act = float(act[year]["Upstate_West"]["rt_mon"][m - 1])
        for z in DOWNSTATE:
            mz_c = float(zm_c[year].loc[z, m])
            mz_a = float(zm_a[year].loc[z, m])
            z_act = float(act[year][z]["rt_mon"][m - 1])
            sp_c, sp_a = mz_c - uw_c, mz_a - uw_a
            sp_act = z_act - uw_act
            gap_c = sp_act - sp_c
            rec = (sp_a - sp_c) / gap_c if abs(gap_c) > 1e-9 else 1.0
            overshoot = (mz_a - z_act) / z_act > 0.15
            hit = (rec >= 0.30) and not overshoot if gated else None
            if gated:
                ok_a = ok_a and bool(hit)
            rows.append({"year": year, "month": m, "zone": z, "gated": gated,
                         "spread_ctl": round(sp_c, 1), "spread_arm": round(sp_a, 1),
                         "spread_actual": round(sp_act, 1),
                         "recovery": round(rec, 3),
                         "model_ctl": round(mz_c, 1), "model_arm": round(mz_a, 1),
                         "actual": round(z_act, 1),
                         "overshoot": overshoot, "ok": hit})
    gates.append({"gate": "W-K3a gated winter spread recovery >=30% (no overshoot >+15%)",
                  "rows": rows, "passed": ok_a})

    # W-K3(b): annual gradient doubles toward actual, <= 1.10x actual.
    grads, ok_b = [], True
    for year in (2024, 2025):
        gm_c = float(zm_c[year].mean(axis=1).max() - zm_c[year].mean(axis=1).min())
        ann_c = _system(CONTROL, year).groupby("zone")["price"].mean()
        ann_a = _system(ARM_W, year).groupby("zone")["price"].mean()
        g_c = float(ann_c[ZONES].max() - ann_c[ZONES].min())
        g_a = float(ann_a[ZONES].max() - ann_a[ZONES].min())
        g_act = max(act[year][z]["rt"] for z in ZONES) - min(
            act[year][z]["rt"] for z in ZONES
        )
        hit = (g_a >= 2.0 * g_c or g_a >= g_act) and g_a <= 1.10 * g_act
        ok_b = ok_b and hit
        grads.append({"year": year, "gradient_ctl": round(g_c, 2),
                      "gradient_arm": round(g_a, 2),
                      "gradient_actual": round(g_act, 2), "ok": hit})
    gates.append({"gate": "W-K3b annual gradient toward actual (2024+2025)",
                  "rows": grads, "passed": ok_b})

    # W-K3(c): UW-2023 annual over-pricing strictly improves.
    uw23_c = float(_system(CONTROL, 2023).groupby("zone")["price"].mean()["Upstate_West"])
    uw23_a = float(_system(ARM_W, 2023).groupby("zone")["price"].mean()["Upstate_West"])
    uw23_act = float(act[2023]["Upstate_West"]["rt"])
    ok_c = abs(uw23_a - uw23_act) < abs(uw23_c - uw23_act)
    gates.append({"gate": "W-K3c UW-2023 annual improves",
                  "ctl": round(uw23_c, 2), "arm": round(uw23_a, 2),
                  "actual": round(uw23_act, 2), "passed": ok_c})

    # W-K3(d): anti-relocation — worst-zone |annual err| must not worsen.
    reloc, ok_d = [], True
    for year in YEARS:
        ann_c = _system(CONTROL, year).groupby("zone")["price"].mean()
        ann_a = _system(ARM_W, year).groupby("zone")["price"].mean()
        wc = max(abs(float(ann_c[z]) - act[year][z]["rt"]) / act[year][z]["rt"]
                 for z in ZONES)
        wa = max(abs(float(ann_a[z]) - act[year][z]["rt"]) / act[year][z]["rt"]
                 for z in ZONES)
        hit = wa <= wc + 1e-9
        ok_d = ok_d and hit
        reloc.append({"year": year, "worst_ctl_pct": round(100 * wc, 1),
                      "worst_arm_pct": round(100 * wa, 1), "ok": hit})
    gates.append({"gate": "W-K3d anti-relocation (worst zone |ann err|)",
                  "rows": reloc, "passed": ok_d})

    gates.append(_k4(dc, da, "W"))
    gates.append({"gate": "W-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    # W-K6 gate-side is W-K3a per gated month + W-K3b per year — both
    # already evaluated per-unit above.
    gates.append({"gate": "W-K6 LOYO (gate-side per-month/per-year legs)",
                  "passed": ok_a and ok_b})

    # ADV-W1/W2 report tables: summer downstate + UW winter months.
    adv = []
    for year in YEARS:
        for m in (1, 2, 6, 7, 12):
            for z in ZONES:
                mz_c = float(zm_c[year].loc[z, m])
                mz_a = float(zm_a[year].loc[z, m])
                z_act = float(act[year][z]["rt_mon"][m - 1])
                adv.append({"year": year, "month": m, "zone": z,
                            "ctl": round(mz_c, 1), "arm": round(mz_a, 1),
                            "actual": round(z_act, 1)})
    gates.append({"gate": "ADV-W1/W2 monthly report (reported, not gated)",
                  "rows": adv, "passed": None})
    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-c-log", type=Path)
    ap.add_argument("--arm-w", action="store_true", help="score ARM W")
    ap.add_argument("--ident-only", action="store_true")
    args = ap.parse_args()
    result: dict = {"session": "nyiso-150", "control": CONTROL.name, "arms": {}}
    result["ident"] = ident_gate()
    print(f"{'PASS' if result['ident']['passed'] else 'FAIL':9s} IDENT "
          f"(max |dprice| {result['ident']['max_abs_dprice']})")
    if not args.ident_only:
        if args.arm_c_log:
            gates = score_arm_c(args.arm_c_log)
            result["arms"]["C"] = gates
            print("--- ARM C' ---")
            for g in gates:
                state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
                print(f"{state:9s} {g['gate']}")
        if args.arm_w:
            gates = score_arm_w()
            result["arms"]["W"] = gates
            print("--- ARM W ---")
            for g in gates:
                state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
                print(f"{state:9s} {g['gate']}")
    if OUT.exists():
        prior = json.loads(OUT.read_text())
        prior.update({k: v for k, v in result.items() if k != "arms"})
        prior.setdefault("arms", {}).update(result["arms"])
        result = prior
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
