"""Score the pjm-152 PREREG gates on the collapse arm (K1/K2/K5/E1). No LP.

The pjm-152 collapse is a rule 26 ``[R-DELETE]`` debt discharge, not a
mechanism: the per-neighbour PJM seam-envelope construction becomes
unconditional and ``pjm_seam_envelope_by_neighbor`` (plus the zone-summed
branch, the ``by_neighbor`` parameter, the three config registrations and the
``run_calibration.py`` plumbing) is deleted. So there is exactly ONE substantive
gate and it is absolute:

    **E1 — max |dMW| = 0.000000 on every P1 class-hour of all three years**,
    against ``results/calibration/pjm151_seam_B``. Anything else means the
    collapse changed behaviour and is a stop-the-line event.

Reads only committed/solved artifacts — no re-solve, no floor rebuild.

Usage:
    PYTHONPATH=.:src python <this> --arm results/calibration/pjm152_collapse_A
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path[:0] = [str(REPO), str(REPO / "src")]

KEEPER = REPO / "results/calibration/pjm151_seam_B"
YEARS = (2023, 2024, 2025)
_MISSING = object()

#: The field the collapse retires. It is expected to appear as ``keeper_only``
#: in the recipe diff — the keeper recorded it, HEAD has no such field.
RETIRED_FIELD = "pjm_seam_envelope_by_neighbor"

#: Fields present on only ONE side because the SCHEMA moved, not the recipe.
#: ``config_drift`` is absence-aware for exactly this reason (caiso-160 §4).
#: Each is enumerated with the commit that moved it and why it cannot reach a
#: PJM calibration backcast. Carried forward from pjm-151's list
#: (``scripts/probes/pjm151_seam_gates.py``) and re-based on the pjm-151 keeper,
#: which POST-dates the seven pjm-151-era entries — so only the new ones remain.
SCHEMA_DRIFT = {
    RETIRED_FIELD: (
        "THE DECLARED DELTA (PREREG-pjm152 §4), and the ONLY intended one. "
        "Deleted from ScenarioConfig by this session under rule 26 [R-DELETE], "
        "so it lands in keeper_only: the pjm-151 keeper recorded it True and "
        "HEAD has no such field because the path it gated is now the only path."
    ),
    "exit_rate_limits": (
        "db5ff912 (FFR-3F, owner decision D-8) added the measured "
        "exit-throughput cap, default off. Read ONLY in runner.py's capacity-"
        "evolution path, which the calibration harness never enters — "
        "solve_and_persist loops years through run_calibration.run_year, a "
        "standalone per-year solve (pjm-150 §4)."
    ),
    # Added at the 2026-08-04 rebase onto a0bf3db3, after this PREREG was
    # pushed. Both are default-off and BOTH ARE ISO-GATED IN CODE, not merely
    # by convention — the enumeration is by inspection of the guard, per K2.
    "ercot_energy_online_capability_cap": (
        "935c33dd (ercot-159) added the energy-side online-capability cap, "
        "default off. Its sole read sits inside "
        "`if getattr(config, 'ercot_energy_online_capability_cap', False)` in "
        "model/reserves/spec.py, on the ERCOT fast-tier row of the "
        "online_capacity_cap block; None/off leaves the LP unchanged."
    ),
    "ercot_energy_online_capability_cap_path": (
        "935c33dd, the artifact path for the field above. Read only when that "
        "flag is armed."
    ),
    "caiso_zonal_loss_surface": (
        "eda8ebe8 (caiso-164) added the CAISO internal-link loss-pair split, "
        "default off and guarded by "
        "`if getattr(config, 'caiso_zonal_loss_surface', False) and "
        "iso == 'CAISO'` — unreachable for iso='PJM' twice over. The runner "
        "site adds a conditional that reduces to the pre-existing UNSET when "
        "off, so PJM is byte-identical."
    ),
}

#: Shipped ``ScenarioConfig`` defaults that MOVED on main after the PJM keeper
#: solved (basis ``1c191624``). The pjm-151 keeper post-dates every entry on
#: pjm-150's list, so this set starts EMPTY and is populated only by a measured
#: value_diff. The reason such a move cannot reach a PJM backcast is NOT that
#: the evolution loop is mode-gated but that THE CALIBRATION HARNESS NEVER
#: CALLS IT (pjm-150 §4).
DEFAULT_MOVES: set[str] = set()

#: PREREG-pjm152 E1. A behaviour-preserving collapse admits exactly zero.
E1_MAX_DMW = 0.0


def scenario_cfg(bundle: Path) -> dict:
    """Return a bundle's recorded ScenarioConfig."""
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def gate_k1(arm: Path) -> dict:
    """K1 -- zero recipe changes beyond the declared field deletion."""
    a, k = scenario_cfg(arm), scenario_cfg(KEEPER)
    changed = [
        key
        for key in sorted(set(a) | set(k))
        if a.get(key, _MISSING) != k.get(key, _MISSING)
    ]
    value_diffs = [c for c in changed if c in a and c in k]
    arm_only = [c for c in changed if c not in k]
    keeper_only = [c for c in changed if c not in a]
    retired_ok = RETIRED_FIELD in keeper_only and k.get(RETIRED_FIELD) is True
    unexplained = [c for c in value_diffs if c not in DEFAULT_MOVES] + [
        c for c in (*arm_only, *keeper_only) if c not in SCHEMA_DRIFT
    ]
    return {
        "arm_only": arm_only,
        "keeper_only": keeper_only,
        "value_diffs": value_diffs,
        "detail": {c: {"keeper": k.get(c), "arm": a.get(c)} for c in value_diffs},
        "retired_field_channel": (
            "keeper_only (the keeper recorded it True; HEAD has no such field)"
            if retired_ok
            else "UNEXPECTED"
        ),
        "schema_drift_explained": {
            c: SCHEMA_DRIFT[c] for c in (*arm_only, *keeper_only) if c in SCHEMA_DRIFT
        },
        "default_moves_explained": [c for c in value_diffs if c in DEFAULT_MOVES],
        "unexplained": unexplained,
        "verdict": "PASS" if retired_ok and not unexplained else "FAIL",
    }


