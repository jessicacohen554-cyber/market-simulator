"""neiso-70 A/B scorer — both heat-rate arms against ONE same-HEAD control.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-neiso70-heat-rate-provenance-2026-07-31.md`` from
the three solved bundles. **No solve, and no gate that is not in the prereg.**

Two arms share one control (prereg §1):

* ``neiso70_control_A``      — zero-delta replay of the keeper at HEAD
* ``neiso70_ctheatrate_B``   — ``measured_ct_heat_rates=true`` only
* ``neiso70_chpheatrate_B``  — ``measured_chp_heat_rates=true`` only

Construction gates (prereg §2), scored per arm:

* **G-1 flag fidelity** — the arm records its own flag ``true`` and the control
  records both ``false``. (The pre-solve half — that the flag reaches NEISO's
  fleet at all — was discharged by ``_neiso70_flag_fidelity.py`` before any
  solve; this is the post-solve confirmation from the committed configs.)
* **G-2 control integrity** — the control's ScenarioConfig equals the keeper's
  except for recorded provenance, and both flags read ``False``. **Two bases,
  and they are reported separately.** The *config* basis is the gate. The
  *byte* basis (class-hour for class-hour against the committed keeper) is NOT
  a gate — the keeper's ``git_sha`` ``eede1c4`` is not in the repo, so its
  sidecars cannot reproduce at HEAD, and the divergence is the separately
  reported DRIFT finding (prereg §6, the neiso-69 catch).
* **G-3 mechanism is LIVE** — ``max |Δ class MW| > 50`` on the arm's target
  classes in at least one year. Failing this is verdict ``I``, not ``R``.
* **G-4 single delta** — the arm's ScenarioConfig differs from the control's in
  exactly one field, and that field is the arm's flag.
* **G-5 year span** — every bundle carries exactly ``[2023, 2024, 2025]``
  (rule 16 / rule 22 D-6 quarantine).

Everything else — C1 class TWh, mean λ, C3c tail hours, D-1/D-2 on the repriced
classes — is REPORTED, per prereg §6: a worse backcast on a measured-input swap
is a discovered bug under rules 1 ``[R-STRUCT]`` / 14 ``[R-ACCURATE]``, not a
kill condition.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_neiso70_heatrate_ab.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

CONTROL = Path("results/calibration/neiso70_control_A")
KEEPER = Path("results/calibration/neiso61_netrev_margin")
OUT_PATH = Path("results/probes/neiso70_heatrate_ab.json")

#: Arm -> (bundle, flag, target classes whose dispatch the flag re-prices).
ARMS = {
    "ct": (
        Path("results/calibration/neiso70_ctheatrate_B"),
        "measured_ct_heat_rates",
        ("CT_PEAKER",),
    ),
    "chp": (
        Path("results/calibration/neiso70_chpheatrate_B"),
        "measured_chp_heat_rates",
        ("CC_CHP", "CT_CHP"),
    ),
}

#: PREREG §2 G-3 — the liveness floor, in MW of class dispatch divergence.
G3_LIVENESS_MW = 50.0
#: The two flags, which must BOTH read False in the control.
FLAGS = ("measured_ct_heat_rates", "measured_chp_heat_rates")
#: P1 is the scored pass everywhere (CLAUDE.md "Dispatch & Commitment").
SCORED_PASS = "P1"


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == SCORED_PASS]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """P1 annual TWh by class."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max and per-class class-hour divergence between two bundles, one year."""
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
    """P1 system (zone-hour) frame for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == SCORED_PASS]


def _mean_lambda(bundle: Path, year: int) -> float:
    """Load-weighted mean λ over the physical zones (HQ_import excluded).

    ``HQ_import`` is a seam pseudo-node, not NEISO load, so it is excluded on
    the same principle as the CAISO scorer's WECC nodes.
    """
    frame = _system(bundle, year)
    phys = frame[frame["zone"] != "HQ_import"]
    return round(
        float((phys["price"] * phys["demand"]).sum() / phys["demand"].sum()), 4
    )


def _tail_hours(bundle: Path, year: int, threshold: float = 200.0) -> int:
    """C3c-side diagnostic: system-hours whose load-weighted λ exceeds a level."""
    frame = _system(bundle, year)
    phys = frame[frame["zone"] != "HQ_import"]
    hourly = phys.groupby("hour").apply(
        lambda g: (g["price"] * g["demand"]).sum() / g["demand"].sum(),
        include_groups=False,
    )
    return int((hourly > threshold).sum())


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """Total P1 slack and dump for one bundle-year."""
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


def _scenario_block(bundle: Path) -> dict:
    """The bundle's recorded ScenarioConfig snapshot."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    return cfg.get("scenario_config", {}) or {}


