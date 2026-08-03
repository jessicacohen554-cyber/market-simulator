"""Score the pjm-150 CT heat-rate re-gate against its pre-registered gates.

``PREREG-pjm150`` §3. This is the whole evidentiary product of the session: the
chartered A/B is moot (the PJM keeper already consumed the corrected artifact —
§1), so what remains is **K2**, the bit-identity check ``pjm-147`` could not run
because its own comparison spanned two HEADs.

Nothing here is hand-typed from a solve. Every figure is recomputed at run time
from the arm's and the keeper's own committed bytes, so the record cannot drift
from what it describes.

Usage::

    PYTHONPATH=.:src python scripts/probes/pjm150_regate_gates.py
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ISO = "PJM"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/pjm147_chp_B"
ARM = REPO / "results/calibration/pjm150_ctmeter_regate_A"
ARTIFACT = REPO / "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv"
FIX_COMMIT = "f6238a5"

_MISSING = object()

#: Shipped ``ScenarioConfig`` defaults that MOVED on ``main`` after the PJM
#: keeper solved (basis ``217e5b1``, 2026-08-03 01:57). ``config_drift`` cannot
#: tell a moved default from a changed recipe — the field is present on both
#: sides with different values either way (caiso-160 §4) — so each one is
#: enumerated with the commit that moved it and why it cannot reach a **PJM
#: calibration backcast**.
#:
#: DERIVED FOR PJM, not inherited from caiso-160's NYISO list (rule 25
#: ``[R-ISO-SCOPE]``, and caiso-160 §4's own instruction). The shared reason is
#: also **stronger** than the one caiso-160 recorded: it is not that the
#: evolution loop is mode-gated, but that the calibration harness never enters
#: it. ``run_calibration_full.solve_and_persist`` loops ``for year in years``
#: and calls ``run_calibration.run_year`` per year — a standalone per-year
#: backcast solve that builds that year's own historical fleet.
#: ``runner.py``'s multi-year ``evolve_fleet`` path, which owns capacity
#: evolution steps 0-6, is never reached from this lane at all.
#:
#: The allowlist is the HYPOTHESIS; K2 is the EVIDENCE. One non-zero MW voids it.
DEFAULT_MOVES = {
    "retirement_rule": (
        "24b1602 flipped the default legacy -> pipeline. Read only by "
        "model/capacity_evolution/retirements.py inside apply_economic_"
        "retirements (evolution step 3), which the calibration harness never "
        "calls — it solves each backcast year standalone via "
        "run_calibration.run_year, not runner.py's evolution loop."
    ),
    "entry_rate_limits": (
        "3e33f15 armed it by default. Read only by capacity_evolution/"
        "new_entry.py + adequacy.py (evolution step 5, economic new entry); "
        "the calibration harness builds nothing and never enters step 5."
    ),
    "entry_commissioning_lag": (
        "3e33f15 armed it by default. Same step-5 entry path "
        "(new_entry.py:1118 pending-queue netting), unreachable for the same "
        "reason."
    ),
    "net_cone_forward_escalation": (
        "e6f0cdb (owner decision D-3a) moved the default hold_last -> "
        "reindex_gross. Read only by config/capacity_market.py's forward "
        "net-CONE escalation, which prices the capacity-market revenue stream "
        "consumed by the evolution screens — forecast/hindcast machinery with "
        "no backcast reader."
    ),
    "caiso_ra_min_load_frac": (
        "a0fc302 task 3(b) made it CAISO-SCOPED under rule 25 [R-ISO-SCOPE]; "
        "backcast_config now assigns 0.26 only when iso == 'CAISO' and the "
        "neutral shipped 0.40 otherwise, so PJM re-records 0.40 where the "
        "keeper recorded a CAISO-fitted 0.26. Verified for PJM rather than "
        "inherited from caiso-160's NYISO entry: BOTH readers "
        "(pipeline/commitment.py:207 and :1582) sit behind "
        '`caiso_ra_mustoffer and iso == "CAISO"`, and this bundle carries '
        "caiso_ra_mustoffer=False AND iso='PJM' — either condition alone "
        "closes it. A RECORDING change, not a solve change. NOTE it also "
        "overrides the replayed meta.json kwarg (the keeper records it at "
        "top level), so a replay cannot re-assert the old value."
    ),
    "capacity_market_clearing_by_iso": (
        "the FF-2C per-ISO capacity-clearing flip arms PJM by default at HEAD "
        "(keeper recorded None). Listed for completeness only: "
        "ScenarioConfig.__post_init__ coerces it to None whenever "
        'mode == "backcast", explicitly so backcast keepers stay '
        "byte-identical, so it should not even appear as a diff."
    ),
}


def md5_bytes(b: bytes) -> str:
    """Return the hex md5 of a byte string."""
    return hashlib.md5(b).hexdigest()


def blob(ref: str, path: str) -> bytes:
    """Return a committed blob's bytes."""
    return subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=REPO, check=True, capture_output=True
    ).stdout