def gate_k2(arm: Path) -> dict:
    """K2 -- control integrity: same solver/numerics stack, recorded basis."""
    am = json.loads((arm / "meta.json").read_text())
    km = json.loads((KEEPER / "meta.json").read_text())
    ae, ke = am.get("environment") or {}, km.get("environment") or {}
    drift = {
        f: {"keeper": ke.get(f), "arm": ae.get(f)}
        for f in ("python_version", "platform")
        if ke.get(f) != ae.get(f)
    }
    kp, ap_ = ke.get("packages") or {}, ae.get("packages") or {}
    drift.update(
        {
            p: {"keeper": kp.get(p), "arm": ap_.get(p)}
            for p in sorted(set(kp) | set(ap_))
            if kp.get(p) != ap_.get(p)
        }
    )
    return {
        "keeper_basis_sha": km.get("basis_sha"),
        "arm_basis_sha": am.get("basis_sha"),
        "environment_drift": drift,
        "verdict": "PASS" if not drift else "FAIL",
    }


def gate_k5(arm: Path) -> dict:
    """K5 -- span: 2023+2024+2025 in ONE bundle, no holdout year touched."""
    am = json.loads((arm / "meta.json").read_text())
    yrs = [int(y) for y in am.get("years", [])]
    return {
        "years": yrs,
        "holdout_touched": sorted(y for y in yrs if y not in YEARS),
        "verdict": "PASS" if sorted(yrs) == list(YEARS) else "FAIL",
    }


def _class_hour(bundle: Path, year: int) -> pd.DataFrame | None:
    """P1 class-hour dispatch, sorted to a canonical key order.

    The sidecar is LONG-form (``year, pass, klass, hour, mw``) and carries both
    passes, so it MUST be filtered to ``P1`` (the scored pass) and sorted before
    a positional diff — reading it wide or unsorted silently produces a vacuous
    comparison (the pjm-151 scorer's recorded first-attempt defect).
    """
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    df = df[df["pass"].astype(str) == "P1"].copy()
    df["klass"] = df["klass"].astype(str)
    return df.sort_values(["klass", "hour"]).reset_index(drop=True)


