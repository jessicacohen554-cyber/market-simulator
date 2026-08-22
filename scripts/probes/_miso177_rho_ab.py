"""miso-177 A/B scorer — the measured-rho (floor-refuted) arm.

Committed BEFORE either run's result is read, so the gates cannot be written
around the outcome. Scores ``PREREG-miso177-rho-measured-ab-2026-08-22.md``
§4: R-0..R-7 for arm ``miso_online_rho_no_floor``.

Modes:

* ``--identity CONTROL KEEPER`` — R-0, run and reported BEFORE any arm
  output is read: every scored sidecar of every year bit-identical
  (``max|diff| = 0.0``, non-numeric columns equal).
* ``--gates CONTROL ARM`` — R-1..R-7 plus the report-only cuts, scored from
  the two bundles' committed artifacts, the frozen instrument JSON
  (``_miso177_rho_instrument.json``) and ``calibration_verdict --json``.

No LP is spent here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

INSTRUMENT = REPO / "results/calibration/_miso177_rho_instrument.json"
KEEPER = REPO / "results/calibration/miso175_hourkey"
YEARS = (2023, 2024, 2025)

R2_MIN_CELLS = 50  # liveness: differing P1 price cells summed over the years
R2_TOL = 0.001  # $/MWh
R6_C3A_2023_BAND = 3.0  # ±pp
R6_C3A_2024_BAND = 10.0  # ±pp
R6_C3A_2024_ADVERSE_PP = 1.5
R7_ANNUAL_BAND_PCT = 2.0


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    return df.sort_values(["zone", "hour"]).reset_index(drop=True)


def _regspin(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    df = df[df["family"] == "miso_rbdc_regspin"]
    return df.sort_values("hour").reset_index(drop=True)


def identity(control: Path, keeper: Path) -> dict:
    """R-0 — every scored sidecar of every year must be bit-identical."""
    out: dict = {"gate": "R-0", "files": [], "passed": True}
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


def _c3a_rt_pct(verdict: dict) -> dict[int, float]:
    out: dict[int, float] = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("key") is None and rec.get("year") in YEARS:
            out[int(rec["year"])] = (
                (float(rec["model"]) - float(rec["actual"])) / float(rec["actual"]) * 100
            )
    return out


def _d4_fail_keys(bundle: Path) -> set[tuple]:
    legit = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    keys = set()
    for r in legit["diagnostics"]["D4"]["rows"]:
        if r.get("verdict") == "FAIL":
            keys.add(
                (
                    int(r["year"]),
                    str(r.get("floor", "")).split(" × ")[0],
                    str(r.get("plant", "")),
                    r["check"],
                )
            )
    return keys


def gates(control: Path, arm: Path) -> dict:
    inst = json.loads(INSTRUMENT.read_text())
    res: dict = {"arm": "rho_measured", "years": list(YEARS)}

    # --- R-1 coefficient exactness -----------------------------------------
    from market_sim.data.online_reserve_rho import _artifact_path, load_online_rho

    art = _artifact_path("MISO")
    sha_now = hashlib.sha256(art.read_bytes()).hexdigest()
    measured = load_online_rho("MISO", "miso_reg_spin")
    rc_c = json.loads((control / "run_config.json").read_text())
    rc_a = json.loads((arm / "run_config.json").read_text())
    flag_c = bool(
        (rc_c.get("scenario_config") or {}).get("miso_online_rho_no_floor", False)
    )
    flag_a = bool(
        (rc_a.get("scenario_config") or {}).get("miso_online_rho_no_floor", False)
    )
    r1 = {
        "gate": "R-1",
        "artifact_sha_frozen": inst["artifact"]["sha256"],
        "artifact_sha_now": sha_now,
        "sha_match": sha_now == inst["artifact"]["sha256"],
        "control_flag": flag_c,
        "arm_flag": flag_a,
        "seam_control_value": measured.rho_used if measured else None,
        "seam_arm_value": measured.rho_used_no_floor if measured else None,
        "frozen_control_value": inst["coefficients"]["rho_control_consumes"],
        "frozen_arm_value": inst["coefficients"]["rho_arm_consumes"],
    }
    r1["passed"] = bool(
        r1["sha_match"]
        and not flag_c
        and flag_a
        and measured is not None
        and measured.rho_used == inst["coefficients"]["rho_control_consumes"]
        and measured.rho_used_no_floor == inst["coefficients"]["rho_arm_consumes"]
    )
    res["r1_coefficient"] = r1

    # --- R-2 liveness + report-only price cuts -----------------------------
    live_cells = 0
    per_year: dict = {}
    for y in YEARS:
        sc, sa = _system(control, y), _system(arm, y)
        pc, pa = sc["price"].to_numpy(float), sa["price"].to_numpy(float)
        dem = sc["demand"].to_numpy(float)
        diff = pa - pc
        cells = int((np.abs(diff) > R2_TOL).sum())
        live_cells += cells
        dw_c = float((pc * dem).sum() / dem.sum())
        dw_a = float((pa * dem).sum() / dem.sum())
        month = (sc["hour"].to_numpy(int) // 730).clip(0, 11) + 1  # coarse month
        summer = (month >= 6) & (month <= 9)
        # control regspin binding hours -> mask onto every zone row
        rs_c = _regspin(control, y)
        bind_h = set(rs_c.loc[rs_c["dual"] > 1e-9, "hour"].astype(int).tolist())
        bmask = sc["hour"].astype(int).isin(bind_h).to_numpy()
        rs_a = _regspin(arm, y)
        per_year[str(y)] = {
            "diff_cells": cells,
            "dw_price_control": round(dw_c, 4),
            "dw_price_arm": round(dw_a, 4),
            "dw_price_delta_pct": round((dw_a - dw_c) / dw_c * 100, 4),
            "summer_dw_delta_usd": round(
                float(
                    (diff * dem)[summer].sum() / dem[summer].sum()
                    if summer.any()
                    else 0.0
                ),
                4,
            ),
            "control_bind_hours": len(bind_h),
            "arm_bind_hours": int((rs_a["dual"] > 1e-9).sum()),
            "control_bind_dual_max": round(float(rs_c["dual"].max()), 3),
            "arm_bind_dual_max": round(float(rs_a["dual"].max()), 3),
            "bindhour_dw_delta_usd": round(
                float((diff * dem)[bmask].sum() / dem[bmask].sum())
                if bmask.any()
                else 0.0,
                4,
            ),
        }
    res["r2_liveness"] = {
        "gate": "R-2",
        "total_diff_cells": live_cells,
        "threshold": R2_MIN_CELLS,
        "live": live_cells >= R2_MIN_CELLS,
        "per_year": per_year,
    }

    # --- R-3 conduct --------------------------------------------------------
    fc, fa = _d4_fail_keys(control), _d4_fail_keys(arm)
    res["r3_conduct"] = {
        "gate": "R-3",
        "control_failures": len(fc),
        "arm_failures": len(fa),
        "new_failures": [list(k) for k in sorted(fa - fc)],
        "passed": len(fa) == 0 and not (fa - fc),
    }

    # --- R-4 C8 / R-5 flips (arm vs committed keeper) ----------------------
    va = _verdict_json(arm)
    vk = _verdict_json(KEEPER)
    c8_arm = [
        (r.get("key"), r.get("year"), r.get("status"))
        for r in va["criteria"]["forced_share"]["records"]
    ]
    res["r4_c8"] = {
        "gate": "R-4",
        "arm_records": c8_arm,
        "passed": all(s == "PASS" for _, _, s in c8_arm),
    }
    recs_k, recs_a = _records(vk), _records(va)
    flips = [
        {"record": list(k), "keeper": recs_k[k], "arm": recs_a.get(k)}
        for k in recs_k
        if recs_k[k] == "PASS" and recs_a.get(k) not in (None, "PASS")
    ]
    res["r5_flips"] = {
        "gate": "R-5",
        "n_records": len(recs_k),
        "flips": flips,
        "passed": not flips,
    }
    res["determination"] = {
        "keeper": vk.get("determination"),
        "arm": va.get("determination"),
    }

    # --- R-6 against-interest / C3a report ---------------------------------
    c3a_k, c3a_a = _c3a_rt_pct(vk), _c3a_rt_pct(va)
    ok_2023 = abs(c3a_a.get(2023, 99.0)) <= R6_C3A_2023_BAND
    adverse_2024 = c3a_k.get(2024, 0.0) - c3a_a.get(2024, 0.0)  # +ve = more negative
    ok_2024 = (
        abs(c3a_a.get(2024, 99.0)) <= R6_C3A_2024_BAND
        and adverse_2024 <= R6_C3A_2024_ADVERSE_PP
    )
    res["r6_against_interest"] = {
        "gate": "R-6",
        "c3a_keeper_pct": {str(y): round(c3a_k.get(y, float("nan")), 3) for y in YEARS},
        "c3a_arm_pct": {str(y): round(c3a_a.get(y, float("nan")), 3) for y in YEARS},
        "c3a_2025_reported_not_gated": True,
        "passed": bool(ok_2023 and ok_2024),
    }

    # --- R-7 over-reach ----------------------------------------------------
    worst = max(abs(per_year[str(y)]["dw_price_delta_pct"]) for y in YEARS)
    res["r7_overreach"] = {
        "gate": "R-7",
        "worst_annual_dw_delta_pct": worst,
        "band_pct": R7_ANNUAL_BAND_PCT,
        "passed": worst <= R7_ANNUAL_BAND_PCT,
    }

    res["kills_silent"] = bool(
        res["r1_coefficient"]["passed"]
        and res["r3_conduct"]["passed"]
        and res["r4_c8"]["passed"]
        and res["r5_flips"]["passed"]
        and res["r6_against_interest"]["passed"]
        and res["r7_overreach"]["passed"]
    )
    res["verdict"] = (
        "KEEPER-CANDIDATE (owner ruling required)"
        if res["kills_silent"] and res["r2_liveness"]["live"]
        else "INERT (verdict I)"
        if res["kills_silent"]
        else "REJECTED-AS-ARMED"
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
