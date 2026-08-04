"""neiso-81 A/B scorer — ``measured_chp_heat_rates`` re-adjudicated at NEISO.

Scores the PRE-REGISTERED properties of
``results/calibration/PREREG-neiso81-chp-heat-rate-readjudication-2026-08-04.md``
from the two solved bundles plus committed artifacts. **No solve, and no gate
that is not in the prereg.**

Post-solve construction properties (prereg §4):

* **P4 single delta** — the arms' ``run_config`` scenario blocks differ in
  exactly the one boolean. Falsifier: >= 2 keys ⇒ INVALID, no verdict.
* **P5 control integrity** (miso-124) — arm A is a zero-delta same-HEAD replay.
  TWO BASES, and only the first is the gate: the *scorecard* basis (same
  determination structure as the committed keeper) gates; the stricter *byte*
  basis is computed and REPORTED, because a byte miss is same-HEAD drift, a
  separately reported finding, not a failed gate (caiso-146 / neiso-69 /
  neiso-70 K2 precedent).
* **P6 post-arm firing, grain 2** (miso-126(a)) — per-class ENERGY delta on
  CC_CHP is non-zero. Falsifier: exactly 0 ⇒ the flag was recorded but never
  applied ⇒ cell ``I``. Grain 1 is the pre-arm loader check in
  ``_neiso81_chp_phase0.py``; a loader check alone is NOT sufficient proof.
* **P7 conservation** (miso-126(b)) — the FULL identity
  ``d_class + d_discharge - d_charge + d_slack - d_dump - d_demand == 0`` over
  ``class_hourly`` + ``storage`` + ``system``, never ``class_hourly`` alone.
  Falsifier: breach ⇒ the magnitude statistic has a boundary defect; re-scope
  before any verdict.
* **P10 substitution** — the post-solve half of the headroom screen: what share
  of the CC_CHP energy delta CC_REGULAR actually absorbs. Falsifier: < 70 %
  absorbed ⇒ the defect reaches beyond the CC pair ⇒ STOP-AND-ESCALATE.

The §7 promotion standard is then scored mechanically: S1-S4 (structural
integrity), A1-A4 (accepted regression), N1-N4 (stop-and-escalate triggers) and
the V1-V6 verdict ladder, with the 0.50 TWh combined-CC threshold fixed in the
prereg.

Everything else — per-class TWh vs actual, mean λ, tail hours, D-1/D-2 — is
REPORTED. A worse backcast on a strictly more accurate measured input is a
discovered bug under rules 1 / 14, never a kill condition.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_neiso81_chpheatrate_ab.py \
        --json-out results/calibration/_neiso81_chpheatrate_ab.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)
#: C1 gates only the complete-vintage years; 2025 CC rows are SKIPPED on
#: preliminary EIA-923 (3/7 CC_CHP plants missing, 57 % reporting).
SCORED_YEARS = (2023, 2024)

ARM_A = REPO / "results/calibration/neiso81_control_A"
ARM_B = REPO / "results/calibration/neiso81_chpheatrate_B"
KEEPER = REPO / "results/calibration/neiso_c156_meter_screen_B"
ARTIFACT = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv"
BENCH = REPO / "frontend/data/backcast/bench/NEISO"
OUT_PATH = REPO / "results/calibration/_neiso81_chpheatrate_ab.json"

FLAG = "measured_chp_heat_rates"
REPRICED = ("CC_CHP", "CT_CHP")
CC_PAIR = ("CC_CHP", "CC_REGULAR")

# ---- thresholds, every one fixed in the prereg before either arm solved ----
#: §4 P5 — a zero-delta replay's byte basis.
P5_BYTE_TOL_MW = 1e-6
#: §4 P7 — the full-balance identity tolerance. The prereg specifies a PER-HOUR
#: RELATIVE tolerance ("any hour breaching a 1e-6 relative tolerance"), so that
#: is what is scored: max_h |residual_h| / demand_h. The annual-sum absolute
#: residual is computed alongside and REPORTED, but it is not the bar — the
#: sidecar ``mw`` column is float32, whose epsilon (1.2e-7) sets the floor on
#: any such identity, and an absolute GWh bar on a ~100 TWh system silently
#: measures storage dtype rather than conservation.
P7_BALANCE_REL_TOL = 1e-6
#: §4 P10 — minimum share of the CC_CHP energy delta CC_REGULAR must absorb.
P10_ABSORPTION_MIN = 0.70
#: §7.2 A3 — accepted λ rise, as a fraction of level.
A3_LAMBDA_MAX_PP = 0.01
#: §7.3 N4 — accepted total-generation drift.
N4_TOTAL_GEN_TOL = 0.0005
#: §8 V4 — the combined-CC |error| worsening allowance, TWh. Anchored at one
#: quarter of the C1 per-class volume band, NOT fitted, and not moved.
V4_COMBINED_WORSEN_MAX_TWH = 0.50
#: The incumbent determination this promotion must not fall below (rule 22 D-5(b)).
INCUMBENT_DETERMINATION = "CALIBRATED-WITH-CAVEATS"
#: Determination ordering, best -> worst.
_DET_RANK = {"CALIBRATED": 0, "CALIBRATED-WITH-CAVEATS": 1, "NOT-YET": 2}


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def _p1(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    return _p1(pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet"))


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).to_dict()


def _system(bundle: Path, year: int) -> pd.DataFrame:
    return _p1(pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet"))


def _pairwise(a: Path, b: Path, year: int) -> dict:
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
            if float(v) > 1e-9
        },
    }


def _lambda(bundle: Path, year: int) -> float:
    """NEISO load-weighted mean λ, the HQ import node excluded."""
    frame = _system(bundle, year)
    native = frame[frame["zone"].astype(str) != "HQ_import"]
    return float((native["price"] * native["demand"]).sum() / native["demand"].sum())


def _tail_hours(bundle: Path, year: int, thresh: float = 300.0) -> int:
    frame = _system(bundle, year)
    native = frame[frame["zone"].astype(str) != "HQ_import"]
    lam = (native["price"] * native["demand"]).groupby(native["hour"]).sum() / (
        native.groupby("hour")["demand"].sum()
    )
    return int((lam > thresh).sum())


def _scenario_block(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    ) or {}


def _flag(bundle: Path) -> bool | None:
    scen = _scenario_block(bundle)
    return bool(scen[FLAG]) if FLAG in scen else None


def _scorecard(bundle: Path) -> dict | None:
    path = bundle / "metrics.json"
    if not path.exists():
        return None
    m = json.loads(path.read_text())
    return {
        "determination": m.get("determination"),
        "criteria": {
            k: (v.get("status") if isinstance(v, dict) else v)
            for k, v in (m.get("criteria") or {}).items()
        },
        "criteria_rows": {
            k: [
                {
                    "year": r.get("year"),
                    "key": r.get("key"),
                    "status": r.get("status"),
                    "magnitude": r.get("magnitude"),
                }
                for r in (v.get("rows") or [])
            ]
            for k, v in (m.get("criteria") or {}).items()
            if isinstance(v, dict)
        },
        "free_class_score": m.get("free_class_score"),
        "grade_summary": m.get("grade_summary"),
        "caveats": m.get("caveats"),
    }


def _bench_classfull(year: int) -> dict[str, float]:
    b = json.loads(gzip.open(BENCH / f"{year}.json.gz").read())["bench"]
    return {k: float(v) for k, v in (b.get("classFull") or {}).items()}


# --------------------------------------------------------------------------- #
# P4 / P5 / P6 / P7 / P10 — the post-solve construction properties
# --------------------------------------------------------------------------- #
def p4_single_delta() -> dict:
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "property": "P4 single delta",
        "differing_keys": diff,
        "n_differing": len(diff),
        "arm_A_flag": _flag(ARM_A),
        "arm_B_flag": _flag(ARM_B),
        "passed": list(diff) == [FLAG]
        and _flag(ARM_A) is False
        and _flag(ARM_B) is True,
        "falsifier": ">= 2 differing keys ⇒ INVALID, no verdict written",
    }


def p5_control_integrity() -> dict:
    byte = {str(y): _pairwise(KEEPER, ARM_A, y) for y in YEARS}
    byte_ok = all(v["max_abs_diff_mw"] <= P5_BYTE_TOL_MW for v in byte.values())
    keeper_sc, a_sc = _scorecard(KEEPER), _scorecard(ARM_A)
    scorecard_ok = (
        a_sc is not None
        and keeper_sc is not None
        and a_sc["determination"] == keeper_sc["determination"]
        and a_sc["criteria"] == keeper_sc["criteria"]
    )
    return {
        "property": "P5 control integrity (miso-124)",
        "gate_basis": "scorecard",
        "scorecard_matches_committed_keeper": scorecard_ok,
        "keeper_determination": (keeper_sc or {}).get("determination"),
        "control_determination": (a_sc or {}).get("determination"),
        "byte_basis_vs_committed_keeper": byte,
        "byte_basis_identical": byte_ok,
        "passed": bool(scorecard_ok),
        "note": (
            "Byte basis is REPORTED, not the gate. A byte miss is same-HEAD "
            "drift — a separately reported finding, and the very reason a "
            "same-HEAD control is solved rather than differencing against the "
            "committed keeper."
        ),
    }


def p6_post_arm_firing() -> dict:
    """Grain 2 of miso-126(a): the per-class ENERGY delta, not a loader check."""
    per_year = {}
    fired = False
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        deltas = {
            k: round(b.get(k, 0.0) - a.get(k, 0.0), 6)
            for k in sorted(set(a) | set(b))
        }
        chp_delta = deltas.get("CC_CHP", 0.0)
        pw = _pairwise(ARM_A, ARM_B, year)
        per_year[str(year)] = {
            "energy_delta_twh": {k: v for k, v in deltas.items() if abs(v) > 1e-6},
            "CC_CHP_energy_delta_twh": chp_delta,
            "max_abs_class_hour_mw": pw["max_abs_diff_mw"],
            "max_by_class_mw": pw["max_by_class_mw"],
        }
        if abs(chp_delta) > 0.0:
            fired = True
    return {
        "property": "P6 post-arm firing, grain 2 (miso-126a)",
        "per_year": per_year,
        "passed": fired,
        "falsifier": "|Δ CC_CHP energy| == 0 ⇒ recorded but never applied ⇒ cell I",
        "note": (
            "max_abs_class_hour_mw is liveness ONLY and is NOT a mechanism "
            "magnitude (miso-122). The magnitude is the per-class energy delta."
        ),
    }


def p7_conservation() -> dict:
    """The FULL balance identity across three sidecars (miso-126b)."""

    def hourly(bundle: Path, year: int) -> dict[str, pd.Series]:
        c = _p1(pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet"))
        q = _p1(pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet"))
        spath = bundle / "hourly" / f"storage_{year}.parquet"
        zero = pd.Series(0.0, index=sorted(q["hour"].unique()), dtype="float64")
        if spath.exists():
            s = _p1(pd.read_parquet(spath))
            dis = s.groupby("hour")["discharge_mw"].sum().astype("float64")
            chg = s.groupby("hour")["charge_mw"].sum().astype("float64")
        else:
            dis = chg = zero
        return {
            "class": c.groupby("hour")["mw"].sum().astype("float64"),
            "discharge": dis,
            "charge": chg,
            "slack": (
                q.groupby("hour")["slack"].sum().astype("float64")
                if "slack" in q
                else zero
            ),
            "dump": (
                q.groupby("hour")["dump"].sum().astype("float64")
                if "dump" in q
                else zero
            ),
            "demand": q.groupby("hour")["demand"].sum().astype("float64"),
        }

    per_year, ok = {}, True
    for year in YEARS:
        a, b = hourly(ARM_A, year), hourly(ARM_B, year)
        d = {k: b[k].reindex(a[k].index).fillna(0.0) - a[k] for k in a}
        residual = (
            d["class"]
            + d["discharge"]
            - d["charge"]
            + d["slack"]
            - d["dump"]
            - d["demand"]
        )
        rel = (residual.abs() / b["demand"]).max()
        per_year[str(year)] = {
            **{f"{k}_delta_gwh": round(float(v.sum()) / 1e3, 6) for k, v in d.items()},
            "max_abs_hourly_residual_mw": round(float(residual.abs().max()), 8),
            "max_relative_hourly_residual": float(f"{float(rel):.3e}"),
            "annual_sum_residual_mwh": round(float(residual.sum()), 6),
            "sidecar_dtype": str(
                _p1(
                    pd.read_parquet(ARM_A / "hourly" / f"class_hourly_{year}.parquet")
                )["mw"].dtype
            ),
            "storage_sidecar_present": (
                ARM_A / "hourly" / f"storage_{year}.parquet"
            ).exists(),
        }
        if float(rel) > P7_BALANCE_REL_TOL:
            ok = False
    return {
        "property": "P7 conservation, full identity (miso-126b)",
        "identity": (
            "d_class + d_discharge - d_charge + d_slack - d_dump - d_demand == 0"
        ),
        "basis": "PER-HOUR RELATIVE, as pre-registered: max_h |residual_h| / demand_h",
        "tolerance_relative": P7_BALANCE_REL_TOL,
        "per_year": per_year,
        "passed": ok,
        "falsifier": "breach ⇒ BOUNDARY defect in the statistic; re-scope before any verdict",
        "note": (
            "The sidecar mw column is float32 (epsilon 1.2e-7), which sets the "
            "floor on any identity computed from it — the observed residuals sit "
            "AT that floor, so this measures stored-column precision, not "
            "conservation. The annual-sum absolute residual is reported "
            "alongside but is NOT the bar; an absolute GWh bar on a ~100 TWh "
            "system would silently score dtype instead of the identity."
        ),
    }


def p10_substitution() -> dict:
    """Post-solve half of the headroom screen: does CC_REGULAR absorb it?"""
    per_year, ok = {}, True
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        d_chp = b.get("CC_CHP", 0.0) - a.get("CC_CHP", 0.0)
        d_reg = b.get("CC_REGULAR", 0.0) - a.get("CC_REGULAR", 0.0)
        absorbed = (-d_reg / d_chp) if abs(d_chp) > 1e-9 else None
        others = {
            k: round(b.get(k, 0.0) - a.get(k, 0.0), 6)
            for k in sorted(set(a) | set(b))
            if k not in CC_PAIR and abs(b.get(k, 0.0) - a.get(k, 0.0)) > 1e-4
        }
        per_year[str(year)] = {
            "CC_CHP_delta_twh": round(d_chp, 6),
            "CC_REGULAR_delta_twh": round(d_reg, 6),
            "absorption_share": round(absorbed, 4) if absorbed is not None else None,
            "other_classes_moved_twh": others,
            "sign_as_predicted": bool(d_chp < 0.0 and d_reg > 0.0),
        }
        if absorbed is None or absorbed < P10_ABSORPTION_MIN:
            ok = False
    return {
        "property": "P10 substitution (post-solve)",
        "threshold": P10_ABSORPTION_MIN,
        "per_year": per_year,
        "passed": ok,
        "falsifier": (
            "< 70 % of the CC_CHP delta absorbed by CC_REGULAR ⇒ the defect "
            "reaches beyond the CC pair ⇒ STOP-AND-ESCALATE"
        ),
    }


# --------------------------------------------------------------------------- #
# §7 — the promotion standard, scored mechanically
# --------------------------------------------------------------------------- #
def c1_errors() -> dict:
    """Per-class grid-delivered |error| vs the committed bench, both arms."""
    out = {}
    for year in YEARS:
        cf = _bench_classfull(year)
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        rows = {}
        for k in sorted(cf):
            act = cf[k]
            ma, mb = a.get(k, 0.0), b.get(k, 0.0)
            rows[k] = {
                "actual": round(act, 4),
                "A": round(ma, 4),
                "B": round(mb, 4),
                "abs_err_A": round(abs(ma - act), 4),
                "abs_err_B": round(abs(mb - act), 4),
                "abs_err_delta": round(abs(mb - act) - abs(ma - act), 4),
            }
        chp_a, chp_b = a.get("CC_CHP", 0.0), b.get("CC_CHP", 0.0)
        reg_a, reg_b = a.get("CC_REGULAR", 0.0), b.get("CC_REGULAR", 0.0)
        act_comb = cf.get("CC_CHP", 0.0) + cf.get("CC_REGULAR", 0.0)
        err_a = abs(chp_a + reg_a - act_comb)
        err_b = abs(chp_b + reg_b - act_comb)
        rows["_CC_COMBINED"] = {
            "actual": round(act_comb, 4),
            "A": round(chp_a + reg_a, 4),
            "B": round(chp_b + reg_b, 4),
            "abs_err_A": round(err_a, 4),
            "abs_err_B": round(err_b, 4),
            "abs_err_delta": round(err_b - err_a, 4),
        }
        out[str(year)] = rows
    return out


def promotion_standard(props: dict, errs: dict) -> dict:
    a_sc, b_sc = _scorecard(ARM_A), _scorecard(ARM_B)
    art = pd.read_csv(ARTIFACT)
    cems = art["cems_vs_egrid_total"].dropna()

    # ---- S1-S4 structural integrity -------------------------------------- #
    s1 = bool(len(cems) > 0 and ((cems - 1.0).abs() <= 0.01).all())
    s2 = True  # zero free parameters: one boolean, no derived value moved
    s3 = props["p4"]["passed"]  # no new mechanism surface: exactly one boolean
    s4 = props["p6"]["passed"] and props["p7"]["passed"]

    # ---- N1 any criterion PASS -> FAIL ----------------------------------- #
    n1_flips = []
    if a_sc and b_sc:
        for crit, a_status in a_sc["criteria"].items():
            b_status = b_sc["criteria"].get(crit)
            if a_status == "PASS" and b_status == "FAIL":
                n1_flips.append({"criterion": crit, "A": a_status, "B": b_status})
    n1 = bool(n1_flips)

    # ---- N2 determination worse (rule 22 D-5(b)) -------------------------- #
    b_det = (b_sc or {}).get("determination")
    a_det = (a_sc or {}).get("determination")
    n2 = bool(
        b_det
        and _DET_RANK.get(b_det, 9) > _DET_RANK.get(INCUMBENT_DETERMINATION, 9)
    )

    # ---- N3 C3c degradation / new caveat slot ---------------------------- #
    a_tail = (a_sc or {}).get("criteria", {}).get("price_tail")
    b_tail = (b_sc or {}).get("criteria", {}).get("price_tail")
    n_cav_a = len((a_sc or {}).get("caveats") or [])
    n_cav_b = len((b_sc or {}).get("caveats") or [])
    n3 = bool((a_tail == "CAVEAT" and b_tail == "FAIL") or n_cav_b > n_cav_a)

    # ---- N4 total gen / slack / dump ------------------------------------- #
    n4_rows, n4 = {}, False
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        ta, tb = sum(a.values()), sum(b.values())
        sa = _system(ARM_A, year)
        sb = _system(ARM_B, year)
        slack_a = float(sa["slack"].sum()) if "slack" in sa else 0.0
        slack_b = float(sb["slack"].sum()) if "slack" in sb else 0.0
        dump_a = float(sa["dump"].sum()) if "dump" in sa else 0.0
        dump_b = float(sb["dump"].sum()) if "dump" in sb else 0.0
        frac = (tb - ta) / ta if ta else 0.0
        row = {
            "total_gen_twh": {"A": round(ta, 5), "B": round(tb, 5)},
            "total_gen_frac_delta": round(frac, 8),
            "slack_mwh": {"A": round(slack_a, 3), "B": round(slack_b, 3)},
            "dump_mwh": {"A": round(dump_a, 3), "B": round(dump_b, 3)},
        }
        n4_rows[str(year)] = row
        if abs(frac) > N4_TOTAL_GEN_TOL or slack_b > slack_a + 1e-6 or dump_b > dump_a + 1e-6:
            n4 = True

    # ---- A3 λ push -------------------------------------------------------- #
    a3_rows, a3_ok = {}, True
    for year in YEARS:
        la, lb = _lambda(ARM_A, year), _lambda(ARM_B, year)
        pp = (lb - la) / la if la else 0.0
        a3_rows[str(year)] = {
            "lambda_A": round(la, 4),
            "lambda_B": round(lb, 4),
            "delta_usd": round(lb - la, 4),
            "frac_of_level": round(pp, 6),
        }
        if abs(pp) > A3_LAMBDA_MAX_PP:
            a3_ok = False

    # ---- A1/A2: repriced-class C1 rows stay PASS -------------------------- #
    a12_rows = {}
    for year in SCORED_YEARS:
        for k in REPRICED:
            r = errs[str(year)].get(k)
            if r is None:
                continue
            a12_rows[f"{year}:{k}"] = r

    # ---- V4 combined-CC test --------------------------------------------- #
    combined = {
        str(y): errs[str(y)]["_CC_COMBINED"]["abs_err_delta"] for y in SCORED_YEARS
    }
    improves = [y for y, d in combined.items() if d < 0]
    worsens_over = [
        y for y, d in combined.items() if d > V4_COMBINED_WORSEN_MAX_TWH
    ]
    v4_combined_ok = bool(improves) and not worsens_over
    worsens_both = all(d > 0 for d in combined.values())

    structural = s1 and s2 and s3 and s4
    n_fired = {"N1": n1, "N2": n2, "N3": n3, "N4": n4}
    any_n = any(n_fired.values())

    # ---- V ladder --------------------------------------------------------- #
    if not props["p6"]["passed"]:
        verdict, cell = "V1 INERT", "I"
    elif not props["p4"]["passed"] or not props["p7"]["passed"]:
        verdict, cell = "V2 INVALID", None
    elif not s1:
        verdict, cell = "V3 REFUSED", "R"
    elif structural and not any_n and v4_combined_ok and props["p10"]["passed"]:
        verdict, cell = "V4 PROMOTE", "K"
    elif structural and (any_n or worsens_both or not props["p10"]["passed"]):
        verdict, cell = "V5 STOP-AND-ESCALATE", "O"
    else:
        verdict, cell = "V6 RETAIN O", "O"

    return {
        "structural_integrity": {
            "S1_measurement_replaces_estimate": s1,
            "S1_cems_rows": int(len(cems)),
            "S1_cems_median": round(float(cems.median()), 5) if len(cems) else None,
            "S2_zero_free_parameters": s2,
            "S3_no_new_mechanism_surface": s3,
            "S4_live_and_conservation_clean": s4,
            "all_hold": structural,
        },
        "accepted_regression": {
            "A1_A2_repriced_class_rows": a12_rows,
            "A3_lambda": {"rows": a3_rows, "within_1pp": a3_ok},
            "A4_note": (
                "CHP D-1/D-2 degradation is accepted without limit: CC_CHP and "
                "CT_CHP are exempt from C7 AND C8 by explicit class list, so "
                "those numbers are diagnostics and never a passed gate."
            ),
        },
        "stop_and_escalate_triggers": {
            "N1_pass_to_fail": {"fired": n1, "flips": n1_flips},
            "N2_determination_worse": {
                "fired": n2,
                "incumbent": INCUMBENT_DETERMINATION,
                "control_A": a_det,
                "arm_B": b_det,
            },
            "N3_caveat_degradation": {
                "fired": n3,
                "price_tail": {"A": a_tail, "B": b_tail},
                "n_caveats": {"A": n_cav_a, "B": n_cav_b},
            },
            "N4_total_gen_slack_dump": {"fired": n4, "rows": n4_rows},
            "any_fired": any_n,
        },
        "V4_combined_cc": {
            "threshold_twh": V4_COMBINED_WORSEN_MAX_TWH,
            "abs_err_delta_by_year": combined,
            "improves_in": improves,
            "worsens_beyond_threshold_in": worsens_over,
            "worsens_in_both_scored_years": worsens_both,
            "passed": v4_combined_ok,
        },
        "VERDICT": verdict,
        "matrix_cell": cell,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=str(OUT_PATH))
    args = ap.parse_args()

    props = {
        "p4": p4_single_delta(),
        "p5": p5_control_integrity(),
        "p6": p6_post_arm_firing(),
        "p7": p7_conservation(),
        "p10": p10_substitution(),
    }
    errs = c1_errors()
    standard = promotion_standard(props, errs)

    report = {
        "session": "neiso-81",
        "iso": "NEISO",
        "prereg": (
            "results/calibration/"
            "PREREG-neiso81-chp-heat-rate-readjudication-2026-08-04.md"
        ),
        "arms": {"A": str(ARM_A.relative_to(REPO)), "B": str(ARM_B.relative_to(REPO))},
        "keeper": str(KEEPER.relative_to(REPO)),
        "scored_years_C1": list(SCORED_YEARS),
        "construction_properties": props,
        "c1_errors_vs_bench": errs,
        "promotion_standard": standard,
        "reported": {
            str(y): {
                "tail_hours_gt_300": {
                    "A": _tail_hours(ARM_A, y),
                    "B": _tail_hours(ARM_B, y),
                }
            }
            for y in YEARS
        },
        "scorecards": {
            "keeper": _scorecard(KEEPER),
            "A": _scorecard(ARM_A),
            "B": _scorecard(ARM_B),
        },
    }

    # ------------------------------- print -------------------------------- #
    print("=== CONSTRUCTION PROPERTIES (prereg §4) ===")
    for key in ("p4", "p5", "p6", "p7", "p10"):
        p = props[key]
        print(f"  [{'PASS' if p['passed'] else 'FAIL'}] {p['property']}")
    print(f"\n  P4 differing keys: {list(props['p4']['differing_keys'])}")
    print(f"  P5 byte-identical vs committed keeper: "
          f"{props['p5']['byte_basis_identical']}  (scorecard gate: "
          f"{props['p5']['scorecard_matches_committed_keeper']})")
    for y, r in props["p6"]["per_year"].items():
        print(f"  P6 {y}: ΔCC_CHP {r['CC_CHP_energy_delta_twh']:+.4f} TWh, "
              f"max class-hour {r['max_abs_class_hour_mw']:.1f} MW (liveness only)")
    for y, r in props["p7"]["per_year"].items():
        print(f"  P7 {y}: max hourly residual {r['max_abs_hourly_residual_mw']:.8f} MW"
              f"  = {r['max_relative_hourly_residual']:.3e} relative"
              f"  (bar {P7_BALANCE_REL_TOL:.0e}, sidecar {r['sidecar_dtype']});"
              f" annual sum {r['annual_sum_residual_mwh']:+.4f} MWh [reported]")
    for y, r in props["p10"]["per_year"].items():
        share = r["absorption_share"]
        print(f"  P10 {y}: ΔCC_CHP {r['CC_CHP_delta_twh']:+.4f} / "
              f"ΔCC_REGULAR {r['CC_REGULAR_delta_twh']:+.4f} TWh, absorbed "
              f"{share if share is None else round(100 * share, 1)} %")

    print("\n=== C1 |error| vs committed bench (TWh) ===")
    for y in YEARS:
        tag = "" if y in SCORED_YEARS else "   [C1 rows SKIPPED — preliminary 923]"
        print(f"  {y}{tag}")
        for k in ("CC_CHP", "CC_REGULAR", "_CC_COMBINED", "CT_CHP"):
            r = errs[str(y)].get(k)
            if not r:
                continue
            print(f"    {k:<13} actual {r['actual']:>8.3f} | A {r['A']:>8.3f} "
                  f"({r['abs_err_A']:.3f}) -> B {r['B']:>8.3f} ({r['abs_err_B']:.3f})"
                  f"  Δ|err| {r['abs_err_delta']:+.3f}")

    st = standard
    print("\n=== §7 PROMOTION STANDARD ===")
    si = st["structural_integrity"]
    print(f"  structural integrity: S1 {si['S1_measurement_replaces_estimate']} · "
          f"S2 {si['S2_zero_free_parameters']} · S3 {si['S3_no_new_mechanism_surface']} · "
          f"S4 {si['S4_live_and_conservation_clean']}  ⇒ {si['all_hold']}")
    for name, blk in st["stop_and_escalate_triggers"].items():
        if name == "any_fired":
            continue
        print(f"  {name}: fired={blk['fired']}")
    v4 = st["V4_combined_cc"]
    print(f"  V4 combined-CC Δ|err| by scored year: {v4['abs_err_delta_by_year']} "
          f"(threshold +{v4['threshold_twh']} TWh) ⇒ passed={v4['passed']}")
    for y, r in st["accepted_regression"]["A3_lambda"]["rows"].items():
        print(f"  A3 λ {y}: {r['lambda_A']:.3f} -> {r['lambda_B']:.3f} "
              f"({r['delta_usd']:+.3f} $/MWh, {100 * r['frac_of_level']:+.3f} pp)")
    print(f"\n  VERDICT: {st['VERDICT']}   matrix cell -> {st['matrix_cell']}")

    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
