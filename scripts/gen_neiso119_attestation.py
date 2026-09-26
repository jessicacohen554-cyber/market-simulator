"""Emit the neiso-119 calibration attestation for the composite ``neiso119_span``.

neiso-119 (``docs/handoffs/neiso119/PRECOMMIT-neiso119-2026-09-26.md``) replays
the NEISO keeper ``2026-09-26-neiso-118-canal-ct`` (``neiso118_span``) with two
owner-ruled arms (2026-09-26): ``gas_offer_margin_anchor_vintage`` (the gas
net-revenue margin identified on the solved year's own delivered gas instead of
the frozen 2023-2025 mean) and ``neiso_winter_fuelsec_conduct_roster`` (the winter
fuel-security floor narrowed to plants whose CEMS boilers were online in its
cold-day window in other years) — one year per shard (rule 36), composed at zero
LP.

``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``,
so the keeper's governance block and DOF ledger are inherited verbatim; **zero
free parameters are added and none is re-cut** (rules 21 / 24).
``offer_curve_by_group`` is asserted identical to the keeper's, so the rule-1
authorized price-tuning channel was not touched.

Usage:
    python scripts/gen_neiso119_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
COMPOSITE = "neiso119_span"
KEEPER = "neiso118_span"
KEEPER_ID = "2026-09-26-neiso-118-canal-ct"
PRECOMMIT = "docs/handoffs/neiso119/PRECOMMIT-neiso119-2026-09-26.md"
RESULT = "docs/handoffs/neiso119/RESULT-neiso119-2026-09-26.md"
PINNED = "00d4a7691c2f30c39a72d9d99e31a2ce1d07546f"
CT_ARTIFACT = "data/raw/_processed-legacy/winter_fuelsec_conduct_NEISO.csv"
CT_SHA256 = "1952101d29f51222bba9f5b8579a4dccc2e762a76f705238cc525b0a84fb5a58"
FLIPS: tuple[str, ...] = (
    "gas_offer_margin_anchor_vintage",
    "neiso_winter_fuelsec_conduct_roster",
)
#: Fields that move with the arms (the anchor is re-resolved per solve year).
EXPECTED_MOVES = frozenset(
    {"gas_offer_margin_anchor_vintage", "gas_offer_margin_anchor"}
)
KEEP_ARMED = (
    "coal_fuel_inventory_plant_grain",
    "measured_ct_heat_rates",
    "gas_offer_margin_anchor_vintage",
    "neiso_winter_fuelsec_conduct_roster",
)


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
        k = json.loads((kb / f"run_config_{y}.json").read_text())["scenario_config"]
        sc = json.loads((bundle / f"run_config_{y}.json").read_text())[
            "scenario_config"
        ]
        moved = [
            f
            for f in sorted(set(sc) & set(k))
            if sc[f] != k[f] and f not in EXPECTED_MOVES and f != "offer_curve_by_group"
        ]
        off = [f for f in KEEP_ARMED if sc.get(f) is not True]
        if moved or off:
            raise SystemExit(f"{y}: config moved {moved} / not armed {off}")
    ct = hashlib.sha256((REPO / CT_ARTIFACT).read_bytes()).hexdigest()
    if ct != CT_SHA256:
        raise SystemExit(f"conduct artifact {ct} != pinned {CT_SHA256}")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"neiso-119 (2026-09-26) -- keeper {KEEPER_ID}'s recipe replayed via "
        "scripts/replay_keeper.py with --set gas_offer_margin_anchor_vintage=true and "
        "--set neiso_winter_fuelsec_conduct_roster=true (owner rulings 2026-09-26), ONE YEAR "
        f"PER SHARD (rule 36); conduct artifact {CT_ARTIFACT} sha256 {CT_SHA256[:12]}. Every "
        "leg verified by docs/handoffs/neiso119/shard_check.py at composition. Zero LP in the "
        f"parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard "
        f"launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"neiso-119 (2026-09-26): this run's own solved years {years}. "
            f"offer_curve_by_group (bare COAL entry excluded, folded by COAL-SUB) SHA-256 {sha} "
            f"equals keeper {KEEPER_ID}'s; no band moved and nothing was swept (rule 1 (c))."
        )
    gov["structural_delta"] = {
        "flips": list(FLIPS),
        "data_artifact": CT_ARTIFACT,
        "free_parameters_added": 0,
        "basis": (
            "(1) gas_offer_margin_anchor_vintage: the gas net-revenue margin's identification "
            "point (fuel == anchor reduces the offer to the calibrated band multiplier) was a "
            "frozen 2023-2025 mean applied to every year; evaluated on the solved year it is the "
            "SAME frozen formula (rule 23), zero DOF, not the rule-1 carve-out (bands untouched). "
            "(2) neiso_winter_fuelsec_conduct_roster: the winter fuel-security floor bound units "
            "CEMS shows offline over its own window (rule 17 [R-FLOOR-WINDOW]); the roster keeps "
            "only plants online in >= 0.5 of that window in OTHER years (D-4's test, "
            "leave-one-year-out, rule 13). Adopted for structure, never because a residual moved."
        ),
        "control": f"the committed keeper {KEEPER} (rule 29(b) form 4); G-DRIFT {PRECOMMIT} s4",
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["neiso119"] = {
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
