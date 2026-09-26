"""Emit the neiso-118 calibration attestation for the composite ``neiso118_span``.

neiso-118 (``docs/handoffs/neiso118/PRECOMMIT-neiso118-2026-09-26.md``) replays
the NEISO keeper ``2026-09-26-neiso-117-coal-yard`` (``neiso117_span``) with NO
config delta: the arm is a data re-derive — the NEISO measured-CT heat-rate
artifact regenerated after the class-preserving ``union_fleet`` repair, which
adds Canal 3 (plant 1599) rows only (owner ruling 2026-09-26, "CT only") — one
year per shard (rule 36), composed at zero LP.

``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``,
so the keeper's governance block and DOF ledger are inherited verbatim; **zero
free parameters are added and none is re-cut** (rules 21 / 24).
``offer_curve_by_group`` is asserted identical to the keeper's, so the rule-1
authorized price-tuning channel was not touched.

Usage:
    python scripts/gen_neiso118_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
COMPOSITE = "neiso118_span"
KEEPER = "neiso117_span"
KEEPER_ID = "2026-09-26-neiso-117-coal-yard"
PRECOMMIT = "docs/handoffs/neiso118/PRECOMMIT-neiso118-2026-09-26.md"
RESULT = "docs/handoffs/neiso118/RESULT-neiso118-2026-09-26.md"
PINNED = "faa5bd591040e58e31a33e3c3369c1de7d4f31ea"
CT_ARTIFACT = "data/raw/_processed-legacy/campd_ct_heat_rates_NEISO.csv"
CT_SHA256 = "f57df14e6e506dc1e06b7174510c98b6fb64aec0d0b5737baf5666cdb06dd9f9"
FLIPS: tuple[str, ...] = ()
KEEP_ARMED = ("coal_fuel_inventory_plant_grain", "measured_ct_heat_rates")


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
            if sc[f] != k[f] and f != "offer_curve_by_group"
        ]
        off = [f for f in KEEP_ARMED if sc.get(f) is not True]
        if moved or off:
            raise SystemExit(f"{y}: config moved {moved} / not armed {off}")
    ct = hashlib.sha256((REPO / CT_ARTIFACT).read_bytes()).hexdigest()
    if ct != CT_SHA256:
        raise SystemExit(f"CT artifact {ct} != pinned {CT_SHA256}")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"neiso-118 (2026-09-26) -- keeper {KEEPER_ID}'s recipe replayed UNCHANGED via "
        "scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), on the re-derived NEISO "
        f"measured-CT heat-rate artifact ({CT_ARTIFACT}, sha256 {CT_SHA256[:12]}; +Canal 3 "
        "rows only, owner ruling 2026-09-26 'CT only'). Every leg verified by "
        "docs/handoffs/neiso118/shard_check.py at composition. Zero LP in the parent. "
        f"Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard launched; "
        f"record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"neiso-118 (2026-09-26): this run's own solved years {years}. "
            f"offer_curve_by_group (bare COAL entry excluded, folded by COAL-SUB) SHA-256 {sha} "
            f"equals keeper {KEEPER_ID}'s; no band moved and nothing was swept (rule 1 (c))."
        )
    gov["structural_delta"] = {
        "flips": list(FLIPS),
        "data_rederive": CT_ARTIFACT,
        "free_parameters_added": 0,
        "basis": (
            "rule 14 [R-ACCURATE] / rule 23 [R-FROZEN-DERIVE]: the CT derive's union_fleet kept "
            "each unit's latest-vintage record, so Canal 3 (1599; CT_PEAKER 2019-2022, oil "
            "2023-2025) never entered the measured population and 2019 priced it at eGRID-2019's "
            "boundary-broken 4.14 MMBtu/MWh (CAMPD partial-year heat input over full-year EIA-923 "
            "generation). The class-preserving union re-derive adds only Canal 3 (pooled CAMPD "
            "net 10.76); every other artifact row is byte-identical. Re-derived for a membership "
            "CODE defect, never because a residual moved."
        ),
        "control": f"the committed keeper {KEEPER} (rule 29(b) form 4); G-DRIFT {PRECOMMIT} s4",
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["neiso118"] = {
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
