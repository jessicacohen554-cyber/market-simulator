"""Score the pjm-151 PREREG gates on the solved arm (K1/K3/K4/E1). No LP.

K2 is discharged WITHOUT a solve (PREREG-pjm151 §6): pjm-150 measured the keeper
reproducing bit-identically at HEAD ``01b6a6a``, and every ``src/market_sim``
commit between that point and this arm's basis is provably PJM-inert by
inspection. So the CONTROL is the committed keeper bundle ``pjm147_chp_B`` and
this script compares the treatment against it directly.

Reads only committed/solved artifacts — no re-solve, no floor rebuild.

Usage:
    PYTHONPATH=.:src python <this> --arm results/calibration/pjm151_seam_B
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path[:0] = [str(REPO), str(REPO / "src")]

KEEPER = REPO / "results/calibration/pjm147_chp_B"
YEARS = (2023, 2024, 2025)
_MISSING = object()

#: The ONE pre-registered delta (PREREG-pjm151 §4).
DECLARED_DELTA = "pjm_seam_envelope_by_neighbor"

#: Fields present on only ONE side because the SCHEMA moved, not the recipe.
#: ``config_drift`` is absence-aware for exactly this reason (caiso-160 §4): a
#: field the keeper's ``run_config.json`` predates shows up as ``arm_only`` even
#: when both sides run it at the same effective value. Each is enumerated with
#: why it cannot reach a PJM calibration backcast.
SCHEMA_DRIFT = {
    "pjm_seam_envelope_by_neighbor": (
        "THE DECLARED DELTA (PREREG-pjm151 §4). New in this session, so the "
        "keeper predates the field entirely and its effective keeper value is "
        "the shipped default False -- which is why it lands in arm_only rather "
        "than as a False -> True value_diff."
    ),
    "electrification_path": (
        "2541a02 added the FF-G4 Option-B electrification load-shape layers, "
        "default off. Forecast-only demand layering with no backcast reader."
    ),
    "electrification_percentile": "same FF-G4 layer as electrification_path.",
    "nyiso_nyc_rcpf_step_curve": (
        "69f1aa0 (nyiso-115) added it, default off; NYISO-gated RCPF demand "
        "curve, unreachable for iso='PJM'."
    ),
    "nyiso_seny_rcpf_increment_step": (
        "4491fe6 (nyiso-119) added it, default off; the reserves/spec.py branch "
        "gates on `seny_increment and name == NYISO_SENY_30MIN_FAMILY` and "
        "reduces to the pre-existing condition when off, so PJM is "
        "byte-identical."
    ),
    "ct_committed_hr_override": (
        "DELETED from ScenarioConfig by a0fc302 ('delete the dead CT_CHP "
        "override triple'), so the keeper records a field that no longer "
        "exists. Removed precisely because it was dead -- rule 26 [R-DELETE]."
    ),
    "ct_econ_hr_override": "same a0fc302 deletion as ct_committed_hr_override.",
    "ct_peak_hr_override": "same a0fc302 deletion as ct_committed_hr_override.",
}

#: Shipped ``ScenarioConfig`` defaults that MOVED on main after the PJM keeper
#: solved (basis ``217e5b1``). Carried forward from pjm-150's PJM-derived list
#: (``scripts/probes/pjm150_regate_gates.py``), which corrected the reasoning:
#: the true reason these cannot reach a PJM backcast is NOT that the evolution
#: loop is mode-gated but that the CALIBRATION HARNESS NEVER CALLS IT --
#: ``solve_and_persist`` loops years through ``run_calibration.run_year``, a
#: standalone per-year solve, so ``runner.py``'s ``evolve_fleet`` path (which
#: owns capacity-evolution steps 0-6) is never entered from this lane.
DEFAULT_MOVES = {
    "retirement_rule",
    "entry_rate_limits",
    "entry_commissioning_lag",
    "net_cone_forward_escalation",
    "caiso_ra_min_load_frac",
    "capacity_market_clearing_by_iso",
}

#: C1 band: |d| <= min(2% of ISO load, 8 TWh) and |share| <= 3.0 pp.
C1_VOL_CAP_TWH = 8.0
#: PREREG-pjm151 E1's ex ante magnitude discipline.
E1_MAX_MOVE_TWH = 3.0


def scenario_cfg(bundle: Path) -> dict:
    """Return a bundle's recorded ScenarioConfig."""
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def gate_k1(arm: Path) -> dict:
    """K1 -- exactly one differing key vs the keeper, the declared delta."""
    a, k = scenario_cfg(arm), scenario_cfg(KEEPER)
    changed = [
        key
        for key in sorted(set(a) | set(k))
        if a.get(key, _MISSING) != k.get(key, _MISSING)
    ]
    value_diffs = [c for c in changed if c in a and c in k]
    arm_only = [c for c in changed if c not in k]
    keeper_only = [c for c in changed if c not in a]
    # The declared delta arrives as arm_only, NOT as a value_diff: the keeper's
    # run_config predates the field, so its effective keeper value is the
    # shipped default False.
    armed = a.get(DECLARED_DELTA) is True
    unexplained = [
        c for c in value_diffs if c != DECLARED_DELTA and c not in DEFAULT_MOVES
    ] + [c for c in (*arm_only, *keeper_only) if c not in SCHEMA_DRIFT]
    return {
        "arm_only": arm_only,
        "keeper_only": keeper_only,
        "value_diffs": value_diffs,
        "detail": {c: {"keeper": k.get(c), "arm": a.get(c)} for c in value_diffs},
        "declared_delta_armed": armed,
        "declared_delta_channel": (
            "arm_only (keeper predates the field; effective keeper value = "
            "shipped default False)"
            if DECLARED_DELTA in arm_only
            else "value_diff"
        ),
        "schema_drift_explained": {
            c: SCHEMA_DRIFT[c] for c in (*arm_only, *keeper_only) if c in SCHEMA_DRIFT
        },
        "default_moves_explained": [c for c in value_diffs if c in DEFAULT_MOVES],
        "unexplained": unexplained,
        "verdict": "PASS" if armed and not unexplained else "FAIL",
    }


