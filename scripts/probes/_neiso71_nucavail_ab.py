"""neiso-71 A/B scorer — `nuclear_unit_availability` against a same-HEAD control.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-neiso71-nuclear-availability-2026-07-31.md`` from
the two solved bundles. **No solve, and no gate that is not in the prereg.**

* ``neiso71_control_A``  — zero-delta replay of the neiso-70 keeper meta at HEAD
* ``neiso71_nucavail_B`` — the same meta with ``nuclear_unit_availability=True``

Construction gates (prereg §2):

* **G-1 flag fidelity** — the arm records the flag ``true``, the control
  ``false``. (The pre-solve half — that the overlay reaches NEISO's *dispatch*
  fleet — was discharged by ``_neiso71_lever_screen.py`` before any solve and
  re-confirmed in the arm's own log: ``3 reactor(s) on measured daily
  windows``. NOTE the duplicate log line: ``bins_to_fleet`` builds its own
  FleetArrays from the thermal-tranche list alone and logs ``0 reactor(s)``
  first; the runner's dispatch-fleet build logs the real ``3``. Read the LAST
  occurrence.)
* **G-2 control integrity** — the control's ScenarioConfig equals the keeper's
  on every field present in both snapshots, and the flag reads ``False``.
  Byte-basis drift vs the committed keeper is REPORTED, never gated.
* **G-3 LIVENESS** — ``max |Δ class MW| > 50`` in ≥1 year. Failing ⇒ ``I``, not ``R``.
* **G-4 single delta** — exactly one ScenarioConfig field differs, and it is the flag.
* **G-5 year span** — both bundles carry exactly ``[2023, 2024, 2025]``.

Prediction P1 (prereg §3) is checked as a KILL condition: fleet nuclear energy
must move ≤ 0.05 TWh/yr, since the EIA-923 monthly anchor is preserved by
construction. A larger move means the reconciliation leaked.

Everything else — class TWh, mean λ, C3c tail hours, zonal splits — is
REPORTED (prereg §4): a worse backcast on a measured-input swap is a discovered
bug under rules 1 ``[R-STRUCT]`` / 14 ``[R-ACCURATE]``, not a kill condition.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_neiso71_nucavail_ab.py
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

CONTROL = Path("results/calibration/neiso71_control_A")
ARM = Path("results/calibration/neiso71_nucavail_B")
KEEPER = Path("results/calibration/neiso70_ctheatrate_B")
OUT_PATH = Path("results/probes/neiso71_nucavail_ab.json")

FLAG = "nuclear_unit_availability"
#: PREREG §2 G-3 — liveness floor, MW of class dispatch divergence.
G3_LIVENESS_MW = 50.0
#: PREREG §3 P1 — max admissible nuclear energy move, TWh/yr.
P1_ENERGY_TOL_TWH = 0.05
#: P1 is the scored pass everywhere (CLAUDE.md "Dispatch & Commitment").
SCORED_PASS = "P1"
#: Seam pseudo-node, not NEISO load — excluded from load-weighted λ.
SEAM_ZONE = "HQ_import"


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == SCORED_PASS]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


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
        },
    }


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == SCORED_PASS]


def _mean_lambda(bundle: Path, year: int) -> float:
    phys = _system(bundle, year)
    phys = phys[phys["zone"] != SEAM_ZONE]
    return round(float((phys["price"] * phys["demand"]).sum() / phys["demand"].sum()), 4)


def _zone_mean_lambda(bundle: Path, year: int) -> dict[str, float]:
    """Per-zone load-weighted λ — the arm's Connecticut/North split is the story."""
    phys = _system(bundle, year)
    phys = phys[phys["zone"] != SEAM_ZONE]
    out = {}
    for zone, grp in phys.groupby("zone"):
        d = grp["demand"].sum()
        out[str(zone)] = round(float((grp["price"] * grp["demand"]).sum() / d), 4) if d else 0.0
    return out


def _tail_hours(bundle: Path, year: int, threshold: float = 200.0) -> int:
    phys = _system(bundle, year)
    phys = phys[phys["zone"] != SEAM_ZONE]
    hourly = phys.groupby("hour").apply(
        lambda g: (g["price"] * g["demand"]).sum() / g["demand"].sum(),
        include_groups=False,
    )
    return int((hourly > threshold).sum())


def _scenario_block(bundle: Path) -> dict:
    cfg = json.loads((bundle / "run_config.json").read_text())
    return cfg.get("scenario_config", {}) or {}


def g1_flag_fidelity() -> dict:
    arm = _scenario_block(ARM).get(FLAG)
    ctrl = _scenario_block(CONTROL).get(FLAG)
    return {
        "flag": FLAG,
        "arm_value": arm,
        "control_value": ctrl,
        "passed": bool(arm is True and ctrl is not True),
    }


