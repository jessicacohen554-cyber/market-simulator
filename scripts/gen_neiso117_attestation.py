"""Emit the neiso-117 calibration attestation for the composite ``neiso117_span``.

neiso-117 (``docs/handoffs/neiso117/PRECOMMIT-neiso117-2026-09-26.md``) replays
the NEISO keeper ``2026-09-25-neiso114-arm-b-stgas`` (``neiso114b_span``) with ONE
registered delta, ``coal_fuel_inventory_plant_grain=true`` — the per-coal-yard
ANNUAL fuel budget rows (Dec(Y-1) EIA-923 stock + mean Y-2..Y-1 receipts per
yard, zero free parameters), armed WITHOUT the pooled monthly limb on the owner
ruling of 2026-09-26 — one year per shard (rule 36), composed at zero LP.

``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``,
so the keeper's governance block and DOF ledger are inherited verbatim; **zero
free parameters are added and none is re-cut** (rules 21 / 24).
``offer_curve_by_group`` is asserted identical to the keeper's (legacy bare
``COAL`` entry set aside, as COAL-SUB folds it at replay), so the rule-1
authorized price-tuning channel was not touched.

Usage:
    python scripts/gen_neiso117_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
COMPOSITE = "neiso117_span"
KEEPER = "neiso114b_span"
KEEPER_ID = "2026-09-25-neiso114-arm-b-stgas"
PRECOMMIT = "docs/handoffs/neiso117/PRECOMMIT-neiso117-2026-09-26.md"
RESULT = "docs/handoffs/neiso117/RESULT-neiso117-2026-09-26.md"
PINNED = "17402f351e5dc3d45126100b7839531cd21c1ca3"
FLIPS = ("coal_fuel_inventory_plant_grain",)
UNARMED = ("coal_fuel_inventory",)


def _offer_sha(bundle: Path, skip: frozenset = frozenset({"COAL"})) -> str:
    """Hash of the resolved ``offer_curve_by_group`` with ``skip`` groups set aside."""
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    curve = {
        g: v
        for g, v in (cfg.get("offer_curve_by_group") or {}).items()
        if g not in skip
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
        on = [f for f in UNARMED if sc.get(f)]
        if off or on:
            raise SystemExit(f"{y}: flips not armed {off} / must stay off {on}")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"neiso-117 (2026-09-26) -- keeper {KEEPER_ID}'s recipe replayed via "
        "scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), with one registered zero-DOF "
        f"delta: {', '.join(FLIPS)} (per-coal-yard annual budget rows; the pooled monthly limb "
        "coal_fuel_inventory stays off, owner ruling 2026-09-26). Every leg verified by "
        "docs/handoffs/neiso117/shard_check.py at composition. Zero LP in the parent. "
        f"Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard launched; "
        f"record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"neiso-117 (2026-09-26): this run's own solved years {years}. "
            f"offer_curve_by_group (bare COAL entry excluded, folded by COAL-SUB) SHA-256 {sha} "
            f"equals keeper {KEEPER_ID}'s; no band moved and nothing was swept (rule 1 (c))."
        )
    gov["structural_delta"] = {
        "flips": list(FLIPS),
        "free_parameters_added": 0,
        "basis": (
            "rule 13 [R-MEASURED] / rule 14 [R-ACCURATE]: coal energy input at each NEISO coal "
            "yard (Bridgeport 568, Merrimack 2364, Schiller 2367) is capped annually at the coal "
            "that physically existed -- Dec(Y-1) EIA-923 Page 2 stock + mean Y-2..Y-1 Page 5 "
            "receipts x the yard's own prior-years heat content. Every sizing quantity predates "
            "the solved year; the keeper burned 31.0 TBtu at Merrimack in 2022 against a 7.68 "
            "TBtu yard budget (PRECOMMIT-neiso116 s2)."
        ),
        "control": f"the committed keeper {KEEPER} (rule 29(b) form 4); G-DRIFT {PRECOMMIT} s3",
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["neiso117"] = {
        "precommit": PRECOMMIT,
        "result": RESULT,
        "keeper_control": KEEPER_ID,
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
