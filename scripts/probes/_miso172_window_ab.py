"""miso-172 A/B scorer — the per-plant must-run WINDOW-VINTAGE and LEVEL-BASIS arms.

Committed BEFORE either arm result is read, so the gates cannot be written
around the outcome. Scores the two pre-registrations:

* ``PREREG-miso172-mustrun-window-vintage-2026-08-20.md`` — arm ``peryear``
  (``mustrun_online_frac_per_year``), gates K-0..K-6.
* ``PREREG-miso172-p25-level-basis-2026-08-20.md`` — arm ``p25mw``
  (``st_gas_mustrun_p25_measured_level``), gates K-0, L-1..L-3, K-3, K-5, K-6.

Modes:

* ``--identity CONTROL KEEPER`` — the K-0 prerequisite, run and reported BEFORE
  any arm output is read. Every scored sidecar of every year must be
  bit-identical (``max|diff| = 0.0``, non-numeric columns equal).
* ``--gates CONTROL ARM --arm {peryear,p25mw}`` — the arm's own gates, scored
  from both bundles' committed artifacts plus (where present) the solve-time
  ``dispatch/<year>_P1.parquet``.

Everything is read from committed artifacts; no LP is spent here.
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

# The mechanisms both arms touch. D-4 labels them "<mech> × <CLASS>".
MECHS = ("st_gas_mustrun_per_plant", "cc_mustrun_per_plant")

# The ST_GAS plants the keeper actually floors (read off the keeper's own D-4
# rows, restated here so the gate set is fixed in the committed scorer).
LIVE_PLANTS = (3459, 1403, 990, 1122, 3457, 1402, 6035)

# Plants each arm is pre-registered to MOVE, and those it must leave alone.
PERYEAR_MOVERS = (1402, 3457, 6035)
P25MW_MOVERS = (1402, 1122, 3459, 3457)
P25MW_UNMOVED = (990, 1403, 6035)

# Pre-registered K-2 / L-2 bands on the CHANGE in the mechanism's D-2 forced
# energy (TWh), +-50 % of the point prediction (PREREG §5 / §4).
K2_BANDS = {2023: (-0.163, -0.054), 2024: (-0.047, -0.016), 2025: (0.094, 0.283)}
L2_BANDS = {2023: (-2.232, -0.744), 2024: (-2.222, -0.741), 2025: (-2.867, -0.956)}

# 1122 Ames control overshoot vs its meter (L-3): model / actual - 1.
AMES_CONTROL_OVERSHOOT = {2023: 0.65, 2024: 0.77, 2025: 0.93}

D1_MIN_PROFILE_R = 0.80
D1_MIN_CV_RATIO = 0.5
D1_MAX_PROFILE_R_DROP = 0.05


def _legit(bundle: Path) -> dict:
    """Return a bundle's committed ``legitimacy_diagnostics.json``."""
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _d4_rows(legit: dict) -> list[dict]:
    """Return the D-4 rows."""
    return list(legit["diagnostics"]["D4"]["rows"])


def _d4_failures(legit: dict) -> list[str]:
    """Return the D-4 failure strings."""
    return list(legit["diagnostics"]["D4"].get("failures") or [])


def _mech_of(row: dict) -> str:
    """Return the bare mechanism name from a D-4 ``floor`` label."""
    return str(row.get("floor", "")).split(" × ")[0]


def _d2_mech_twh(legit: dict, klass: str = "ST_GAS") -> dict[int, float]:
    """Return ``{year: forced_twh}`` for the per-plant must-run mechanism."""
    out: dict[int, float] = {}
    for r in legit["diagnostics"]["D2"]["rows"]:
        if r.get("class") != klass or str(r.get("mechanism")) not in MECHS:
            continue
        out[int(r["year"])] = out.get(int(r["year"]), 0.0) + float(
            r.get("forced_twh") or 0.0
        )
    return out


def _d4_plant_twh(legit: dict) -> dict[tuple[int, int], float]:
    """Return ``{(plant, year): floored_twh}`` for the mechanism's plant rows."""
    out: dict[tuple[int, int], float] = {}
    for r in _d4_rows(legit):
        if not r.get("plant") or _mech_of(r) not in MECHS:
            continue
        try:
            out[(int(r["plant"]), int(r["year"]))] = float(r.get("floored_twh") or 0.0)
        except (TypeError, ValueError):
            continue
    return out


def _d1_rows(legit: dict, klass: str = "ST_GAS") -> dict[int, dict]:
    """Return ``{year: row}`` of the class's D-1 shape row."""
    out: dict[int, dict] = {}
    for r in legit["diagnostics"]["D1"]["rows"]:
        if r.get("class") == klass and r.get("year") is not None:
            out[int(r["year"])] = r
    return out


