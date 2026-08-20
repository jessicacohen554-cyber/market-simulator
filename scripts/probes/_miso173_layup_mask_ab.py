"""miso-173 A/B scorer — the measured lay-up window mask arm.

Committed BEFORE either run's result is read, so the gates cannot be written
around the outcome. Scores ``PREREG-miso173-layup-window-mask-2026-08-20.md``
§5: gates M-0..M-7 for arm ``mustrun_layup_window_mask``.

Modes:

* ``--identity CONTROL KEEPER`` — the M-0 prerequisite, run and reported
  BEFORE any arm output is read. Every scored sidecar of every year must be
  bit-identical (``max|diff| = 0.0``, non-numeric columns equal).
* ``--gates CONTROL ARM`` — the arm's gates, scored from both bundles'
  committed artifacts, the two solves' own ``floors/<year>_P1.npz`` (M-1/M-2,
  the floor-VOLUME basis the miso-172 §4 lesson moved the kill band onto), and
  the committed instrument JSON
  (``results/calibration/_miso173_layup_mask_instrument.json``).

No LP is spent here.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

MECHS = ("st_gas_mustrun_per_plant", "cc_mustrun_per_plant")
MECH_ST_GAS_ID = 16  # market_sim.data.floor_mechanisms.MECH_ST_GAS_MUSTRUN_PER_PLANT
LIVE_PLANTS = (3459, 1403, 990, 1122, 3457, 1402, 6035)
INSTRUMENT = REPO / "results/calibration/_miso173_layup_mask_instrument.json"
YEARS = (2023, 2024, 2025)

# M-1 tolerance: max(0.005 TWh, 3 %) per plant-year vs the pre-solve ENGINE
# build (PREREG §5; absorbs the known miso-156 reconstruction residual).
M1_ABS_TWH = 0.005
M1_REL = 0.03
# M-2: mechanism-total delta volume within +-15 % of the engine prediction; an
# engine-flat plant-year unchanged within 0.1 % (or 0.0005 TWh).
M2_TOTAL_REL = 0.15
M2_FLAT_REL = 0.001
M2_FLAT_ABS_TWH = 0.0005
# M-3 reported bands: +-50 % of the predicted at-floor delta (PREREG §4).
D1_MIN_PROFILE_R = 0.80
D1_MIN_CV_RATIO = 0.5
D1_MAX_PROFILE_R_DROP = 0.05


def _legit(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _d4_rows(legit: dict) -> list[dict]:
    return list(legit["diagnostics"]["D4"]["rows"])


def _mech_of(row: dict) -> str:
    return str(row.get("floor", "")).split(" × ")[0]


def _d2_mech_twh(legit: dict, klass: str = "ST_GAS") -> dict[int, float]:
    out: dict[int, float] = {}
    for r in legit["diagnostics"]["D2"]["rows"]:
        if r.get("class") != klass or str(r.get("mechanism")) not in MECHS:
            continue
        out[int(r["year"])] = out.get(int(r["year"]), 0.0) + float(
            r.get("forced_twh") or 0.0
        )
    return out


def _d1_rows(legit: dict, klass: str = "ST_GAS") -> dict[int, dict]:
    out: dict[int, dict] = {}
    for r in legit["diagnostics"]["D1"]["rows"]:
        if r.get("class") == klass and r.get("year") is not None:
            out[int(r["year"])] = r
    return out


def _floor_volumes(bundle: Path, year: int) -> dict[int, float]:
    """Per-plant TWh of ST_GAS-mechanism floor volume from floors npz."""
    path = bundle / "floors" / f"{year}_P1.npz"
    if not path.exists():
        return {}
    z = np.load(path, allow_pickle=False)
    mg = np.asarray(z["min_gen"], dtype=float)
    mech = np.asarray(z["mechanism"])
    pc = np.asarray(z["plant_code"])
    out: dict[int, float] = {}
    sel = mech == MECH_ST_GAS_ID
    contrib = np.where(sel, mg, 0.0).sum(axis=1) / 1e6
    for i in np.flatnonzero(contrib > 0):
        out[int(pc[i])] = out.get(int(pc[i]), 0.0) + float(contrib[i])
    return out


def identity(control: Path, keeper: Path) -> dict:
    """M-0 — every scored sidecar of every year must be bit-identical."""
    out: dict = {"gate": "M-0", "files": [], "passed": True}
    for path in sorted((keeper / "hourly").glob("*.parquet")):
        other = control / "hourly" / path.name
        rec: dict = {"file": path.name}
        if not other.exists():
            rec.update(present=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        a, b = pd.read_parquet(path), pd.read_parquet(other)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            rec.update(shape_match=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        worst = 0.0
        nonnum_ok = True
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]):
                d = np.abs(a[col].to_numpy(dtype=float) - b[col].to_numpy(dtype=float))
                worst = max(worst, float(np.nanmax(d)) if len(d) else 0.0)
            else:
                nonnum_ok &= bool(a[col].equals(b[col]))
        ok = worst == 0.0 and nonnum_ok
        rec.update(max_abs_diff=worst, nonnumeric_equal=nonnum_ok, passed=ok)
        out["files"].append(rec)
        out["passed"] = bool(out["passed"] and ok)
    return out


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"calibration_verdict.py produced no JSON for {bundle}")
    return json.loads(res.stdout)


def _records(verdict: dict) -> dict[tuple, str]:
    out: dict[tuple, str] = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[(rec.get("criterion", name), rec.get("key"), rec.get("year"))] = (
                rec.get("status")
            )
    return out


def gates(control: Path, arm: Path) -> dict:
    inst = json.loads(INSTRUMENT.read_text())
    pred = inst["volume_predictions"]
    totals = inst["mechanism_totals"]
    lc, la = _legit(control), _legit(arm)
    res: dict = {"arm": "layupmask", "years": list(YEARS)}

    # --- M-1 volume exactness / M-2 volume liveness ------------------------
    # BINDING targets are the pre-solve production-ENGINE build volumes
    # (instrument JSON `engine_volumes`, frozen before any solve) — the CSV
    # `est` table is identification narrative only (PREREG §4's disclosed
    # composition-blindness).
    engine = inst["engine_volumes"]
    m1_rows, m1_ok = [], True
    m2_rows, m2_ok = [], True
    for y in YEARS:
        vc = _floor_volumes(control, y)
        va = _floor_volumes(arm, y)
        if not vc or not va:
            m1_rows.append({"year": y, "scored": False})
            m1_ok = False
            continue
        tot_c = tot_a = 0.0
        for p in LIVE_PLANTS:
            er = engine[str(y)].get(str(p), {})
            e0, e1 = er.get("engine_ctrl_twh"), er.get("engine_arm_twh")
            v0, v1 = vc.get(p, 0.0), va.get(p, 0.0)
            tot_c += v0
            tot_a += v1
            ok0 = e0 is None or abs(v0 - e0) <= max(M1_ABS_TWH, M1_REL * e0)
            ok1 = e1 is None or abs(v1 - e1) <= max(M1_ABS_TWH, M1_REL * e1)
            m1_ok &= bool(ok0 and ok1)
            m1_rows.append(
                {
                    "year": y,
                    "plant": p,
                    "ctrl_npz": round(v0, 4),
                    "ctrl_engine": e0,
                    "arm_npz": round(v1, 4),
                    "arm_engine": e1,
                    "passed": bool(ok0 and ok1),
                }
            )
            # M-2 per-plant: engine-predicted movers move DOWN, others flat.
            if e0 is not None and e1 is not None and e1 < e0 - 1e-6:
                ok2 = v1 < v0
            else:
                ok2 = v0 == 0.0 or abs(v1 - v0) <= max(
                    M2_FLAT_ABS_TWH, M2_FLAT_REL * v0
                )
            m2_ok &= bool(ok2)
            m2_rows.append({"year": y, "plant": p, "passed": bool(ok2)})
        t = totals[str(y)]
        d_pred = t["engine_delta_volume_twh"]
        d_obs = tot_a - tot_c
        ok_t = abs(d_obs - d_pred) <= M2_TOTAL_REL * abs(d_pred)
        m2_ok &= bool(ok_t)
        m2_rows.append(
            {
                "year": y,
                "plant": "TOTAL",
                "delta_pred": d_pred,
                "delta_obs": round(d_obs, 4),
                "passed": bool(ok_t),
            }
        )
    res["m1_volume_exactness"] = {"gate": "M-1", "rows": m1_rows, "passed": bool(m1_ok)}
    res["m2_volume_liveness"] = {"gate": "M-2", "rows": m2_rows, "passed": bool(m2_ok)}

    # --- M-3 at-floor movement: sign kills, magnitude reported -------------
    d2c, d2a = _d2_mech_twh(lc), _d2_mech_twh(la)
    m3_rows, m3_sign_ok = [], True
    for y in YEARS:
        delta = d2a.get(y, 0.0) - d2c.get(y, 0.0)
        t = totals[str(y)]
        lo, hi = t["at_floor_band_lo_engine"], t["at_floor_band_hi_engine"]
        in_band = lo <= delta <= hi
        sign_ok = delta < 0.0
        m3_sign_ok &= bool(sign_ok)
        m3_rows.append(
            {
                "year": y,
                "control_twh": round(d2c.get(y, 0.0), 4),
                "arm_twh": round(d2a.get(y, 0.0), 4),
                "delta_twh": round(delta, 4),
                "band": [lo, hi],
                "in_band": bool(in_band),
                "sign_ok": bool(sign_ok),
            }
        )
    res["m3_at_floor"] = {
        "gate": "M-3",
        "rows": m3_rows,
        "passed": bool(m3_sign_ok),
        "note": "sign kills; magnitude reported (at-floor-rate drift is the "
        "pre-registered miso-172 §4 interpretation of an out-of-band "
        "magnitude with M-1/M-2 clean)",
    }

    # --- M-4 conduct --------------------------------------------------------
    def _fail_keys(legit: dict) -> set[tuple]:
        keys = set()
        for r in _d4_rows(legit):
            if r.get("verdict") == "FAIL":
                keys.add(
                    (int(r["year"]), _mech_of(r), str(r.get("plant", "")), r["check"])
                )
        return keys

    fc, fa = _fail_keys(lc), _fail_keys(la)
    new_fails = sorted(fa - fc)
    target_cleared = not any(k[0] == 2023 and k[2] == "1402" for k in fa)
    res["m4_conduct"] = {
        "gate": "M-4",
        "control_failures": len(fc),
        "arm_failures": len(fa),
        "new_failures": [list(k) for k in new_fails],
        "cleared": [list(k) for k in sorted(fc - fa)],
        "m4a_passed": not new_fails,
        "m4b_target_1402_2023_cleared": bool(target_cleared),
    }

    # --- M-5 C8 no regress / M-6 zero flips --------------------------------
    vc_j, va_j = _verdict_json(control), _verdict_json(arm)
    recs_c, recs_a = _records(vc_j), _records(va_j)
    flips = [
        {"record": list(k), "control": recs_c[k], "arm": recs_a.get(k)}
        for k in recs_c
        if recs_c[k] == "PASS" and recs_a.get(k) not in (None, "PASS")
    ]
    c8_flips = [f for f in flips if f["record"][0] == "forced_share"]
    res["m5_c8"] = {
        "gate": "M-5",
        "records": {
            str(y): {
                "control": [
                    r.get("status")
                    for r in (
                        vc_j.get("criteria", {}).get("forced_share", {}) or {}
                    ).get("records", [])
                    or []
                    if r.get("year") == y
                ],
                "arm": [
                    r.get("status")
                    for r in (
                        va_j.get("criteria", {}).get("forced_share", {}) or {}
                    ).get("records", [])
                    or []
                    if r.get("year") == y
                ],
            }
            for y in YEARS
        },
        "passed": not c8_flips,
    }
    res["m6_flips"] = {
        "gate": "M-6",
        "n_records": len(recs_c),
        "flips": flips,
        "passed": not flips,
    }
    res["determination"] = {
        "control": vc_j.get("determination"),
        "arm": va_j.get("determination"),
    }

    # --- M-7 ST_GAS D-1 shape ----------------------------------------------
    d1c, d1a = _d1_rows(lc), _d1_rows(la)
    shape_rows, shape_ok = [], True
    for y in YEARS:
        a, c = d1a.get(y) or {}, d1c.get(y) or {}
        pr, cv = a.get("profile_r"), a.get("cv_ratio")
        prc = c.get("profile_r")
        ok = (
            pr is not None
            and cv is not None
            and float(pr) >= D1_MIN_PROFILE_R
            and float(cv) >= D1_MIN_CV_RATIO
            and (prc is None or float(pr) >= float(prc) - D1_MAX_PROFILE_R_DROP)
        )
        shape_ok &= bool(ok)
        shape_rows.append(
            {
                "year": y,
                "control_profile_r": prc,
                "arm_profile_r": pr,
                "arm_cv_ratio": cv,
                "passed": bool(ok),
            }
        )
    res["m7_shape"] = {"gate": "M-7", "rows": shape_rows, "passed": bool(shape_ok)}

    res["kills_silent"] = bool(
        res["m1_volume_exactness"]["passed"]
        and res["m2_volume_liveness"]["passed"]
        and res["m3_at_floor"]["passed"]
        and res["m4_conduct"]["m4a_passed"]
        and res["m5_c8"]["passed"]
        and res["m6_flips"]["passed"]
        and res["m7_shape"]["passed"]
    )
    res["candidate"] = bool(
        res["kills_silent"] and res["m4_conduct"]["m4b_target_1402_2023_cleared"]
    )
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--identity", nargs=2, metavar=("CONTROL", "KEEPER"))
    ap.add_argument("--gates", nargs=2, metavar=("CONTROL", "ARM"))
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    out: dict = {}
    if args.identity:
        out["identity"] = identity(Path(args.identity[0]), Path(args.identity[1]))
    if args.gates:
        out["gates"] = gates(Path(args.gates[0]), Path(args.gates[1]))
    if not out:
        ap.error("pass --identity and/or --gates")

    text = json.dumps(out, indent=1, default=str)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")


if __name__ == "__main__":
    main()
