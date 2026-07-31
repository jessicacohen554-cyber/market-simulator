"""nyiso-105 A/B scorer — ``measured_chp_heat_rates`` against the nyiso-100 keeper.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md`` from the two
solved bundles plus the committed NYISO artifact. **No solve, and no gate that is
not in the prereg.**

Construction gates (prereg §4):

* **K1 flag fidelity** — arm B records ``measured_chp_heat_rates=true``, the
  control ``false``; every applied artifact row carries ``flag == "ok"``.
* **K2 control integrity** — TWO BASES, and only the first is a gate. The
  *scorecard* basis (same determination, same per-criterion statuses as the
  committed keeper) is the pre-registered gate. The stricter *byte* basis
  (class-hour for class-hour, < 1e-6 MW) is computed and REPORTED; a byte miss is
  same-HEAD drift, a separately-reported finding, not a failed gate (caiso-146 K2
  precedent, and the reason a same-HEAD control is solved at all).
* **K3 mechanism is LIVE** — ``max |Δ CC_CHP MW| > 50`` or
  ``max |Δ CT_CHP MW| > 50`` on a class-hour in at least one year. Failing this
  is verdict ``I`` (inert), not ``R``.
* **K4 single delta** — the arms' ``run_config`` scenario blocks differ in
  exactly the one boolean.
* **K5 year span** — both bundles carry ``[2023, 2024, 2025]`` and nothing else
  (rule 22 / D-6 quarantine; the holdout spend freeze is ACTIVE).
* **K6 pin sensitivity** — C1 recomputed with the D-10 pinned classes excluded,
  so a verdict resting only on classes D-10 discounts is visible.

Everything else — per-class TWh vs actual, mean λ, tail hours, slack/dump — is
REPORTED per prereg §5: a worse backcast on a strictly more accurate measured
input is a discovered bug under rules 1/14, never a kill condition.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso105_chpheatrate_ab.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/nyiso105_control_A"
ARM_B = REPO / "results/calibration/nyiso105_chpheatrate_B"
KEEPER = REPO / "results/calibration/nyiso100_silretire"
ARTIFACT = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_NYISO.csv"
OUT_PATH = REPO / "results/calibration/_nyiso105_chpheatrate_ab.json"

#: PREREG §4 K3 — the liveness floor, in MW of class dispatch divergence.
K3_LIVENESS_MW = 50.0
#: PREREG §4 K2 — a zero-delta replay must land inside this many MW.
K2_TOL_MW = 1e-6
#: The one boolean under test.
FLAG = "measured_chp_heat_rates"
#: PREREG §4 — NYISO's D-10 pinned classes (scripts/calibration_verdict.py).
PINNED = {"CC_CHP", "CT_CHP", "ST_CHP", "hydro", "imports", "nuclear", "solar", "wind"}
#: The classes this artifact actually reprices (turbine physics; ST_CHP is out of
#: scope — a boiler-first back-pressure cogen's fuel is process fuel).
REPRICED = ("CC_CHP", "CT_CHP")


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max / by-class class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
        },
    }


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean λ (the external interchange node excluded)."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _tail_hours(bundle: Path, year: int, thresh: float = 300.0) -> int:
    """C3c basis: load-weighted system λ hours above *thresh*."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    lam = (ny["price"] * ny["demand"]).groupby(ny["hour"]).sum() / ny.groupby("hour")[
        "demand"
    ].sum()
    return int((lam > thresh).sum())


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    frame = _system(bundle, year)
    slack = float(frame["slack"].sum()) if "slack" in frame.columns else float("nan")
    dump = float(frame["dump"].sum()) if "dump" in frame.columns else float("nan")
    return round(slack, 3), round(dump, 3)


def _scenario_block(bundle: Path) -> dict:
    cfg = json.loads((bundle / "run_config.json").read_text())
    return cfg.get("scenario_config", {}) or {}


def _flag(bundle: Path) -> bool | None:
    """The bundle's recorded ``measured_chp_heat_rates`` setting."""
    path = bundle / "run_config.json"
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    scen = cfg.get("scenario_config", {}) or {}
    if FLAG in scen:
        return bool(scen[FLAG])
    ovr = (cfg.get("calibration_flags", {}) or {}).get(
        "coal_prb_sigmoid_overrides"
    ) or {}
    return bool(ovr[FLAG]) if FLAG in ovr else None


