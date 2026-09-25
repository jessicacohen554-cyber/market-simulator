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

Usage:
    python scripts/gen_neiso114_attestation.py
"""

from __future__ import annotations

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


def main() -> int:
    """Write the composite's attestation from the keeper's."""
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