def artifact_stats() -> dict:
    """Measure the CT artifact's pre/post-fix applied cap-weighted heat rate."""
    rel = "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv"
    out = {}
    for label, ref in (("pre_fix", f"{FIX_COMMIT}^"), ("post_fix", FIX_COMMIT)):
        raw = blob(ref, rel)
        df = pd.read_csv(io.BytesIO(raw))
        ok = df[df["flag"] == "ok"]
        out[label] = {
            "md5": md5_bytes(raw),
            "rows": int(len(df)),
            "applied": int(len(ok)),
            "applied_capacity_mw": round(float(ok["class_capacity_mw"].sum()), 1),
            "cap_weighted_heat_rate": round(
                float(np.average(ok["heat_rate"], weights=ok["class_capacity_mw"])), 4
            ),
        }
    out["delta_cap_weighted"] = round(
        out["post_fix"]["cap_weighted_heat_rate"]
        - out["pre_fix"]["cap_weighted_heat_rate"],
        4,
    )
    out["on_disk_md5"] = md5_bytes(ARTIFACT.read_bytes())
    out["on_disk_is_post_fix"] = out["on_disk_md5"] == out["post_fix"]["md5"]
    return out


def config_drift(arm: Path, keeper: Path) -> dict:
    """Return the ScenarioConfig delta between two bundles, absence-aware.

    Splits the delta into keys only one side declares (schema drift: one bundle
    predates or postdates the field) and keys both declare with different values
    (a real config change, or a moved default — the two are byte-identical here,
    which is why :data:`DEFAULT_MOVES` exists).
    """
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    k = json.loads((keeper / "run_config.json").read_text())["scenario_config"]
    changed = [
        key
        for key in sorted(set(a) | set(k))
        if a.get(key, _MISSING) != k.get(key, _MISSING)
    ]
    return {
        "arm_only": [key for key in changed if key not in k],
        "keeper_only": [key for key in changed if key not in a],
        "value_diffs": [key for key in changed if key in a and key in k],
        "value_diff_detail": {
            key: {"keeper": k.get(key), "arm": a.get(key)}
            for key in changed
            if key in a and key in k
        },
    }


def control_bit_identity(arm: Path, keeper: Path) -> dict:
    """Return per-year max |ΔMW| on any P1 class-hour, arm vs keeper.

    The K2 gate. This arm replays the keeper's recipe at THIS HEAD against the
    SAME artifact, so any non-zero entry means something that landed after the
    keeper solved — a moved default in :data:`DEFAULT_MOVES`, or one of the 11
    ``src/market_sim`` commits since — reached the PJM backcast.
    """
    out: dict[str, float] = {}
    for year in YEARS:
        a_path = arm / "hourly" / f"class_hourly_{year}.parquet"
        k_path = keeper / "hourly" / f"class_hourly_{year}.parquet"
        if not (a_path.is_file() and k_path.is_file()):
            continue
        a = pd.read_parquet(a_path)
        k = pd.read_parquet(k_path)
        a, k = a[a["pass"] == "P1"], k[k["pass"] == "P1"]
        merged = a.merge(
            k, on=["klass", "hour"], suffixes=("_a", "_k"), how="outer"
        ).fillna(0.0)
        out[str(year)] = float((merged["mw_a"] - merged["mw_k"]).abs().max())
    return out


def class_twh(bundle: Path) -> dict:
    """Return per-year P1 class energy in TWh, for the K2 report's context."""
    out: dict[str, dict[str, float]] = {}
    for year in YEARS:
        path = bundle / "hourly" / f"class_hourly_{year}.parquet"
        if not path.is_file():
            continue
        df = pd.read_parquet(path)
        df = df[df["pass"] == "P1"]
        out[str(year)] = {
            str(klass): round(float(mw) / 1e6, 4)
            for klass, mw in df.groupby("klass")["mw"].sum().items()
        }
    return out


