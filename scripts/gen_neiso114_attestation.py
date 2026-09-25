"""Emit the neiso-114 arm A calibration attestation for the composite.

neiso-114 (``docs/handoffs/neiso114/PRECOMMIT-neiso114-2026-09-25.md``) replays
the NEISO keeper ``2026-09-24-r-neiso-inputs-2019`` (``rneiso_span``) with ONE
registered delta, ``coal_mustrun_requires_measured_row=true`` (zero free
parameters: it withdraws the unmeasured 45 %-of-nameplate coal must-run default
from plants absent from ``thermal_tranches_NEISO.csv`` — Bridgeport Harbor 568
u3 and Schiller 2367), one year per shard (rule 36), composed at zero LP into
``neiso114a_span`` (2019-2025).

``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``,
so the keeper's governance block and DOF ledger are inherited verbatim;
**zero free parameters are added and none is re-cut** (rules 21 / 24).
``offer_curve_by_group`` is asserted identical to the keeper's apart from the
legacy bare ``COAL`` entry COAL-SUB (#6619) folds out at replay (G-DRIFT,
PRECOMMIT §2), so the rule-1 authorized price-tuning channel was not touched.

Arm B (``--arm B``, bundle ``neiso114b_span``) is arm A plus NEISO's ST_GAS
offer bands re-derived on the CORRECTED class: the unchanged
``derive_campd_marginal_hr`` per-unit construction over Montville, Middletown,
Newington, New Haven Harbor and West Springfield (7 CEMS units, 2019-2025),
x NEISO's own CC reach 1.223, x the keeper's fossil scalar 0.9547 (PRECOMMIT §3).
Its control is the promoted arm-A keeper; the ledger records the re-identified
magnitudes (measured, not residual-identified).

Usage:
    python scripts/gen_neiso114_attestation.py [--arm A|B]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
COMPOSITE = "neiso114a_span"
KEEPER = "rneiso_span"
KEEPER_ID = "2026-09-24-r-neiso-inputs-2019"
PRECOMMIT = "docs/handoffs/neiso114/PRECOMMIT-neiso114-2026-09-25.md"
RESULT = "docs/handoffs/neiso114/RESULT-neiso114-2026-09-25.md"
PINNED = "9db30b45a55bf4bbd9cdbc3b2a7f51aa37dc7466"
FLIPS = ("coal_mustrun_requires_measured_row",)


def _offer_sha(bundle: Path) -> str:
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    curve = {
        g: v for g, v in (cfg.get("offer_curve_by_group") or {}).items() if g != "COAL"
    }
    return hashlib.sha256(json.dumps(curve, sort_keys=True).encode()).hexdigest()[:16]


def main_b() -> int:
    """Write arm B's attestation from the promoted arm-A keeper's."""
    bundle, kb = CAL / "neiso114b_span", CAL / COMPOSITE
    att = json.loads((kb / "calibration_attestation.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    skip = frozenset({"COAL", "ST_GAS"})
    if _offer_sha(bundle, skip) != _offer_sha(kb, skip):
        raise SystemExit("offer_curve_by_group moved outside ST_GAS")
    want = json.loads(
        (REPO / "docs/handoffs/neiso114/arm_b_offer_curve.json").read_text()
    )
    for y in years:
        rc = json.loads((bundle / f"run_config_{y}.json").read_text())
        if rc["calibration_flags"].get("offer_curve_overrides") != want:
            raise SystemExit(f"{y}: offer_curve_overrides != arm_b_offer_curve.json")
        if rc["scenario_config"].get("coal_mustrun_requires_measured_row") is not True:
            raise SystemExit(f"{y}: coal_mustrun_requires_measured_row not armed")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        "neiso-114 (2026-09-25) arm B -- the promoted arm-A keeper recipe replayed one year per "
        "shard (rule 36) with NEISO's ST_GAS offer bands re-derived on the corrected class "
        "(docs/handoffs/neiso114/arm_b_offer_curve.json). Pre-registered in "
        f"{PRECOMMIT} §3 (pinned {PINNED[:8]}) before any solve; the value was never swept."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["st_gas_rederivation"] = {
            "bands_effective": want["ST_GAS"],
            "bands_registered": {
                "committed": 0.89,
                "econ_low": 1.07,
                "econ_high": 1.20,
                "peak": 1.20,
            },
            "construction": (
                "derive_campd_marginal_hr.derive_unit_bands UNCHANGED, corrected ST_GAS class "
                "(546, 562, 8002, 6156, 1642; 7 units) pooled 2019-2025, each unit normalised by "
                "its own average HR: marg p50 0.727 / 0.872 / 0.983 x NEISO CC reach 1.223 -> "
                "0.89 / 1.07 / 1.20 (2 dp) x fossil scalar 0.9547; peak = max(registered 1.0, "
                "econ_high) so the ladder stays monotone. Rule 23 data change: the class "
                "membership the F1 vintage correction restored."
            ),
            "set_ex_ante": True,
            "not_swept": True,
            "one_config_all_years": years,
        }
    fp = att["free_parameters"]
    fp["entries"].append(
        {
            "name": "st_gas_bands_corrected_class",
            "where": "run_config.calibration_flags.offer_curve_overrides.ST_GAS",
            "identification": "measured (CAMPD marginal heat rate of the corrected ST_GAS class) x existing reach and scalar",
            "value": want["ST_GAS"],
            "note": (
                "A re-identification of the existing ST_GAS band magnitudes, not a new knob: the "
                "previous values were the same construction on Montville alone (n=2 units). "
                "Not residual-identified; set ex ante in the PRECOMMIT, never swept."
            ),
        }
    )
    fp["n_entries"] = len(fp["entries"])
    att["neiso114"] = {
        "precommit": PRECOMMIT,
        "result": RESULT,
        "keeper_control": "2026-09-25-neiso114-coal-mustrun-measured",
        "arm": "B",
    }
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


def main() -> int:
    """Write the composite's attestation from the keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", choices=("A", "B"), default="A")
    if ap.parse_args().arm == "B":
        return main_b()
    bundle, kb = CAL / COMPOSITE, CAL / KEEPER
    att = json.loads((kb / "calibration_attestation.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    sha, ksha = _offer_sha(bundle), _offer_sha(kb)
    if sha != ksha:
        raise SystemExit(f"offer_curve_by_group {sha} != keeper {ksha}")
    for y in years:
        sc = json.loads((bundle / f"run_config_{y}.json").read_text())[
            "scenario_config"
        ]
        off = [f for f in FLIPS if sc.get(f) is not True]
        if off:
            raise SystemExit(f"{y}: flips not armed: {off}")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"neiso-114 (2026-09-25) arm A -- keeper {KEEPER_ID}'s recipe replayed via "
        "scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), with one registered zero-DOF "
        f"delta: {', '.join(FLIPS)}. Every leg verified by docs/handoffs/neiso114/shard_check.py "
        f"at composition. Zero LP in the parent. Pre-registered in {PRECOMMIT} (pinned "
        f"{PINNED[:8]}) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"neiso-114 arm A (2026-09-25): this run's own solved years {years}. "
            f"offer_curve_by_group (bare COAL entry excluded, folded by COAL-SUB) SHA-256 {sha} "
            f"equals keeper {KEEPER_ID}'s; no band moved and nothing was swept (rule 1 (c))."
        )
    gov["structural_delta"] = {
        "flips": list(FLIPS),
        "free_parameters_added": 0,
        "basis": (
            "rule 17 [R-FLOOR-WINDOW] / pjm-h14: a coal plant absent from the CAMPD thermal-"
            "tranche artifact no longer takes the unmeasured 45 % must-run default held in all "
            "8,760 h; its capacity falls to the economic band. NEISO population: Bridgeport "
            "Harbor 568 u3 (173 / 116 / 116 MW 2019-21) and Schiller 2367 (43 MW), restored by "
            "the corrected EIA-860 vintages but never seen by the canonical-fleet artifact."
        ),
        "control": f"the committed keeper {KEEPER} (rule 29(b) form 4); G-DRIFT {PRECOMMIT} §2",
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["neiso114"] = {
        "precommit": PRECOMMIT,
        "result": RESULT,
        "keeper_control": KEEPER_ID,
        "arm": "A",
    }
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