def gate_e1(arm: Path) -> dict:
    """E1 -- THE gate. Max |dMW| on every P1 class-hour must be exactly 0."""
    out: dict[str, object] = {"years": {}, "breaches": []}
    for year in YEARS:
        a, k = _class_hour(arm, year), _class_hour(KEEPER, year)
        if a is None or k is None:
            out["breaches"].append({"year": year, "why": "missing class_hourly"})
            out["years"][str(year)] = {"status": "missing sidecar"}
            continue
        rec: dict[str, object] = {"n_rows_arm": len(a), "n_rows_keeper": len(k)}
        if len(a) != len(k) or not a["klass"].equals(k["klass"]):
            rec["status"] = "KEY MISMATCH"
            out["breaches"].append({"year": year, "why": "class/hour key mismatch"})
            out["years"][str(year)] = rec
            continue
        d = a["mw"].to_numpy(dtype=float) - k["mw"].to_numpy(dtype=float)
        mx = float(np.nanmax(np.abs(d)))
        rec["max_abs_class_hour_dMW"] = round(mx, 6)
        rec["n_class_hours"] = int(d.size)
        rec["n_nonzero"] = int(np.count_nonzero(d))
        rec["sum_abs_dMW"] = round(float(np.nansum(np.abs(d))), 6)
        if mx > E1_MAX_DMW:
            worst = a.iloc[int(np.nanargmax(np.abs(d)))]
            rec["worst_row"] = {
                "klass": str(worst["klass"]),
                "hour": int(worst["hour"]),
                "arm_mw": float(worst["mw"]),
                "keeper_mw": float(k.iloc[int(np.nanargmax(np.abs(d)))]["mw"]),
            }
            out["breaches"].append(
                {"year": year, "why": f"max |dMW| = {mx:.6f} > 0.000000"}
            )
        out["years"][str(year)] = rec
    out["verdict"] = "PASS" if not out["breaches"] else "STOP-THE-LINE"
    return out


def gate_determination(arm: Path) -> dict:
    """Report the arm's scored determination against the keeper's, unmoved."""
    ap_ = arm / "metrics.json"
    a = json.loads(ap_.read_text()) if ap_.is_file() else {}
    k = json.loads((KEEPER / "metrics.json").read_text())
    ac, kc = a.get("criteria", {}), k.get("criteria", {})
    moves = {
        key: {
            "keeper": kc.get(key, {}).get("status"),
            "arm": ac.get(key, {}).get("status"),
        }
        for key in sorted(set(ac) | set(kc))
        if kc.get(key, {}).get("status") != ac.get(key, {}).get("status")
    }
    return {
        "keeper_determination": k.get("determination"),
        "arm_determination": a.get("determination"),
        "keeper_grade": k.get("grade_summary"),
        "arm_grade": a.get("grade_summary"),
        "keeper_c1": k.get("free_class_score", {}).get("headline"),
        "arm_c1": a.get("free_class_score", {}).get("headline"),
        "criterion_moves": moves,
        "verdict": "PASS" if not moves else "MOVED",
    }


def main() -> None:
    """Score every pre-registered gate and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", default="results/calibration/_pjm152_collapse_gates.json")
    args = ap.parse_args()
    arm = REPO / args.arm

    rec: dict[str, object] = {
        "_what": "pjm-152 PREREG gate scoring: the rule 26 [R-DELETE] collapse "
        "of pjm_seam_envelope_by_neighbor, re-solved cold at the collapsed HEAD "
        "and diffed against the committed keeper pjm151_seam_B. E1 is THE gate "
        "and admits exactly zero movement.",
        "arm_bundle": args.arm,
        "keeper_bundle": "results/calibration/pjm151_seam_B",
        "K1_recipe": gate_k1(arm),
        "K2_control": gate_k2(arm),
        "K5_span": gate_k5(arm),
        "E1_byte_identity": gate_e1(arm),
        "determination": gate_determination(arm),
    }
    (REPO / args.out).write_text(json.dumps(rec, indent=2))
    print(f"wrote {args.out}")
    print(json.dumps(rec, indent=2)[:8000])


if __name__ == "__main__":
    main()