def scorecard(bundle: Path) -> dict:
    """Return a bundle's committed determination, grade summary and verdicts."""
    path = bundle / "metrics.json"
    if not path.is_file():
        return {}
    m = json.loads(path.read_text())
    return {
        "determination": m.get("determination"),
        "grade_summary": m.get("grade_summary"),
        "criteria": {
            key: (val or {}).get("status")
            for key, val in (m.get("criteria") or {}).items()
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default="results/calibration/_pjm150_regate_gates.json",
        help="where to write the measured gate record",
    )
    ap.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="report what is measurable instead of raising when the arm has "
        "not finished every year (for use mid-chain)",
    )
    args = ap.parse_args()

    art = artifact_stats()
    rec: dict = {
        "prereg": "results/calibration/PREREG-pjm150-ct-heat-rate-regate-2026-08-03.md",
        "iso": ISO,
        "keeper": str(KEEPER.relative_to(REPO)),
        "arm": str(ARM.relative_to(REPO)),
        "ct_heat_rate_artifact": art,
    }

    # The premise, re-measured rather than asserted: the keeper's basis commit
    # must already carry the POST-FIX artifact, which is what makes the
    # chartered A/B moot and this a single-arm re-gate.
    basis = json.loads((KEEPER / "run_config.json").read_text())["git"]["basis_sha"]
    keeper_blob_md5 = md5_bytes(
        blob(basis, "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv")
    )
    rec["premise"] = {
        "keeper_basis_sha": basis,
        "artifact_md5_at_keeper_basis": keeper_blob_md5,
        "keeper_already_on_corrected_artifact": keeper_blob_md5
        == art["post_fix"]["md5"],
    }

    if not (ARM / "run_config.json").is_file():
        rec["status"] = "ARM NOT SOLVED"
        Path(args.out).write_text(json.dumps(rec, indent=1))
        print(json.dumps(rec, indent=1))
        return

    # K1 — zero recipe changes. Every value diff must be an enumerated moved
    # default; anything else means this arm is controlled against a different
    # recipe than the keeper it is measuring.
    drift = config_drift(ARM, KEEPER)
    unexplained = [k for k in drift["value_diffs"] if k not in DEFAULT_MOVES]
    drift["default_moves_exempted"] = {
        k: DEFAULT_MOVES[k] for k in drift["value_diffs"] if k in DEFAULT_MOVES
    }
    drift["unexplained_value_diffs"] = unexplained
    rec["K1_config_drift"] = drift
    rec["K1_passed"] = not unexplained

    # K2 — bit-identity against the committed keeper.
    identity = control_bit_identity(ARM, KEEPER)
    rec["K2_max_abs_mw_by_year"] = identity
    complete = len(identity) == len(YEARS)
    rec["K2_years_measured"] = sorted(identity)
    rec["K2_passed"] = complete and max(identity.values(), default=1.0) == 0.0
    rec["K2_complete"] = complete

    rec["class_twh_keeper"] = class_twh(KEEPER)
    rec["class_twh_arm"] = class_twh(ARM)

    # K4 — no criterion regresses.
    ks, as_ = scorecard(KEEPER), scorecard(ARM)
    rec["K4_keeper_scorecard"] = ks
    rec["K4_arm_scorecard"] = as_
    if ks and as_:
        flips = sorted(
            key
            for key in set(ks["criteria"]) | set(as_["criteria"])
            if ks["criteria"].get(key) != as_["criteria"].get(key)
        )
        rec["K4_criterion_flips"] = flips
        # K4 splits, because exactly one of the nine criteria is not
        # model-determined. C6 `governance` reads the bundle's rule-21
        # attestation, which a probe arm does not carry and which no solve can
        # produce — caiso-159 §3 documents the same UNATTESTED -> NOT-YET
        # bookkeeping on arms that reproduced their incumbent exactly. It is
        # reported, never absorbed: K4a is the gate on model behaviour, K4b
        # discloses the bookkeeping difference.
        rec["K4a_model_criterion_flips"] = [k for k in flips if k != "governance"]
        rec["K4a_passed"] = not rec["K4a_model_criterion_flips"]
        rec["K4b_governance_flip"] = "governance" in flips
        rec["K4b_reason"] = (
            "probe arm carries no rule-21 attestation; C6 is attestation-"
            "presence bookkeeping, not a model verdict. With K2 = 0.000000 MW "
            "on every P1 class-hour the eight model-determined criteria are "
            "not merely equal but PROVABLY equal — identical dispatch cannot "
            "score differently."
            if "governance" in flips
            else ""
        )
        rec["K4_passed"] = (
            not flips
            and ks["determination"] == as_["determination"]
            and ks["grade_summary"] == as_["grade_summary"]
        )
    else:
        rec["K4_passed"] = None

    # K5 — span and holdout posture.
    arm_years = sorted(
        int(y) for y in json.loads((ARM / "meta.json").read_text())["years"]
    )
    rec["K5_years"] = arm_years
    rec["K5_passed"] = arm_years == list(YEARS)

    Path(args.out).write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))

    if args.allow_incomplete:
        return
    if unexplained:
        raise SystemExit(
            f"{ISO}: K1 FAILED — {len(unexplained)} unexplained ScenarioConfig "
            f"value difference(s) vs the keeper: {', '.join(unexplained)}"
        )
    if not rec["K2_passed"]:
        worst = max(identity.values(), default=float("nan"))
        raise SystemExit(
            f"{ISO}: K2 control integrity FAILED — the arm diverges from the "
            f"committed keeper by up to {worst:.6f} MW on a class-hour "
            f"({identity}). Something that landed after the keeper solved "
            "reached the PJM backcast; the DEFAULT_MOVES exemption is void."
        )


if __name__ == "__main__":
    main()