def _flag_value(bundle: Path, flag: str) -> bool | None:
    """The bundle's recorded setting for ``flag``, via either channel.

    ``replay_keeper --set`` routes through the generic ``prb_overrides``
    channel as well as the ScenarioConfig block, so both are checked.
    """
    cfg = json.loads((bundle / "run_config.json").read_text())
    scen = cfg.get("scenario_config", {}) or {}
    if flag in scen:
        return bool(scen[flag])
    ovr = (cfg.get("calibration_flags", {}) or {}).get(
        "coal_prb_sigmoid_overrides"
    ) or {}
    if flag in ovr:
        return bool(ovr[flag])
    return None


def g1_flag_fidelity(arm_bundle: Path, flag: str) -> dict:
    """G-1 — the arm records its flag true; the control records both false."""
    arm_on = _flag_value(arm_bundle, flag)
    ctrl = {f: _flag_value(CONTROL, f) for f in FLAGS}
    return {
        "arm_flag": flag,
        "arm_value": arm_on,
        "control_values": ctrl,
        "passed": bool(arm_on is True and all(v is not True for v in ctrl.values())),
    }


def g2_control_integrity() -> dict:
    """G-2 — the control's config matches the keeper's, both flags off.

    The byte-basis comparison against the committed keeper is computed too, but
    is REPORTED as the drift finding, never scored as a gate (prereg §2/§6).
    """
    ctrl, keep = _scenario_block(CONTROL), _scenario_block(KEEPER)
    all_diff = {
        k: {"control": ctrl.get(k), "keeper": keep.get(k)}
        for k in sorted(set(ctrl) | set(keep))
        if ctrl.get(k) != keep.get(k)
    }
    # A field the keeper's snapshot never carried is a ScenarioConfig field ADDED
    # to the codebase since eede1c4, sitting at its default in the control — code
    # evolution, not a recipe difference. The gate is the RECIPE: fields present
    # in BOTH snapshots that disagree. Counting new-default fields as diffs would
    # fail G-2 on every keeper older than the last config addition.
    new_fields = sorted(k for k, v in all_diff.items() if v["keeper"] is None)
    recipe_diff = {k: v for k, v in all_diff.items() if v["keeper"] is not None}
    flags_off = all(_flag_value(CONTROL, f) is not True for f in FLAGS)
    drift = {}
    for year in YEARS:
        try:
            drift[year] = _pairwise(CONTROL, KEEPER, year)
        except FileNotFoundError:
            drift[year] = None
    return {
        "recipe_diff_vs_keeper": recipe_diff,
        "n_recipe_diff": len(recipe_diff),
        "n_new_fields_since_keeper": len(new_fields),
        "new_fields_since_keeper": new_fields,
        "control_flags_off": flags_off,
        "passed": bool(not recipe_diff and flags_off),
        "REPORTED_byte_drift_vs_committed_keeper": drift,
    }


def g3_liveness(arm_bundle: Path, classes: tuple[str, ...]) -> dict:
    """G-3 — the arm moves its target classes by > 50 MW in some class-hour."""
    per_year = {}
    for year in YEARS:
        pw = _pairwise(CONTROL, arm_bundle, year)
        per_year[year] = {c: pw["max_by_class_mw"].get(c, 0.0) for c in classes} | {
            "max_any_class_mw": pw["max_abs_diff_mw"]
        }
    best = max(
        (v[c] for v in per_year.values() for c in classes),
        default=0.0,
    )
    return {
        "target_classes": list(classes),
        "per_year": per_year,
        "max_target_class_mw": round(float(best), 4),
        "threshold_mw": G3_LIVENESS_MW,
        "passed": bool(best > G3_LIVENESS_MW),
        "verdict_if_failed": "I (inert) — never R",
    }