def _zone_net(bundle: Path, year: int) -> pd.DataFrame | None:
    """Per-zone hourly LMP + any zone-grain series the system sidecar carries."""
    p = bundle / "hourly" / f"system_{year}.parquet"
    return pd.read_parquet(p) if p.is_file() else None


def gate_k3(arm: Path) -> dict:
    """K3 -- liveness. Zero movement is a REPORTABLE inert, never a tuning cue."""
    out: dict[str, object] = {}
    for year in YEARS:
        a = _zone_net(arm, year)
        k = _zone_net(KEEPER, year)
        if a is None or k is None:
            out[str(year)] = {"status": "missing sidecar"}
            continue
        rec: dict[str, object] = {}
        # class-hour dispatch delta (the blunt liveness instrument)
        ap = arm / "hourly" / f"class_hourly_{year}.parquet"
        kp = KEEPER / "hourly" / f"class_hourly_{year}.parquet"
        if ap.is_file() and kp.is_file():
            adf, kdf = pd.read_parquet(ap), pd.read_parquet(kp)
            num = [c for c in adf.columns if adf[c].dtype.kind == "f"]
            common = [c for c in num if c in kdf.columns]
            if len(adf) == len(kdf):
                d = adf[common].to_numpy() - kdf[common].to_numpy()
                rec["max_abs_class_hour_dMW"] = round(float(np.nanmax(np.abs(d))), 6)
                rec["n_class_hours"] = int(d.size)
        # zonal price movement on the two zones the PREREG named
        for col in a.columns:
            if "Dominion" in col or "AEP_Ohio" in col:
                if col in k.columns and len(a) == len(k):
                    dd = a[col].to_numpy(dtype=float) - k[col].to_numpy(dtype=float)
                    rec[f"{col}_mean_d"] = round(float(np.nanmean(dd)), 4)
                    rec[f"{col}_max_abs_d"] = round(float(np.nanmax(np.abs(dd))), 4)
        out[str(year)] = rec
    return out


def _payload_gm(run_id: str) -> dict:
    """Decode a registered run payload's per-year gmModel class TWh."""
    import base64

    p = REPO / f"frontend/data/backcast/runs/{run_id}.js"
    s = p.read_text()
    b = s.split('"', 3)[3].split('"')[0]
    d = json.loads(gzip.decompress(base64.b64decode(b)))
    return {y: v["gmModel"] for y, v in d["years"].items()}