def identity(control: Path, keeper: Path) -> dict:
    """K-0 — every scored sidecar of every year must be bit-identical."""
    out: dict = {"gate": "K-0", "files": [], "passed": True}
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
    """Return ``calibration_verdict.py --json`` for a bundle."""
    # check=False deliberately: the scorer exits non-zero on a NOT-YET
    # determination, which is the expected state on both sides of this A/B.
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
    """Flatten a verdict payload to ``{(criterion, key, year): status}``."""
    out: dict[tuple, str] = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[(rec.get("criterion", name), rec.get("key"), rec.get("year"))] = (
                rec.get("status")
            )
    return out


def _plant_annual_mwh(bundle: Path, year: int, plant: int) -> float | None:
    """Return a plant's modelled annual MWh from the solve-time dispatch frame.

    ``None`` when ``dispatch/`` is absent (a slimmed bundle) — the gate that
    needs it then reports ``unscored`` rather than silently passing.
    """
    for label in ("P1", "P2"):
        path = bundle / "dispatch" / f"{year}_{label}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        col = next(
            (c for c in ("plant_code", "plant", "plant_id") if c in df.columns), None
        )
        mwcol = next(
            (c for c in ("mwh", "mw", "generation_mwh", "gen_mwh") if c in df.columns),
            None,
        )
        if col is None or mwcol is None:
            return None
        sub = df[df[col].astype("int64", errors="ignore") == plant]
        return float(pd.to_numeric(sub[mwcol], errors="coerce").sum())
    return None


def _bench_plant_annual_mwh(year: int, plant: int) -> float | None:
    """Return a plant's METERED annual MWh from the committed bench file."""
    try:
        from scripts import legitimacy_diagnostics as ld

        bench = ld.bench_plant_view(ld.load_bench(REPO, "MISO", year))
    except Exception:  # pragma: no cover - bench absent in a bare checkout
        return None
    b = bench.get(str(plant))
    if b is None:
        return None
    return float(np.asarray(b["mw"], dtype=float).sum())