def g2_control_integrity() -> dict:
    ctrl, keep = _scenario_block(CONTROL), _scenario_block(KEEPER)
    all_diff = {
        k: {"control": ctrl.get(k), "keeper": keep.get(k)}
        for k in sorted(set(ctrl) | set(keep))
        if ctrl.get(k) != keep.get(k)
    }
    # A field absent from the keeper's snapshot is a ScenarioConfig field ADDED
    # since it solved, sitting at its default in the control — code evolution,
    # not a recipe difference. The gate is the RECIPE.
    new_fields = sorted(k for k, v in all_diff.items() if v["keeper"] is None)
    recipe_diff = {k: v for k, v in all_diff.items() if v["keeper"] is not None}
    return {
        "recipe_diff": recipe_diff,
        "new_default_fields": new_fields,
        "control_flag_off": ctrl.get(FLAG) is not True,
        "passed": bool(not recipe_diff and ctrl.get(FLAG) is not True),
    }


def g3_liveness() -> dict:
    per_year = {y: _pairwise(CONTROL, ARM, y) for y in YEARS}
    best = max(v["max_abs_diff_mw"] for v in per_year.values())
    return {
        "per_year": per_year,
        "max_abs_diff_mw": best,
        "threshold_mw": G3_LIVENESS_MW,
        "passed": bool(best > G3_LIVENESS_MW),
    }


def g4_single_delta() -> dict:
    ctrl, arm = _scenario_block(CONTROL), _scenario_block(ARM)
    diff = sorted(k for k in set(ctrl) | set(arm) if ctrl.get(k) != arm.get(k))
    return {
        "diff_fields": diff,
        "passed": bool(diff == [FLAG]),
    }


def g5_year_span() -> dict:
    spans = {}
    for name, bundle in (("control", CONTROL), ("arm", ARM)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    return {
        "spans": spans,
        "passed": all(v == list(YEARS) for v in spans.values()),
    }


def p1_energy_neutral(reported: dict) -> dict:
    """PREREG §3 P1 — nuclear energy must be anchor-preserved (KILL if not)."""
    rows = {}
    for y in YEARS:
        # The class key is the fleet's lowercase fuel label ("nuclear"). Look it
        # up case-insensitively and FAIL LOUDLY if it is absent — a missing key
        # would otherwise let this KILL gate pass vacuously on 0.0 == 0.0.
        def _nuc(side: str) -> float:
            twh = reported["class_twh"][side][y]
            hits = [v for k, v in twh.items() if str(k).lower() == "nuclear"]
            if not hits:
                raise KeyError(
                    f"no nuclear class row in {side} {y}: keys={sorted(twh)}"
                )
            return float(sum(hits))

        c, a = _nuc("control"), _nuc("arm")
        rows[y] = {"control": round(c, 4), "arm": round(a, 4), "delta_twh": round(a - c, 4)}
    worst = max(abs(v["delta_twh"]) for v in rows.values())
    return {
        "per_year": rows,
        "max_abs_delta_twh": worst,
        "tolerance_twh": P1_ENERGY_TOL_TWH,
        "passed": bool(worst <= P1_ENERGY_TOL_TWH),
    }


def main() -> int:
    reported = {
        "class_twh": {
            "control": {y: _class_twh(CONTROL, y) for y in YEARS},
            "arm": {y: _class_twh(ARM, y) for y in YEARS},
        },
        "mean_lambda": {
            "control": {y: _mean_lambda(CONTROL, y) for y in YEARS},
            "arm": {y: _mean_lambda(ARM, y) for y in YEARS},
        },
        "zone_mean_lambda": {
            "control": {y: _zone_mean_lambda(CONTROL, y) for y in YEARS},
            "arm": {y: _zone_mean_lambda(ARM, y) for y in YEARS},
        },
        "tail_hours_gt200": {
            "control": {y: _tail_hours(CONTROL, y) for y in YEARS},
            "arm": {y: _tail_hours(ARM, y) for y in YEARS},
        },
    }
    gates = {
        "G1_flag_fidelity": g1_flag_fidelity(),
        "G2_control_integrity": g2_control_integrity(),
        "G3_liveness": g3_liveness(),
        "G4_single_delta": g4_single_delta(),
        "G5_year_span": g5_year_span(),
        "P1_energy_neutral": p1_energy_neutral(reported),
    }
    out = {"gates": gates, "reported": reported}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))

    print("=" * 74)
    print("neiso-71 A/B — nuclear_unit_availability vs same-HEAD control")
    print("=" * 74)
    for name, g in gates.items():
        print(f"  {'PASS' if g['passed'] else 'FAIL'}  {name}")
    print()
    for y in YEARS:
        c = reported["mean_lambda"]["control"][y]
        a = reported["mean_lambda"]["arm"][y]
        print(
            f"  {y}: mean λ {c:8.3f} -> {a:8.3f} ({a - c:+.3f})   "
            f"tail>200 {reported['tail_hours_gt200']['control'][y]:4d} -> "
            f"{reported['tail_hours_gt200']['arm'][y]:4d}"
        )
    print(f"\n  wrote {OUT_PATH}")
    return 0 if all(g["passed"] for g in gates.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
