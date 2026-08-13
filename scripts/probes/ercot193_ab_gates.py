"""ERCOT-193 A/B gate scorer — the ercot-167 §3 gates verbatim, at HEAD. Read-only, no LP.

Scores the standing SOC-reserve re-gate
(`docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md` §4) on the two solved
bundles: **A** = the disarmed control (`ercot193_ctl_nosoc`), **B** = the arm
(`ercot193_arm_soc`, the run192 keeper recipe replayed byte-faithfully).
Verdicts read A→B exactly as PRECOMMIT-ercot167 §3 pre-registered them:

* **G1** (target, 2023) — mean battery discharge in the actual RT >$1000 hours
  moves ≥ 40 % of the A→actual gap toward the measured 423 MW; below 300 MW is
  an over-shoot flag, reported.
* **G2** (KILL) — 2025 model discharge ÷ EIA-930 NG:BAT (5,444.8 GWh, the
  ercot-162 committed constant) ≥ 0.70 on B. 2024 reported on its covered
  window (report-only, as originally).
* **G3** (KILL) — spurious tail hours (model max-zonal P1 dual > $200 where
  actual RT ≤ $200) must not increase A→B, per year.
* **G4** (KILL) — C1/C2/C4/C8 hold PASS in B; C3a 2024/2025 within ±1.0 pp of
  A; C3b 2024/2025 within ±0.02 NRMSE of A.
* **G5** (KILL) — hours with system slack > 1 MW must not increase A→B, any year.
* **G-REPRO** (report) — B's scored criteria vs the committed run192 keeper
  bundle (the nyiso-128 K6-class disclosure; not a kill).

**G-COAL148 is NOT scored here** — its committed scorer is
``scripts/probes/ercot185_coal148.py``, run against the same pair.

The re-gate verdict is **RG-PASS iff G2, G3, G4 and G5 all hold**.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot193_ab_gates.py \
        --base results/calibration/ercot193_ctl_nosoc \
        --arm  results/calibration/ercot193_arm_soc
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pandas as pd  # noqa: E402

from calibration_verdict import (  # noqa: E402  (the rubric's own scorers)
    score_price_mean,
    score_price_shape,
    score_price_tail,
)

RUNS_DIR = REPO / "frontend" / "data" / "backcast" / "runs"
BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench" / "ERCOT"


def _payload(run_id: str) -> dict:
    raw = (RUNS_DIR / f"{run_id}.js").read_text()
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', raw)
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))["years"]


def _bench(year: int) -> dict:
    return json.loads(gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes()))[
        "bench"
    ]

YEARS = (2023, 2024, 2025)
ACTUAL_LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
KEEPER_BUNDLE = REPO / "results" / "calibration" / "ercot192_arm_B"
DEFAULT_OUT = REPO / "results" / "calibration" / "ercot193_ab_gates.json"

#: EIA-930 measured ERCOT NG:BAT annual battery discharge, 2025 — the committed
#: ercot-162 constant (`_ercot162_storage_ab.EIA930_NGBAT_2025_GWH`).
EIA930_NGBAT_2025_GWH = 5444.8
#: ercot-167 G1's measured actual: mean battery discharge in the 61 actual
#: RT >$1000 hours of 2023 (SCED-measured, FINDING-ercot167 §1).
G1_ACTUAL_MW = 423.0
G1_GAP_CLOSE_FRAC = 0.40
G1_OVERSHOOT_MW = 300.0
G2_MIN_RATIO = 0.70
G4_C3A_BAND_PP = 1.0
G4_C3B_BAND = 0.02


def _max_zonal(bundle: Path, year: int) -> pd.Series:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return df.groupby("hour")["price"].max()


def _slack_hours(bundle: Path, year: int) -> int:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return int((df.groupby("hour")["slack"].sum() > 1.0).sum())


def _discharge(bundle: Path, year: int) -> pd.Series:
    df = pd.read_parquet(bundle / "hourly" / f"storage_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return df.groupby("hour")["discharge_mw"].sum()


def _actual_rt(year: int) -> pd.Series:
    df = pd.read_parquet(ACTUAL_LMP)
    df = df[df["year"] == year]
    return df.set_index("hour")["rt"]


def _crit_status(bundle: Path) -> dict:
    """Per-criterion status block, as the solve's metrics.json wrote it."""
    return json.load(open(bundle / "metrics.json"))["criteria"]