def g4_single_delta(arm_bundle: Path, flag: str) -> dict:
    """G-4 — the arm differs from the control in exactly its own flag."""
    a, b = _scenario_block(CONTROL), _scenario_block(arm_bundle)
    diff = {
        k: {"control": a.get(k), "arm": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "passed": list(diff) == [flag],
    }


def g5_year_span(bundles: dict[str, Path]) -> dict:
    """G-5 — every bundle spans exactly 2023, 2024, 2025."""
    spans = {}
    for name, bundle in bundles.items():
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    return {
        "years": spans,
        "passed": all(v == list(YEARS) for v in spans.values()),
    }


def reported(arm_bundle: Path) -> dict:
    """Everything the prereg REPORTS rather than gates."""
    out: dict = {}
    for year in YEARS:
        a_twh, b_twh = _class_twh(CONTROL, year), _class_twh(arm_bundle, year)
        classes = sorted(set(a_twh) | set(b_twh))
        a_slack, a_dump = _slack_dump(CONTROL, year)
        b_slack, b_dump = _slack_dump(arm_bundle, year)
        out[year] = {
            "class_twh": {
                c: {
                    "control": a_twh.get(c, 0.0),
                    "arm": b_twh.get(c, 0.0),
                    "delta": round(b_twh.get(c, 0.0) - a_twh.get(c, 0.0), 4),
                }
                for c in classes
            },
            "total_twh": {
                "control": round(sum(a_twh.values()), 4),
                "arm": round(sum(b_twh.values()), 4),
                "delta": round(sum(b_twh.values()) - sum(a_twh.values()), 4),
            },
            "mean_lambda": {
                "control": _mean_lambda(CONTROL, year),
                "arm": _mean_lambda(arm_bundle, year),
                "delta": round(
                    _mean_lambda(arm_bundle, year) - _mean_lambda(CONTROL, year), 4
                ),
            },
            "tail_hours_gt_200": {
                "control": _tail_hours(CONTROL, year),
                "arm": _tail_hours(arm_bundle, year),
            },
            "slack_dump": {
                "control": {"slack": a_slack, "dump": a_dump},
                "arm": {"slack": b_slack, "dump": b_dump},
            },
        }
    return out


def score_arm(name: str, bundle: Path, flag: str, classes: tuple[str, ...]) -> dict:
    """Score one arm against the shared control on the pre-registered gates."""
    gates = {
        "G1_flag_fidelity": g1_flag_fidelity(bundle, flag),
        "G3_liveness": g3_liveness(bundle, classes),
        "G4_single_delta": g4_single_delta(bundle, flag),
    }
    return {
        "arm": name,
        "bundle": str(bundle),
        "flag": flag,
        "gates": gates,
        "gates_passed": {k: v["passed"] for k, v in gates.items()},
        "reported": reported(bundle),
    }


def main() -> int:
    """Score both arms and emit the machine record."""
    bundles = {"control": CONTROL} | {k: v[0] for k, v in ARMS.items()}
    missing = [str(b) for b in bundles.values() if not (b / "meta.json").exists()]
    if missing:
        print("MISSING BUNDLES:", missing)
        return 1

    result = {
        "session": "neiso-70",
        "prereg": "results/calibration/PREREG-neiso70-heat-rate-provenance-2026-07-31.md",
        "control": str(CONTROL),
        "keeper": str(KEEPER),
        "G2_control_integrity": g2_control_integrity(),
        "G5_year_span": g5_year_span(bundles),
        "arms": {
            name: score_arm(name, bundle, flag, classes)
            for name, (bundle, flag, classes) in ARMS.items()
        },
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=1, default=str))

    # ---- readable summary -------------------------------------------------
    print("=" * 78)
    print("neiso-70 — PRE-REGISTERED GATES (arms scored vs the same-HEAD control)")
    print("=" * 78)
    g2, g5 = result["G2_control_integrity"], result["G5_year_span"]
    print(
        f"G-2 control integrity : {'PASS' if g2['passed'] else 'FAIL'}  "
        f"({g2['n_recipe_diff']} RECIPE diffs vs keeper, "
        f"{g2['n_new_fields_since_keeper']} fields added since the keeper solved, "
        f"flags_off={g2['control_flags_off']})"
    )
    print(
        f"G-5 year span         : {'PASS' if g5['passed'] else 'FAIL'}  {g5['years']}"
    )
    for name, arm in result["arms"].items():
        print(f"\n--- arm '{name}' ({arm['flag']}) ---")
        for gate, ok in arm["gates_passed"].items():
            print(f"  {gate:<20} {'PASS' if ok else 'FAIL'}")
        live = arm["gates"]["G3_liveness"]
        print(
            f"  max |Δ| on {live['target_classes']}: "
            f"{live['max_target_class_mw']:,.1f} MW (floor {live['threshold_mw']})"
        )
        if not live["passed"]:
            print(f"  >>> {live['verdict_if_failed']}")

    print("\n" + "=" * 78)
    print("REPORTED (never a kill — rules 1 / 14)")
    print("=" * 78)
    print("\nControl vs COMMITTED KEEPER drift (evidence, not a gate):")
    for year, d in g2["REPORTED_byte_drift_vs_committed_keeper"].items():
        if d is None:
            print(f"  {year}: keeper sidecars unavailable")
            continue
        top = sorted(d["max_by_class_mw"].items(), key=lambda kv: -kv[1])[:5]
        print(f"  {year}: max |Δ| {d['max_abs_diff_mw']:,.1f} MW; top classes {top}")

    for name, arm in result["arms"].items():
        print(f"\n--- arm '{name}' class TWh (arm − control) ---")
        for year in YEARS:
            rep = arm["reported"][year]
            moved = {
                c: v["delta"]
                for c, v in rep["class_twh"].items()
                if abs(v["delta"]) >= 0.0005
            }
            print(
                f"  {year}: total {rep['total_twh']['delta']:+.4f} TWh, "
                f"mean λ {rep['mean_lambda']['delta']:+.4f} $/MWh, "
                f"tail>200 {rep['tail_hours_gt_200']['control']}"
                f"->{rep['tail_hours_gt_200']['arm']} h"
            )
            for c, dv in sorted(moved.items(), key=lambda kv: -abs(kv[1])):
                print(
                    f"      {c:<12} {rep['class_twh'][c]['control']:>8.4f} -> "
                    f"{rep['class_twh'][c]['arm']:>8.4f}  ({dv:+.4f})"
                )
    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