def gate_e1(arm: Path) -> dict:
    """E1 -- per-class C1 magnitude against the ex ante declared headroom."""
    from scripts.calibration_verdict import (
        COAL_CLASSES,
        FUELMIX_EXCLUDED,
        GAS_CLASSES,
        class_is_gated,
    )

    classes = [c for c in (*GAS_CLASSES, *COAL_CLASSES) if c not in FUELMIX_EXCLUDED]
    keeper_gm = _payload_gm("2026-08-03-pjm-147b-chp-heat")
    arm_metrics = json.loads((arm / "metrics.json").read_text())
    # the arm's own class TWh come from its metrics/bundle scoring pass
    out: dict[str, object] = {"breaches": [], "rows": []}
    for year in YEARS:
        ys = str(year)
        bench_p = REPO / f"frontend/data/backcast/bench/PJM/{ys}.json.gz"
        cf = json.loads(gzip.open(bench_p, "rt").read())["bench"].get("classFull", {})
        kgm = keeper_gm.get(ys, {})
        agm = _arm_class_twh(arm, year)
        for c in classes:
            if c not in cf or c not in agm:
                continue
            actual = float(cf[c])
            km, am = float(kgm.get(c, 0.0)), float(agm[c])
            row = {
                "year": year,
                "class": c,
                "gated": bool(class_is_gated("PJM", c, year)),
                "actual": round(actual, 3),
                "keeper": round(km, 3),
                "arm": round(am, 3),
                "keeper_d": round(km - actual, 3),
                "arm_d": round(am - actual, 3),
                "move": round(am - km, 3),
                "headroom_used": round(abs(am - actual), 3),
            }
            if abs(row["move"]) > E1_MAX_MOVE_TWH:
                out["breaches"].append({**row, "why": "move > 3.0 TWh (E1 cap)"})
            if row["gated"] and abs(row["arm_d"]) > C1_VOL_CAP_TWH:
                out["breaches"].append({**row, "why": "|d| > 8.0 TWh (C1 band)"})
            out["rows"].append(row)
    out["verdict"] = "PASS" if not out["breaches"] else "FAIL"
    out["arm_determination"] = arm_metrics.get("determination")
    return out


def _arm_class_twh(arm: Path, year: int) -> dict:
    """Class TWh for the arm, from its own P1 class_hourly sidecar (MWh -> TWh).

    The sidecar is LONG-form (``year, pass, klass, hour, mw``), not one column
    per class, and carries both passes — so it must be filtered to ``P1`` (the
    scored pass) before summing. Reading it wide silently produced zero rows on
    the first attempt, which would have reported a VACUOUS E1 pass.
    """
    p = arm / "hourly" / f"class_hourly_{year}.parquet"
    if not p.is_file():
        return {}
    df = pd.read_parquet(p)
    df = df[df["pass"].astype(str) == "P1"]
    g = df.groupby(df["klass"].astype(str))["mw"].sum() / 1e6
    return {str(k): float(v) for k, v in g.items()}


def gate_k4(arm: Path) -> dict:
    """K4 -- criterion-by-criterion, keeper vs arm. Any move is REPORTED."""
    a = json.loads((arm / "metrics.json").read_text())
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
    ap.add_argument("--out", default="results/calibration/_pjm151_seam_gates.json")
    args = ap.parse_args()
    arm = REPO / args.arm

    rec: dict[str, object] = {
        "_what": "pjm-151 PREREG gate scoring: seam envelope per-neighbour arm "
        "vs the committed keeper pjm147_chp_B. K2 discharged without a solve.",
        "arm_bundle": args.arm,
        "keeper_bundle": "results/calibration/pjm147_chp_B",
        "K1_recipe": gate_k1(arm),
        "K3_liveness": gate_k3(arm),
        "K4_criteria": gate_k4(arm),
        "E1_c1_magnitude": gate_e1(arm),
    }
    (REPO / args.out).write_text(json.dumps(rec, indent=2))
    print(f"wrote {args.out}")
    print(
        json.dumps(
            {k: v for k, v in rec.items() if k.startswith(("K", "E"))}, indent=2
        )[:6000]
    )


if __name__ == "__main__":
    main()