def _c3(run_id: str) -> dict:
    """Scored C3a/C3b/C3c per year for a REGISTERED run, on the rubric's own
    scorers fed with the registered payload + committed bench."""
    years = _payload(run_id)
    out: dict = {}
    for yr, ypay in years.items():
        ybench = _bench(int(yr))
        r3a = score_price_mean(int(yr), ypay, ybench)
        r3b = score_price_shape(int(yr), ypay, ybench)
        tails = [
            r
            for r in score_price_tail(int(yr), ypay, "ERCOT")
            if r.get("status") != "SKIPPED"
        ]
        model, actual = r3a.get("model"), r3a.get("actual")
        err_pct = (
            round(100.0 * (float(model) / float(actual) - 1.0), 2)
            if model is not None and actual is not None
            else None
        )
        out[yr] = {
            "c3a_err_pct": err_pct,
            "c3a_model": model,
            "c3a_actual": actual,
            "c3b_nrmse": r3b.get("model"),
            "c3c": tails[0].get("magnitude") if tails else None,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--base-id", default="2026-08-13-ercot193-ctl-nosoc")
    ap.add_argument("--arm-id", default="2026-08-13-ercot193-arm-soc")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    A, B = args.base, args.arm
    out: dict = {"base": str(A), "arm": str(B)}

    # --- G1 (target, 2023): battery discharge at the actual >$1000 hours.
    act23 = _actual_rt(2023)
    hot = act23[act23 > 1000.0].index
    dA = float(_discharge(A, 2023).reindex(hot).mean())
    dB = float(_discharge(B, 2023).reindex(hot).mean())
    gap = dA - G1_ACTUAL_MW
    closed = (dA - dB) / gap if gap > 0 else None
    out["G1"] = {
        "hours_gt1000": int(len(hot)),
        "control_mw": round(dA, 1),
        "arm_mw": round(dB, 1),
        "actual_mw": G1_ACTUAL_MW,
        "gap_closed_frac": round(closed, 3) if closed is not None else None,
        "overshoot_flag": bool(dB < G1_OVERSHOOT_MW),
        "pass": bool(closed is not None and closed >= G1_GAP_CLOSE_FRAC),
    }

    # --- G2 (KILL): 2025 volume guard; 2024 report-only.
    volB25 = float(_discharge(B, 2025).sum()) / 1000.0
    volA25 = float(_discharge(A, 2025).sum()) / 1000.0
    ratio = volB25 / EIA930_NGBAT_2025_GWH
    out["G2"] = {
        "arm_2025_gwh": round(volB25, 1),
        "control_2025_gwh": round(volA25, 1),
        "measured_ng_bat_gwh": EIA930_NGBAT_2025_GWH,
        "arm_ratio": round(ratio, 3),
        "arm_2024_gwh": round(float(_discharge(B, 2024).sum()) / 1000.0, 1),
        "control_2024_gwh": round(float(_discharge(A, 2024).sum()) / 1000.0, 1),
        "pass": bool(ratio >= G2_MIN_RATIO),
    }

    # --- G3 (KILL): spurious tail hours must not increase A→B, per year.
    g3 = {}
    for year in YEARS:
        act = _actual_rt(year)
        sp = {}
        for tag, bundle in (("control", A), ("arm", B)):
            mz = _max_zonal(bundle, year)
            common = mz.index.intersection(act.index)
            sp[tag] = int(((mz.loc[common] > 200.0) & (act.loc[common] <= 200.0)).sum())
        g3[str(year)] = {**sp, "pass": bool(sp["arm"] <= sp["control"])}
    g3["pass"] = all(v["pass"] for k, v in g3.items() if k != "pass")
    out["G3"] = g3

    # --- G4 (KILL): no-regress on the scored criteria.
    cb = _crit_status(B)
    holds = {
        c: cb.get(c, {}).get("status") in ("PASS", "CAVEAT")
        for c in ("fuelmix", "sysvol", "dispatch_corr", "forced_share")
    }
    c3A, c3B = _c3(args.base_id), _c3(args.arm_id)
    bands = {}
    for year in ("2024", "2025"):
        da = abs(float(c3B[year]["c3a_err_pct"]) - float(c3A[year]["c3a_err_pct"]))
        ds = abs(float(c3B[year]["c3b_nrmse"]) - float(c3A[year]["c3b_nrmse"]))
        bands[year] = {
            "c3a_control": c3A[year]["c3a_err_pct"],
            "c3a_arm": c3B[year]["c3a_err_pct"],
            "c3a_delta_pp": round(da, 3),
            "c3a_pass": bool(da <= G4_C3A_BAND_PP),
            "c3b_control": c3A[year]["c3b_nrmse"],
            "c3b_arm": c3B[year]["c3b_nrmse"],
            "c3b_delta": round(ds, 4),
            "c3b_pass": bool(ds <= G4_C3B_BAND),
        }
    out["G4"] = {
        "criteria_hold": holds,
        "bands": bands,
        "pass": all(holds.values())
        and all(b["c3a_pass"] and b["c3b_pass"] for b in bands.values()),
    }

    # --- G5 (KILL): shed hours must not increase A→B.
    g5 = {}
    for year in YEARS:
        sA, sB = _slack_hours(A, year), _slack_hours(B, year)
        g5[str(year)] = {"control": sA, "arm": sB, "pass": bool(sB <= sA)}
    g5["pass"] = all(v["pass"] for k, v in g5.items() if k != "pass")
    out["G5"] = g5

    # --- Full-magnitude reports: C3a/C3b/C3c per year, both runs.
    out["full_magnitude"] = {
        str(year): {"control": c3A[str(year)], "arm": c3B[str(year)]}
        for year in YEARS
    }

    # --- G-REPRO (report): the arm replay vs the committed run192 keeper —
    # same C3 scorers on both registered payloads, plus the determinations.
    try:
        c3K = _c3("2026-08-12-run192-arm-coal-peak")
        drift = {
            yr: {"keeper": c3K[yr], "arm_replay": c3B[yr]}
            for yr in c3K
            if c3K[yr] != c3B[yr]
        }
        out["G_REPRO"] = {
            "keeper_determination": json.load(open(KEEPER_BUNDLE / "metrics.json")).get(
                "determination"
            ),
            "arm_replay_determination": json.load(open(B / "metrics.json")).get(
                "determination"
            ),
            "n_drifted_years": len(drift),
            "drift": drift,
        }
    except FileNotFoundError:
        out["G_REPRO"] = {"error": "keeper artifacts unavailable"}

    out["RG_VERDICT"] = (
        "RG-PASS"
        if (out["G2"]["pass"] and out["G3"]["pass"] and out["G4"]["pass"] and out["G5"]["pass"])
        else "RG-FAIL"
    )
    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("G1", "G2", "RG_VERDICT")}, indent=2))
    print("G3", {k: v for k, v in out["G3"].items()})
    print("G4 pass:", out["G4"]["pass"], out["G4"]["bands"])
    print("G5", out["G5"])
    print("G-REPRO drifted years =", out["G_REPRO"].get("n_drifted_years"))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
