#!/usr/bin/env python3
"""nyiso-146 — score the per-plant min-run A/B against its pre-registration.

Evaluates the kill gates of
``results/calibration/PREREG-nyiso146-perplant-min-run-2026-08-19.md`` on the
two committed bundles plus the arms' solve logs and registered run payloads —
no solve, no LP.

* **K1 EXACTNESS** — exactly ONE ``scenario_config`` field differs between the
  arms, and it is ``nyiso_gas_bridge_plant_min_run``.
* **K2(a) FLOOR, EXACT** — the arm's per-leg bridge floor volumes (the solve
  log's own ``bridge leg`` lines, the only place the floor VOLUME is reported)
  land within ±2 % of the control-side capture's deterministic prediction.
  Corroboration: 2539's D-4 binding energy rises and 2517's falls, every year.
* **K2(b) STARTS, BANDED** — Bethlehem's P1 starts fall ≥50 % in 2023 and
  ≥10 % in 2024/2025 (the §4 mechanism-shape prediction).
* **K3 THE OBJECT** — 2539 starts strictly fall and median run length rises in
  all years; the no-degrade cohort stays within 1.5×control error + 5 starts;
  Flynn ≤ control + 25 %.
* **K4 D-4/D-2 (K6-prime form)** — zero new D-4 unit-conduct failures; the
  pre-registered CC forced-share rise escalates and clears only with zero new
  D-4 failures AND zero new D-1 shape misses.
* **K5** — reported: the production scorer (``calibration_verdict.py``) is the
  only thing that may declare criterion verdicts; this probe just records the
  pointer.
* **K6(a)** — derive-side LOYO, already measured and cleared ex ante in the
  prereg; recorded verbatim.

Writes ``results/calibration/_nyiso146_ab_gates.json`` and prints a verdict
table. Exit status is 0 whatever the verdict — this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

CONTROL = REPO / "results/calibration/nyiso146_control"
ARM = REPO / "results/calibration/nyiso146_perplant_arm"
YEARS = (2023, 2024, 2025)
FLAG = "nyiso_gas_bridge_plant_min_run"
BRIDGE = "nyiso_gas_commitment_bridge"
K2_PRED = REPO / "results/calibration/_nyiso146_k2_prediction.json"
PHASE0 = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
OUT = REPO / "results/calibration/_nyiso146_ab_gates.json"

# Predicted ARM per-leg floor volumes (TWh) from the control-side capture
# (PREREG §5 K2(a); scripts/probes/_nyiso146_k2_prediction.py log record).
PRED_LEG_TWH = {
    ("gas_cc", 2023): 2.4508,
    ("gas_st", 2023): 0.1172,
    ("gas_cc", 2024): 1.8400,
    ("gas_st", 2024): 0.1343,
    ("gas_cc", 2025): 1.4399,
    ("gas_st", 2025): 0.1150,
}
K2A_TOL = 0.02

# K3 cohort definitions (PREREG §5 K3). no_degrade holds (plant, year) pairs.
NO_DEGRADE = (
    [(56940, y) for y in YEARS]
    + [(55405, y) for y in YEARS]
    + [(56196, y) for y in YEARS]
    + [(2511, y) for y in YEARS]
    + [(2500, y) for y in YEARS]
    + [(50292, y) for y in YEARS]
    + [(57185, 2024), (57185, 2025), (56234, 2024), (56234, 2025)]
)

_LEG_RE = re.compile(
    r"NYISO gas bridge leg (\w+) \(min_load_frac [\d.]+, min_run [\w.]+\): "
    r"\d+ unit-hours floored, ([\d.]+) TWh floor volume"
)


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _plant_starts(payload: dict, year: int, code: int) -> tuple[int, float] | None:
    """(starts, median run h) for a plant at 0.05 x its total capacity.

    Sums every class slice of the plant code (the bench wire-key convention,
    nyiso-88 §5) so the model series matches the whole-facility CAMPD basis.
    """
    from scripts.legitimacy_diagnostics import _decode_cf_bytes

    pl = payload["years"][str(year)]["plants"]
    keys = [k for k in pl if k.split(":")[0] == str(code)]
    if not keys:
        return None
    total = None
    cap = 0.0
    for k in keys:
        v = pl[k]
        arr = _decode_cf_bytes(v["m"], v.get("m_ann"), float(v["cap"]))
        total = arr if total is None else total + arr
        cap += float(v["cap"])
    on = total > 0.05 * cap
    r = _runs(on)
    lens = [e - s for s, e in r]
    return len(r), (float(np.median(lens)) if lens else 0.0)


def _parse_leg_volumes(log: Path) -> dict[tuple[str, int], float]:
    """Map (fuel, year) -> floor volume TWh from a 3-year solve log.

    The solve runs years sequentially in YEARS order and logs one line per
    armed leg per year, in leg order — so pairs are assigned positionally.
    """
    vols: list[tuple[str, float]] = [
        (m.group(1), float(m.group(2)))
        for m in _LEG_RE.finditer(log.read_text())
    ]
    out: dict[tuple[str, int], float] = {}
    per_year = {}
    for fuel, v in vols:
        per_year.setdefault(fuel, []).append(v)
    for fuel, series in per_year.items():
        if len(series) != len(YEARS):
            raise SystemExit(
                f"{log}: expected {len(YEARS)} '{fuel}' leg lines, got "
                f"{len(series)} — is this a single 3-year solve log?"
            )
        for year, v in zip(YEARS, series):
            out[(fuel, year)] = v
    return out


def _bridge_rows(diag: dict) -> list[dict]:
    return [
        r
        for r in diag["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct" and BRIDGE in str(r.get("floor", ""))
    ]


def _metered_starts() -> dict[tuple[int, int], int]:
    """(plant, year) -> metered plant-basis run count, from the phase-0 record."""
    rec = json.loads(PHASE0.read_text())
    out = {}
    for p in rec["plants"]:
        for year, n in zip(YEARS, p.get("plant_runs_by_year") or []):
            out[(int(p["plant_code"]), year)] = int(n)
    return out


def k1(mc: dict, ma: dict) -> dict:
    """Exactly one scenario_config field differs, and it is the flag."""
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


def k2a(arm_log: Path, dc: dict, da: dict) -> dict:
    """Arm per-leg floor volumes within ±2 % of the deterministic prediction."""
    vols = _parse_leg_volumes(arm_log)
    rows, ok = [], True
    for (fuel, year), pred in sorted(PRED_LEG_TWH.items(), key=lambda x: (x[0][1], x[0][0])):
        got = vols.get((fuel, year))
        hit = got is not None and abs(got - pred) <= K2A_TOL * pred
        ok = ok and hit
        rows.append({"leg": fuel, "year": year, "predicted_twh": pred,
                     "measured_twh": got, "within_2pct": hit})
    # Corroboration from committed D-4 binding energy.
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
    return {"gate": "K2a floor exact", "legs": rows, "d4_corroboration": corr,
            "passed": ok}


def k2b_k3(pc: dict, pa: dict) -> tuple[dict, dict]:
    """K2(b) Bethlehem start bands + K3 object/no-degrade gates."""
    metered = _metered_starts()
    # K2(b) + K3(a): 2539.
    beth, ok2b, ok3a = [], True, True
    for year in YEARS:
        c = _plant_starts(pc, year, 2539)
        a = _plant_starts(pa, year, 2539)
        drop = (c[0] - a[0]) / c[0] if c and c[0] else 0.0
        bar = 0.50 if year == 2023 else 0.10
        ok2b = ok2b and drop >= bar
        ok3a = ok3a and a[0] < c[0] and a[1] > c[1]
        beth.append({"year": year, "ctl_starts": c[0], "arm_starts": a[0],
                     "metered": metered.get((2539, year)),
                     "drop_frac": round(drop, 3), "bar": bar,
                     "ctl_median_run_h": c[1], "arm_median_run_h": a[1]})
    # K3(b): no-degrade cohort.
    cohort, ok3b = [], True
    for code, year in NO_DEGRADE:
        c = _plant_starts(pc, year, code)
        a = _plant_starts(pa, year, code)
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
    # K3(c): Flynn no-degrade.
    flynn, ok3c = [], True
    for year in YEARS:
        c = _plant_starts(pc, year, 7314)
        a = _plant_starts(pa, year, 7314)
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
    """Zero new D-4 failures; forced-share escalation with the two K6' legs."""

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
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-log", type=Path, required=True,
                    help="the ARM's 3-year solve log (per-leg volume lines)")
    ap.add_argument("--control-payload", type=Path, required=True)
    ap.add_argument("--arm-payload", type=Path, required=True)
    args = ap.parse_args()

    from scripts.lib.backcast_artifacts import decode_run_js

    pc = decode_run_js(args.control_payload.read_text())
    pa = decode_run_js(args.arm_payload.read_text())
    mc, ma = _meta(CONTROL), _meta(ARM)
    dc, da = _diag(CONTROL), _diag(ARM)
    g_k2b, g_k3 = k2b_k3(pc, pa)
    result = {
        "session": "nyiso-146",
        "control": CONTROL.name,
        "arm": ARM.name,
        "gates": [
            k1(mc, ma),
            k2a(args.arm_log, dc, da),
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