def gates(control: Path, arm: Path, which: str) -> dict:
    """Score the arm's pre-registered gates from committed artifacts."""
    lc, la = _legit(control), _legit(arm)
    rc = _d4_rows(lc)
    years = sorted({int(r["year"]) for r in rc if r.get("year") is not None})
    res: dict = {"arm": which, "years": years}

    d2c, d2a = _d2_mech_twh(lc), _d2_mech_twh(la)
    plc, pla = _d4_plant_twh(lc), _d4_plant_twh(la)

    # --- liveness (K-2 for peryear, L-2 for p25mw) -------------------------
    bands = K2_BANDS if which == "peryear" else L2_BANDS
    live_rows = []
    live_ok = True
    for y in years:
        delta = d2a.get(y, 0.0) - d2c.get(y, 0.0)
        lo, hi = bands.get(y, (-np.inf, np.inf))
        ok = lo <= delta <= hi
        live_ok &= ok
        live_rows.append(
            {
                "year": y,
                "control_twh": round(d2c.get(y, 0.0), 4),
                "arm_twh": round(d2a.get(y, 0.0), 4),
                "delta_twh": round(delta, 4),
                "band": [lo, hi],
                "passed": bool(ok),
            }
        )
    res["liveness"] = {
        "gate": "K-2" if which == "peryear" else "L-2",
        "rows": live_rows,
        "passed": bool(live_ok),
    }

    # Per-plant direction, the half that makes the gate targeted rather than
    # aggregate: a vintage repair moves 1402 DOWN in 2023 and UP in 2024/25; a
    # level repair moves the four over-floored plants down and leaves the three
    # exact ones alone.
    movers = PERYEAR_MOVERS if which == "peryear" else P25MW_MOVERS
    dir_rows = []
    dir_ok = True
    for p in LIVE_PLANTS:
        for y in years:
            c, a = plc.get((p, y), 0.0), pla.get((p, y), 0.0)
            rel = (a - c) / c if c > 0 else 0.0
            if which == "peryear" and p == 1402:
                want = "down" if y == 2023 else "up"
                ok = (rel < -0.10) if want == "down" else (rel > 0.05)
            elif which == "p25mw" and p in movers:
                want, ok = "down", rel < -0.05
            elif which == "p25mw" and p in P25MW_UNMOVED:
                want, ok = "flat", abs(rel) <= 0.05
            else:
                want, ok = "unconstrained", True
            dir_ok &= ok
            dir_rows.append(
                {
                    "plant": p,
                    "year": y,
                    "control_twh": round(c, 4),
                    "arm_twh": round(a, 4),
                    "rel_change": round(rel, 4),
                    "expected": want,
                    "passed": bool(ok),
                }
            )
    res["plant_direction"] = {"rows": dir_rows, "passed": bool(dir_ok)}

    # --- K-3 conduct failures: ZERO NEW -----------------------------------
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
    res["k3_conduct"] = {
        "gate": "K-3",
        "control_failures": len(fc),
        "arm_failures": len(fa),
        "new_failures": [list(k) for k in new_fails],
        "cleared": [list(k) for k in sorted(fc - fa)],
        # 1402-2023 is pre-named as an expected survivor of the peryear arm.
        "expected_survivor_1402_2023_present": any(
            k[0] == 2023 and k[2] == "1402" for k in fa
        ),
        "passed": not new_fails,
    }

    # --- K-5 no record-grain PASS -> FAIL flip ----------------------------
    vc, va = _verdict_json(control), _verdict_json(arm)
    recs_c, recs_a = _records(vc), _records(va)
    flips = [
        {"record": list(k), "control": recs_c[k], "arm": recs_a.get(k)}
        for k in recs_c
        if recs_c[k] == "PASS" and recs_a.get(k) not in (None, "PASS")
    ]
    res["k5_flips"] = {
        "gate": "K-5",
        "n_records": len(recs_c),
        "flips": flips,
        "passed": not flips,
    }
    res["determination"] = {
        "control": vc.get("determination"),
        "arm": va.get("determination"),
    }

    # --- K-6 ST_GAS D-1 shape --------------------------------------------
    d1c, d1a = _d1_rows(lc), _d1_rows(la)
    shape_rows = []
    shape_ok = True
    for y in years:
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
    res["k6_shape"] = {"gate": "K-6", "rows": shape_rows, "passed": bool(shape_ok)}

    # --- C8 records, reported for both arms ------------------------------
    res["c8"] = {
        y: {
            "control": [
                r.get("status")
                for r in (vc.get("criteria", {}).get("forced_share", {}) or {}).get(
                    "records", []
                )
                or []
                if r.get("year") == y
            ],
            "arm": [
                r.get("status")
                for r in (va.get("criteria", {}).get("forced_share", {}) or {}).get(
                    "records", []
                )
                or []
                if r.get("year") == y
            ],
        }
        for y in years
    }

    # --- L-3 Ames dispatch moves toward its meter (p25mw only) -----------
    if which == "p25mw":
        rows = []
        l3_ok: bool | None = True
        for y in years:
            model_c = _plant_annual_mwh(control, y, 1122)
            model_a = _plant_annual_mwh(arm, y, 1122)
            actual = _bench_plant_annual_mwh(y, 1122)
            if None in (model_c, model_a, actual) or not actual:
                rows.append({"year": y, "scored": False})
                l3_ok = None if l3_ok else l3_ok
                continue
            oc = model_c / actual - 1.0
            oa = model_a / actual - 1.0
            ok = abs(oa) < abs(oc) and oa >= -1.0
            l3_ok = bool(l3_ok) and ok if l3_ok is not None else None
            rows.append(
                {
                    "year": y,
                    "scored": True,
                    "actual_twh": round(actual / 1e6, 4),
                    "control_twh": round(model_c / 1e6, 4),
                    "arm_twh": round(model_a / 1e6, 4),
                    "control_overshoot": round(oc, 4),
                    "arm_overshoot": round(oa, 4),
                    "passed": bool(ok),
                }
            )
        res["l3_ames"] = {"gate": "L-3", "rows": rows, "passed": l3_ok}

    res["passed"] = bool(
        res["liveness"]["passed"]
        and res["plant_direction"]["passed"]
        and res["k3_conduct"]["passed"]
        and res["k5_flips"]["passed"]
        and res["k6_shape"]["passed"]
        and (which != "p25mw" or res.get("l3_ames", {}).get("passed") is not False)
    )
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--identity", nargs=2, metavar=("CONTROL", "KEEPER"))
    ap.add_argument("--gates", nargs=2, metavar=("CONTROL", "ARM"))
    ap.add_argument("--arm", choices=("peryear", "p25mw"), default="peryear")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    out: dict = {}
    if args.identity:
        out["identity"] = identity(Path(args.identity[0]), Path(args.identity[1]))
    if args.gates:
        out["gates"] = gates(Path(args.gates[0]), Path(args.gates[1]), args.arm)
    if not out:
        ap.error("pass --identity and/or --gates")

    text = json.dumps(out, indent=1, default=str)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")


if __name__ == "__main__":
    main()
