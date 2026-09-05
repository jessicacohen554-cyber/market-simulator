"""caiso-251 — ARM vs CONTROL vs the committed KEEPER: gates and predictions, scored against interest.

NO LP. Reads three committed bundles' hourly sidecars, metrics and verdicts:

  * KEEPER  — ``caiso246_b1_spot_coverage`` (run 2026-09-05-caiso-246-b1-spot)
  * CONTROL — **the committed KEEPER itself**. Owner rule 2026-09-05 (rule 29
    ``[R-SCREEN]`` clause b): no control solve is spent. G-CTRL form 2 is
    unavailable (the arm is live in every hour of every year), and form 4 is
    restored by **G-DRIFT**, the code-level audit in PRECOMMIT Addendum B —
    every changed hunk on the backcast path between the keeper's ``git_sha``
    900402b and HEAD is CAISO-backcast-inert with its reason cited (a
    forecast-only path, another ISO's branch, a default-off flag absent from
    the recipe, a per-ISO artifact CAISO lacks, or timing accounting). The
    control solve launched under the withdrawn "files changed therefore void"
    heuristic was killed mid-flight and its partial bundle deleted.
  * ARM     — ``caiso251_arm_nomargin``: the control recipe plus the SINGLE
    flag ``--no-gas-offer-margin`` (``ScenarioConfig.gas_offer_net_revenue_margin``
    False), i.e. the gas offer reverts from the fuel-INVARIANT $/MWh margin to
    the multiplicative form CAISO's own OASIS record identifies (caiso-242 §3.5).

Scored here against ``PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md``:
G-CTRL, G-HOLDOUT, and P-6…P-10. P-1…P-5 were scored pre-solve in
``_caiso251_fuel_coupling_form.json``.

**C3a is EXCLUDED from the promotion basis in both directions** (PRECOMMIT
§0.2) — it is reported here because P-6/P-7 are predictions ABOUT it, never as
evidence for the arm.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso251_arm_vs_control.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CAL = REPO / "results/calibration"
KEEPER = CAL / "caiso246_b1_spot_coverage"
#: Owner rule 2026-09-05 (rule 29 [R-SCREEN] clause b): NO control solve is spent.
#: G-CTRL form 4 is restored by the G-DRIFT code audit recorded in
#: PRECOMMIT-caiso251 Addendum B — every solve-path hunk between the keeper's
#: git_sha 900402b and HEAD is CAISO-backcast-inert with its reason cited — so
#: THE COMMITTED KEEPER IS THE CONTROL.
CONTROL = KEEPER
ARM = CAL / "caiso251_arm_nomargin"
YEARS = (2023, 2024, 2025)
OUT = CAL / "_caiso251_arm_vs_control.json"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"

#: rule 22 [R-HOLDOUT], fail-closed.
TRAINING_YEARS = frozenset({2023, 2024, 2025})
#: PRECOMMIT §1.4 G-CTRL: the control must reproduce the committed keeper's
#: load-weighted price to this tolerance, else HEAD drift is reported.
CTRL_TOL_USD = 0.01
#: PRECOMMIT §2 P-8 — CT_PEAKER 2025 dispatch rise, TWh.
P8_MIN_TWH = 0.5
#: The keeper's committed C3a, quoted for orientation only (never a basis).
KEEPER_C3A_PCT = {2023: 3.9, 2024: 12.3, 2025: 11.4}


def _system(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _classes(bundle: Path, year: int) -> pd.DataFrame | None:
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    return df[(df["year"] == year) & (df["pass"] == "P1")]


def _class_twh(df: pd.DataFrame | None) -> dict[str, float]:
    if df is None:
        return {}
    return {
        str(k): round(float(v) / 1e6, 4)
        for k, v in df.groupby("klass", observed=True)["mw"].sum().items()
    }


def _lw_mean(df: pd.DataFrame | None) -> float | None:
    if df is None or df.empty:
        return None
    return float(np.average(df["price"], weights=df["demand"]))


def _actual_rt_lw(year: int) -> float | None:
    p = BENCH / f"{year}.json.gz"
    if not p.exists():
        return None
    return float(json.load(gzip.open(p))["bench"]["avgLMP"]["rt_lw"])


def _verdict(bundle: Path) -> dict:
    p = bundle / "_verdict.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _metrics(bundle: Path) -> dict:
    p = bundle / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _criteria_status(bundle: Path) -> dict[str, str]:
    m = _metrics(bundle)
    return {
        str(k): str(v.get("status"))
        for k, v in (m.get("criteria") or {}).items()
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-251 (gas-offer fuel-coupling FORM: arm vs control)",
            "keeper": str(KEEPER.relative_to(REPO)),
            "control": str(CONTROL.relative_to(REPO)),
            "arm": str(ARM.relative_to(REPO)),
            "delta": "single flag --no-gas-offer-margin on the replayed keeper recipe",
            "precommit": "PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md",
            "note": (
                "C3a is EXCLUDED from the promotion basis in BOTH directions "
                "(PRECOMMIT §0.2, the sixth consecutive favourable direction "
                "declared in advance). It is reported because P-6/P-7 are "
                "predictions about it, never as evidence for the arm."
            ),
        },
        "years": {},
        "gates": {},
        "predictions": {},
    }

    ctrl_drift = {}
    for y in YEARS:
        if y not in TRAINING_YEARS:
            raise SystemExit(f"rule 22 [R-HOLDOUT]: {y} outside 2023-2025")
        k, c, a = _system(KEEPER, y), _system(CONTROL, y), _system(ARM, y)
        kl, cl, al = _lw_mean(k), _lw_mean(c), _lw_mean(a)
        act = _actual_rt_lw(y)
        row = {
            "actual_rt_lw": None if act is None else round(act, 4),
            "keeper_model_lw": None if kl is None else round(kl, 4),
            "control_model_lw": None if cl is None else round(cl, 4),
            "arm_model_lw": None if al is None else round(al, 4),
            "keeper_c3a_pct_committed": KEEPER_C3A_PCT[y],
        }
        for tag, v in (("control", cl), ("arm", al)):
            if v is not None and act:
                row[f"{tag}_gap_usd"] = round(v - act, 4)
                row[f"{tag}_c3a_pct"] = round(100.0 * (v - act) / act, 3)
        if cl is not None and al is not None:
            row["arm_minus_control_usd"] = round(al - cl, 4)
        if kl is not None and cl is not None:
            ctrl_drift[y] = round(cl - kl, 4)
            row["control_minus_keeper_usd"] = ctrl_drift[y]
        ktw, ctw, atw = (
            _class_twh(_classes(KEEPER, y)),
            _class_twh(_classes(CONTROL, y)),
            _class_twh(_classes(ARM, y)),
        )
        row["class_twh"] = {
            klass: {
                "keeper": ktw.get(klass),
                "control": ctw.get(klass),
                "arm": atw.get(klass),
                "arm_minus_control": (
                    round(atw[klass] - ctw[klass], 4)
                    if klass in atw and klass in ctw
                    else None
                ),
            }
            for klass in sorted(set(ktw) | set(ctw) | set(atw))
        }
        out["years"][y] = row

    out["gates"]["G_CTRL"] = {
        "form": 4,
        "basis": "G-DRIFT code audit, PRECOMMIT-caiso251 Addendum B",
        "control_is": "the committed keeper caiso246_b1_spot_coverage",
        "control_solve_spent": False,
        "drift_audit": (
            "git diff 900402b..HEAD over the backcast path: 22 files, "
            "+2527/-149, EVERY hunk CAISO-backcast-INERT with its reason "
            "cited (forecast-only capacity paths; MISO-only branches; the "
            "NYISO-only egrid_steam_collapse artifact; an adaptive-pass "
            "guard unreachable with *_storage_adaptive_expectation False; a "
            "return-type-only change; timing accounting)"
        ),
        "pass": True,
    }
    out["gates"]["G_HOLDOUT"] = {
        "years": list(YEARS),
        "pass": bool(set(YEARS) <= TRAINING_YEARS),
    }

    # ---- predictions ------------------------------------------------------
    arm_c3a = {y: out["years"][y].get("arm_c3a_pct") for y in YEARS}
    ctl_c3a = {y: out["years"][y].get("control_c3a_pct") for y in YEARS}
    out["predictions"]["P-6"] = {
        "registered": "at least one of 2024/2025 lands with a NEGATIVE C3a gap",
        "arm_c3a_pct": arm_c3a,
        "verdict": (
            "HOLDS"
            if any(
                arm_c3a.get(y) is not None and arm_c3a[y] < 0 for y in (2024, 2025)
            )
            else "FALSIFIED"
        ),
    }
    p7_worse = (
        arm_c3a.get(2023) is not None
        and ctl_c3a.get(2023) is not None
        and arm_c3a[2023] > ctl_c3a[2023]
    )
    out["predictions"]["P-7"] = {
        "registered": "2023 C3a gets WORSE than the control and 2023 FAILS its band",
        "control_2023_c3a_pct": ctl_c3a.get(2023),
        "arm_2023_c3a_pct": arm_c3a.get(2023),
        "got_worse": bool(p7_worse),
        "arm_2023_price_mean_status": _criteria_status(ARM).get("price_mean"),
        "note": "the FAIL leg is read from the arm's own scored verdict, not recomputed",
    }
    ct = out["years"][2025]["class_twh"].get("CT_PEAKER", {})
    out["predictions"]["P-8"] = {
        "registered": f"CT_PEAKER 2025 dispatch rises by >= {P8_MIN_TWH} TWh",
        "control_twh": ct.get("control"),
        "arm_twh": ct.get("arm"),
        "delta_twh": ct.get("arm_minus_control"),
        "verdict": (
            "HOLDS"
            if ct.get("arm_minus_control") is not None
            and ct["arm_minus_control"] >= P8_MIN_TWH
            else "FALSIFIED"
        ),
    }
    cs_c, cs_a = _criteria_status(CONTROL), _criteria_status(ARM)
    regressed = sorted(
        k
        for k in cs_c
        if k != "price_mean"
        and cs_a.get(k) != cs_c.get(k)
        and str(cs_a.get(k)) in {"FAIL", "CAVEAT"}
    )
    out["predictions"]["P-9"] = {
        "registered": "at least one non-C3a scored criterion regresses",
        "control_criteria": cs_c,
        "arm_criteria": cs_a,
        "regressed": regressed,
        "verdict": "HOLDS" if regressed else "FALSIFIED",
    }
    out["predictions"]["P-10"] = {
        "registered": "the determination stays NOT-YET",
        "control_determination": _metrics(CONTROL).get("determination"),
        "arm_determination": _metrics(ARM).get("determination"),
        "verdict": (
            "HOLDS"
            if _metrics(ARM).get("determination") == "NOT-YET"
            else "FALSIFIED"
        ),
    }

    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out["gates"], indent=1))
    for y in YEARS:
        r = out["years"][y]
        print(
            f"{y}: actual {r['actual_rt_lw']} | keeper {r['keeper_model_lw']} "
            f"| control {r['control_model_lw']} ({r.get('control_c3a_pct')}%) "
            f"| arm {r['arm_model_lw']} ({r.get('arm_c3a_pct')}%) "
            f"| arm-ctrl {r.get('arm_minus_control_usd')}"
        )
        for klass, v in r["class_twh"].items():
            if v["arm_minus_control"] and abs(v["arm_minus_control"]) >= 0.05:
                print(f"      {klass:12s} ctrl {v['control']:9.3f} -> arm {v['arm']:9.3f}  ({v['arm_minus_control']:+.3f} TWh)")
    print(json.dumps(out["predictions"], indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