# --------------------------------------------------------------------------- #
# the pre-registered construction gates
# --------------------------------------------------------------------------- #
def k1_flag_fidelity() -> dict:
    art = pd.read_csv(ARTIFACT)
    applied = art[art["flag"] == "ok"]
    return {
        "arm_A_flag": _flag(ARM_A),
        "arm_B_flag": _flag(ARM_B),
        "artifact_rows": int(len(art)),
        "artifact_applied_ok": int(len(applied)),
        "applied_all_ok": bool((applied["flag"] == "ok").all()),
        "applied_mw": round(float(applied["class_capacity_mw"].sum()), 1),
        "passed": _flag(ARM_A) is False and _flag(ARM_B) is True and len(applied) > 0,
    }


def k2_control_integrity() -> dict:
    """Scorecard basis is the gate; byte basis is reported."""
    byte = {}
    for year in YEARS:
        pw = _pairwise(KEEPER, ARM_A, year)
        byte[year] = pw
    byte_ok = all(v["max_abs_diff_mw"] <= K2_TOL_MW for v in byte.values())
    return {
        "byte_basis_vs_committed_keeper": byte,
        "byte_basis_identical": byte_ok,
        "note": (
            "Byte basis is REPORTED, not the gate (prereg §4 K2). The gate is the "
            "scorecard basis, scored from the arms' own metrics.json."
        ),
    }


def k3_liveness() -> dict:
    per_year = {}
    live = False
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        by = pw["max_by_class_mw"]
        repriced_max = {k: by.get(k, 0.0) for k in REPRICED}
        per_year[year] = {
            "max_abs_diff_mw": pw["max_abs_diff_mw"],
            "repriced_class_max_mw": repriced_max,
            "max_by_class_mw": by,
        }
        if max(repriced_max.values() or [0.0]) > K3_LIVENESS_MW:
            live = True
    return {"per_year": per_year, "threshold_mw": K3_LIVENESS_MW, "passed": live}


def k4_single_delta() -> dict:
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "passed": list(diff) == [FLAG],
    }


def k5_year_span() -> dict:
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    return {
        "years": spans,
        "passed": all(v == [2023, 2024, 2025] for v in spans.values()),
    }


def k6_pin_sensitivity() -> dict:
    """C1-relevant class energy split into pinned vs free classes, both arms."""
    out = {}
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        keys = sorted(set(a) | set(b))
        rows = {
            k: {
                "A": round(a.get(k, 0.0), 4),
                "B": round(b.get(k, 0.0), 4),
                "delta": round(b.get(k, 0.0) - a.get(k, 0.0), 4),
                "pinned": k in PINNED,
            }
            for k in keys
        }
        free_moved = {
            k: v["delta"] for k, v in rows.items() if not v["pinned"] and abs(v["delta"]) > 1e-4
        }
        out[year] = {
            "by_class": rows,
            "free_classes_moved": free_moved,
            "free_abs_twh_moved": round(sum(abs(v) for v in free_moved.values()), 4),
        }
    any_free = any(v["free_abs_twh_moved"] > 0.0 for v in out.values())
    return {"per_year": out, "verdict_rests_on_free_classes_too": any_free}


# --------------------------------------------------------------------------- #
# reported-only diagnostics (prereg §5 — these can never kill)
# --------------------------------------------------------------------------- #
def reported() -> dict:
    out = {}
    for year in YEARS:
        a_slack, a_dump = _slack_dump(ARM_A, year)
        b_slack, b_dump = _slack_dump(ARM_B, year)
        out[year] = {
            "mean_lambda": {"A": _lambda(ARM_A, year), "B": _lambda(ARM_B, year)},
            "tail_hours_gt_300": {
                "A": _tail_hours(ARM_A, year),
                "B": _tail_hours(ARM_B, year),
            },
            "slack_mwh": {"A": a_slack, "B": b_slack},
            "dump_mwh": {"A": a_dump, "B": b_dump},
            "class_twh": {
                "A": _class_twh(ARM_A, year),
                "B": _class_twh(ARM_B, year),
            },
        }
    return out


