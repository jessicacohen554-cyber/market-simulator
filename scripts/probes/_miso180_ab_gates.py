"""miso-180 A/B scorer — the anchored SPREAD-ONLY dispersion arm.

Committed BEFORE either run's result is read, so the gates cannot be written
around the outcome (the miso-177 discipline; ``_miso177_rho_ab.py`` is the
direct ancestor). Scores ``PREREG-miso180-anchored-spread-2026-08-23.md`` §5:
G-0..G-7 for arm ``miso_offer_spread_anchored``, plus the ungated report
cuts the prereg lists (lw deltas annual/JJA, C3c tail counts, maxgen
ceiling encounters, static-predictor audit).

Modes:

* ``--identity CONTROL KEEPER`` — G-0, run and reported BEFORE any arm
  output is read: every scored sidecar of every year bit-identical
  (``max|diff| = 0.0``, non-numeric columns equal).
* ``--gates CONTROL ARM [--arm-log PATH]`` — G-1..G-7 plus the report-only
  cuts, scored from the two bundles' committed artifacts, the Phase A
  record (``_miso180_anchored_spread_precheck.json``) and
  ``calibration_verdict --json``.

No LP is spent here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

PRECHECK = REPO / "results/calibration/_miso180_anchored_spread_precheck.json"
KEEPER = REPO / "results/calibration/miso177_rho_B"
ARTIFACT = REPO / "data/raw/_validation-source/miso_offer_level_dispersion.json"
YEARS = (2023, 2024, 2025)

G2_STEP_PP = 0.25  # PREREG §5 G-2: kill <= -0.25; inert |d| < 0.25; improve >= +0.25
G3_BAND_PCT = 10.0  # PREREG §5 G-3: 2023 AND 2024 inside ±10 on the arm


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"] if "pass" in df.columns else df
    return df.sort_values(["zone", "hour"]).reset_index(drop=True)


def identity(control: Path, keeper: Path) -> dict:
    """G-0 — every scored sidecar of every year must be bit-identical."""
    out: dict = {"gate": "G-0", "files": [], "passed": True}
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
        raise SystemExit(
            f"calibration_verdict.py produced no JSON for {bundle}: {res.stderr[-800:]}"
        )
    return json.loads(res.stdout)


def _records(verdict: dict) -> dict[tuple, str]:
    out: dict[tuple, str] = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[(rec.get("criterion", name), rec.get("key"), rec.get("year"))] = rec.get(
                "status"
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


def _crit_year_status(verdict: dict, crit: str) -> dict[int, list[str]]:
    out: dict[int, list[str]] = {y: [] for y in YEARS}
    for rec in verdict["criteria"][crit]["records"]:
        y = rec.get("year")
        if y in YEARS:
            out[int(y)].append(rec.get("status"))
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


def gates(control: Path, arm: Path, arm_log: Path | None) -> dict:
    pre = json.loads(PRECHECK.read_text())
    res: dict = {"arm": "miso_offer_spread_anchored", "years": list(YEARS)}

    # --- G-1 arm validity ---------------------------------------------------
    from market_sim.config.constants import (
        MISO_OFFER_SPREAD_ANCHOR_RANK,
        MISO_OFFER_SPREAD_ARTIFACT_SHA256,
    )

    sha_now = hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
    rc_c = json.loads((control / "run_config.json").read_text())
    rc_a = json.loads((arm / "run_config.json").read_text())
    flag_c = bool(
        (rc_c.get("scenario_config") or {}).get("miso_offer_spread_anchored", False)
    )
    flag_a = bool(
        (rc_a.get("scenario_config") or {}).get("miso_offer_spread_anchored", False)
    )
    telemetry: list[dict] = []
    if arm_log is not None and arm_log.exists():
        pat = re.compile(
            r"MISO anchored spread graft \(miso-180\): (\d+) affected tranches, "
            r"anchor r=([0-9.]+) .*?(\d+) tranche-months raised.*?year (\d+)"
        )
        for m in pat.finditer(arm_log.read_text()):
            telemetry.append(
                {
                    "year": int(m.group(4)),
                    "affected": int(m.group(1)),
                    "anchor": float(m.group(2)),
                    "raised": int(m.group(3)),
                }
            )
    telemetry_ok = (
        {t["year"] for t in telemetry} >= set(YEARS)
        and all(t["affected"] > 0 for t in telemetry)
        if telemetry
        else None  # no log passed: telemetry verified out-of-band, recorded null
    )
    g1 = {
        "gate": "G-1",
        "control_flag": flag_c,
        "arm_flag": flag_a,
        "artifact_sha_now": sha_now,
        "artifact_sha_pinned": MISO_OFFER_SPREAD_ARTIFACT_SHA256,
        "sha_match": sha_now == MISO_OFFER_SPREAD_ARTIFACT_SHA256,
        "anchor_const": float(MISO_OFFER_SPREAD_ANCHOR_RANK),
        "anchor_identified": float(pre["ADJUDICATION"]["r_anchor"]),
        "anchor_match": float(MISO_OFFER_SPREAD_ANCHOR_RANK)
        == float(pre["ADJUDICATION"]["r_anchor"]),
        "telemetry": telemetry,
        "telemetry_ok": telemetry_ok,
    }
    g1["passed"] = bool(
        (not flag_c)
        and flag_a
        and g1["sha_match"]
        and g1["anchor_match"]
        and (telemetry_ok is not False)
    )
    res["g1_arm_validity"] = g1

    # --- verdicts (arm, control, committed keeper) --------------------------
    va = _verdict_json(arm)
    vc = _verdict_json(control)
    vk = _verdict_json(KEEPER)
    res["determination"] = {
        "keeper": vk.get("determination"),
        "control": vc.get("determination"),
        "arm": va.get("determination"),
    }

    # --- G-2 C3a-2025 direction --------------------------------------------
    c3a_c, c3a_a = _c3a_rt_pct(vc), _c3a_rt_pct(va)
    d25 = c3a_a.get(2025, float("nan")) - c3a_c.get(2025, float("nan"))
    g2_outcome = (
        "KILL"
        if d25 <= -G2_STEP_PP
        else ("IMPROVE" if d25 >= G2_STEP_PP else "INERT")
    )
    res["g2_c3a2025"] = {
        "gate": "G-2",
        "c3a_2025_control_pct": round(c3a_c.get(2025, float("nan")), 4),
        "c3a_2025_arm_pct": round(c3a_a.get(2025, float("nan")), 4),
        "delta_pp": round(d25, 4),
        "outcome": g2_outcome,
    }

    # --- G-3 against-interest band ------------------------------------------
    res["g3_band"] = {
        "gate": "G-3",
        "c3a_2023_arm_pct": round(c3a_a.get(2023, float("nan")), 4),
        "c3a_2024_arm_pct": round(c3a_a.get(2024, float("nan")), 4),
        "passed": bool(
            abs(c3a_a.get(2023, 99.0)) <= G3_BAND_PCT
            and abs(c3a_a.get(2024, 99.0)) <= G3_BAND_PCT
        ),
    }

    # --- G-4 C3b ------------------------------------------------------------
    c3b = _crit_year_status(va, "price_shape")
    res["g4_c3b"] = {
        "gate": "G-4",
        "arm_status_by_year": {str(y): c3b[y] for y in YEARS},
        "passed": all(s == "PASS" for y in YEARS for s in c3b[y]),
    }

    # --- G-5 conduct (C8 + D-4) ---------------------------------------------
    c8 = [
        (r.get("key"), r.get("year"), r.get("status"))
        for r in va["criteria"]["forced_share"]["records"]
    ]
    # PREREG G-5's C8 leg is "the scorer's own gate": gated class records all
    # PASS. SKIPPED rows are non-gated (the keeper's own committed record
    # carries the identical hydro SKIPPED rows and scores C8 PASS) — counting
    # them as failures would fail the keeper itself.
    c8_ok = all(s == "PASS" for _, _, s in c8 if s != "SKIPPED")
    fc, fa = _d4_fail_keys(control), _d4_fail_keys(arm)
    res["g5_conduct"] = {
        "gate": "G-5",
        "c8_arm_records": c8,
        "c8_passed": c8_ok,
        "d4_control_failures": len(fc),
        "d4_arm_failures": len(fa),
        "d4_new_failures": [list(k) for k in sorted(fa - fc)],
        "passed": c8_ok and not (fa - fc),
    }

    # --- G-6 DOF ------------------------------------------------------------
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    n_res = int(att["free_parameters"]["n_residual"])
    res["g6_dof"] = {
        "gate": "G-6",
        "keeper_n_residual": n_res,
        "arm_new_entries": [
            {
                "name": "miso_offer_spread vector (committed miso-179 artifact)",
                "identification": "measured",
                "sha256": sha_now,
            },
            {
                "name": "miso_offer_spread anchor rank",
                "identification": "measured/identified (PREREG-miso180 §2 frozen "
                "rule, inputs-only path; zero residual)",
                "value": float(MISO_OFFER_SPREAD_ANCHOR_RANK),
            },
        ],
        "n_residual_unchanged": n_res == 2,
        "passed": n_res == 2,
    }

    # --- G-7 record flips (arm vs committed keeper) -------------------------
    recs_k, recs_a = _records(vk), _records(va)
    flips = [
        {"record": list(k), "keeper": recs_k[k], "arm": recs_a.get(k)}
        for k in recs_k
        if recs_k[k] == "PASS" and recs_a.get(k) not in (None, "PASS")
    ]
    res["g7_flips"] = {
        "gate": "G-7",
        "n_records": len(recs_k),
        "flips": flips,
        "passed": not flips,
    }

    # --- ungated report cuts ------------------------------------------------
    per_year: dict = {}
    for y in YEARS:
        sc, sa = _system(control, y), _system(arm, y)
        pc, pa = sc["price"].to_numpy(float), sa["price"].to_numpy(float)
        dem = sc["demand"].to_numpy(float)
        hours = sc["hour"].to_numpy(int)
        month = pd.DatetimeIndex(
            pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(hours, unit="h")
        ).month.to_numpy()
        jja = (month >= 6) & (month <= 8)
        diff = pa - pc
        # Ceiling encounters: hours (any carry zone) at/above the maxgen slack
        # ceilings — the market's own cap, expected, not touched (PREREG §3).
        pz_a = sa.pivot_table(index="hour", columns="zone", values="price").to_numpy(
            float
        )
        pz_c = sc.pivot_table(index="hour", columns="zone", values="price").to_numpy(
            float
        )
        per_year[str(y)] = {
            "dw_price_control": round(float((pc * dem).sum() / dem.sum()), 4),
            "dw_price_arm": round(float((pa * dem).sum() / dem.sum()), 4),
            "dw_delta_usd": round(float((diff * dem).sum() / dem.sum()), 4),
            "jja_dw_delta_usd": round(
                float((diff * dem)[jja].sum() / dem[jja].sum()), 4
            ),
            "diff_cells_gt_1c": int((np.abs(diff) > 0.01).sum()),
            "hours_ge_500_control": int((pz_c.max(axis=1) >= 499.99).sum()),
            "hours_ge_500_arm": int((pz_a.max(axis=1) >= 499.99).sum()),
            "hours_ge_1000_arm": int((pz_a.max(axis=1) >= 999.99).sum()),
        }
    res["report_price_cuts"] = per_year

    # C3c tail counts at full magnitude, both arms (report-only).
    def _tail(verdict: dict) -> dict:
        out = {}
        for rec in verdict["criteria"]["price_tail"]["records"]:
            if rec.get("year") in YEARS:
                out[str(rec["year"])] = {
                    "model": rec.get("model"),
                    "actual": rec.get("actual"),
                    "status": rec.get("status"),
                }
        return out

    res["report_c3c_tail"] = {"control": _tail(vc), "arm": _tail(va)}

    # Static-predictor audit: Phase A predicted vs LP realized (report-only).
    res["report_static_vs_realized"] = {
        "predicted_shift_pp": {
            "2023": pre["K_b_2023"]["predicted_shift_pp"],
            "2024": pre.get("K_c_report_2024", {}).get("predicted_shift_pp"),
            "2025": pre["K_c_2025"]["predicted_shift_pp"],
        },
        "realized_shift_pp": {
            str(y): round(c3a_a.get(y, float("nan")) - c3a_c.get(y, float("nan")), 4)
            for y in YEARS
        },
    }

    kills_silent = bool(
        res["g1_arm_validity"]["passed"]
        and g2_outcome != "KILL"
        and res["g3_band"]["passed"]
        and res["g4_c3b"]["passed"]
        and res["g5_conduct"]["passed"]
        and res["g6_dof"]["passed"]
        and res["g7_flips"]["passed"]
    )
    res["kills_silent"] = kills_silent
    res["verdict"] = (
        "REJECTED-AS-ARMED"
        if not kills_silent
        else ("INERT (verdict I)" if g2_outcome == "INERT" else "KEEPER-CANDIDATE")
    )
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--identity", nargs=2, metavar=("CONTROL", "KEEPER"))
    ap.add_argument("--gates", nargs=2, metavar=("CONTROL", "ARM"))
    ap.add_argument("--arm-log", default=None)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    out: dict = {}
    if args.identity:
        out["identity"] = identity(Path(args.identity[0]), Path(args.identity[1]))
    if args.gates:
        out["gates"] = gates(
            Path(args.gates[0]),
            Path(args.gates[1]),
            Path(args.arm_log) if args.arm_log else None,
        )
    if not out:
        ap.error("pass --identity and/or --gates")

    text = json.dumps(out, indent=1, default=str)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")


if __name__ == "__main__":
    main()
