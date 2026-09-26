"""Emit the SPP-86 calibration attestation for the composed 2019-2025 arm bundle ``spp86_arm_span``.

SPP-86 (``docs/handoffs/PRECOMMIT-spp-86-coal-extract-basis-2026-09-26.md``) replays SPP's keeper
``spp85_arm_span`` recipe one year per shard (rule 36) with exactly one registered ``ScenarioConfig``
boolean added, ``unit_outage_coal_extract_basis_share``. ``replay_keeper --out-dir`` does not propagate
``calibration_attestation.json``, so without this the composite scores C6 ``UNATTESTED`` for a plumbing
reason. The keeper's governance block is inherited; only the mechanism record and the held-years
statement are replaced.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
``offer_curve_by_group`` is asserted byte-identical to the keeper's on every year (rule 1 condition (c)).

Usage:
    python scripts/gen_spp86_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-86-coal-extract-basis-2026-09-26.md"
FINDING = "docs/handoffs/FINDING-spp-86-coal-floor-conduct-2026-09-26.md"
RESULT = "docs/handoffs/RESULT-spp-86-coal-extract-basis-2026-09-26.md"
PINNED = "d72e5f107a6fe7ca59f94307f37b239e1a48c14f"
COMPOSITE = "spp86_arm_span"
KEEPER = "spp85_arm_span"
KEEPER_ID = "2026-09-26-spp-85-netload-mask"
ARM = "unit_outage_coal_extract_basis_share"


def _offer_sha(cfg: dict) -> str:
    # replay_keeper translates a keeper's bare "COAL" key to its subclasses (the coal-sub
    # refactor), so the bare key is excluded from the identity; the subclass bands are compared.
    oc = {
        k: v for k, v in (cfg.get("offer_curve_by_group") or {}).items() if k != "COAL"
    }
    blob = json.dumps(oc, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _scenario(path: Path) -> dict:
    return json.loads(path.read_text())["scenario_config"]


def main() -> int:
    """Write the composite's attestation from the keeper's."""
    bundle = CAL / COMPOSITE
    att = json.loads((CAL / KEEPER / "calibration_attestation.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    ksha = {_offer_sha(_scenario(CAL / KEEPER / f"run_config_{y}.json")) for y in years}
    if len(ksha) != 1:
        raise SystemExit(f"keeper years disagree on offer_curve_by_group: {ksha}")
    for y in years:
        sc = _scenario(bundle / f"run_config_{y}.json")
        if _offer_sha(sc) not in ksha:
            raise SystemExit(f"{y}: offer_curve_by_group moved: {_offer_sha(sc)}")
        if sc.get(ARM) is not True:
            raise SystemExit(f"{y}: {ARM} is not True")
    sha = ksha.pop()
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"SPP-86 (2026-09-26) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        f"ONE YEAR PER SHARD (rule 36), with exactly one registered ScenarioConfig boolean {ARM} set "
        "True: the coal bins' unit-outage removed share taken on the extract's OWN capacity basis "
        "(nyiso-196's _extract_basis_index construction widened from the CC groups to the coal family), "
        "so a single-unit plant fully out reads exactly 1.0 (Holcomb 108 read 0.97). Every leg verified "
        "by scripts/probes/_spp86_shard_check.py (recipe diff vs the committed keeper + six extract "
        "sha256 + resolved path) and again by scripts/probes/_rspp_compose.py --require before "
        "composition. NO control solve: G-DRIFT all-INERT, rule 29(b) form 4, the committed keeper is "
        f"the control. Zero LP in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard launched; "
        f"phase 0 {FINDING}; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-86 (2026-09-26): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; this lane passed one "
            "input-correction --set flag. No band, class or value moved and nothing was swept "
            "(rule 1 condition (c)). ONE config across every scored year (condition (b))."
        )
    mech = dict(gov.get("mechanism_armed") or {})
    fields = dict(mech.get("fields") or {})
    fields[ARM] = True
    gov["mechanism_armed"] = {
        "fields": fields,
        "free_parameters_added": 0,
        "inherited": {k: v for k, v in mech.items() if k != "fields"},
        "level": (
            "measured: the SAME CAMPD unit-outage extracts (sha256 pinned), each coal row's removed "
            "share = unit_capacity_mw / the extract's own basis (the row's plant_capacity_mw at a "
            "single-group facility = the published unit_pct_of_plant; else the coal group's "
            "distinct-unit sum)"
        ),
        "basis": (
            "rule 14 [R-ACCURATE]: one construction for numerator and denominator of one share; "
            "direction checked against SPP's published hourly coal outage (the keeper's excess over it "
            "falls 0.19-0.32 GW), never a price residual; no frozen setting changed (rule 23)"
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: a scope widening of the existing extract-basis construction, not a "
            "new share; CC and coal scopes disjoint; no window added, no floor created (the incumbent "
            "coal must-run floor follows availability)"
        ),
        "control": (
            "the committed keeper bundle (rule 29(b) form 4; G-DRIFT all-INERT, "
            f"{PRECOMMIT} section 3)"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["spp86"] = {"result": RESULT, "composed_from_years": years}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