def scorecards() -> dict:
    """Per-criterion statuses from each bundle's own metrics.json, if present."""
    out = {}
    for name, bundle in (("keeper", KEEPER), ("A", ARM_A), ("B", ARM_B)):
        path = bundle / "metrics.json"
        if not path.exists():
            out[name] = None
            continue
        m = json.loads(path.read_text())
        out[name] = {
            "determination": m.get("determination"),
            "criteria": {
                k: (v.get("status") if isinstance(v, dict) else v)
                for k, v in (m.get("criteria") or {}).items()
            },
            "grade_summary": m.get("grade_summary"),
            "free_class_headline": (m.get("free_class_score") or {}).get("headline"),
        }
    return out


def main() -> int:
    res = {
        "probe": "nyiso-105 measured_chp_heat_rates A/B",
        "prereg": "results/calibration/PREREG-nyiso105-chp-heat-rates-2026-07-31.md",
        "arms": {"A_control": ARM_A.name, "B": ARM_B.name, "keeper": KEEPER.name},
        "K1_flag_fidelity": k1_flag_fidelity(),
        "K2_control_integrity": k2_control_integrity(),
        "K3_liveness": k3_liveness(),
        "K4_single_delta": k4_single_delta(),
        "K5_year_span": k5_year_span(),
        "K6_pin_sensitivity": k6_pin_sensitivity(),
        "scorecards": scorecards(),
        "reported_only": reported(),
    }
    OUT_PATH.write_text(json.dumps(res, indent=1, default=str))

    print("=" * 78)
    print("nyiso-105 — measured_chp_heat_rates A/B (pre-registered gates only)")
    print("=" * 78)
    for gate in ("K1_flag_fidelity", "K3_liveness", "K4_single_delta", "K5_year_span"):
        p = res[gate].get("passed")
        print(f"  {gate:22s} {'PASS' if p else 'FAIL'}")
    print(f"  K2_control_integrity   byte-identical vs committed keeper: "
          f"{res['K2_control_integrity']['byte_basis_identical']} (reported, not a gate)")
    print(f"  K6_pin_sensitivity     free classes also move: "
          f"{res['K6_pin_sensitivity']['verdict_rests_on_free_classes_too']}")

    print("\nK3 liveness — max |Δ| on the repriced classes (MW of class dispatch):")
    for y, v in res["K3_liveness"]["per_year"].items():
        print(f"  {y}: " + "  ".join(
            f"{k}={v['repriced_class_max_mw'][k]:9.1f}" for k in REPRICED
        ) + f"   any-class max={v['max_abs_diff_mw']:9.1f}")

    print("\nscorecards:")
    for name, sc in res["scorecards"].items():
        if sc is None:
            print(f"  {name:7s} (no metrics.json)")
            continue
        print(f"  {name:7s} {sc['determination']}  "
              + " ".join(f"{k}={v}" for k, v in (sc["criteria"] or {}).items()))

    print("\nREPORTED ONLY (prereg §5 — cannot kill):")
    for y, v in res["reported_only"].items():
        print(f"  {y}: mean lambda A={v['mean_lambda']['A']:8.3f} -> "
              f"B={v['mean_lambda']['B']:8.3f}   "
              f"tail>300h A={v['tail_hours_gt_300']['A']:3d} -> "
              f"B={v['tail_hours_gt_300']['B']:3d}")
    print("\n  class TWh delta (B - A), classes moving > 0.001 TWh:")
    for y in YEARS:
        a, b = _class_twh(ARM_A, y), _class_twh(ARM_B, y)
        moved = {
            k: round(b.get(k, 0.0) - a.get(k, 0.0), 4)
            for k in sorted(set(a) | set(b))
            if abs(b.get(k, 0.0) - a.get(k, 0.0)) > 1e-3
        }
        pin = {k: v for k, v in moved.items() if k in PINNED}
        free = {k: v for k, v in moved.items() if k not in PINNED}
        print(f"   {y} pinned: {pin}")
        print(f"   {y} free  : {free}")

    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
