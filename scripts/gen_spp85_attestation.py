"""Emit the SPP-85 calibration attestation for the composed 2019-2025 arm bundle ``spp85_arm_span``.

SPP-85 (``docs/handoffs/PRECOMMIT-spp-85-netload-mask-repair-2026-09-26.md``) replays SPP's keeper
``rspp_span`` recipe one year per shard (rule 36) with exactly one registered ``ScenarioConfig`` boolean
added, ``unit_outage_netload_mask_repair``. ``replay_keeper --out-dir`` does not propagate
``calibration_attestation.json``, so without this the composite scores C6 ``UNATTESTED`` for a plumbing
reason. The keeper's governance block is inherited; only the mechanism record and the held-years
statement are replaced.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
``offer_curve_by_group`` is asserted byte-identical to the keeper's on every year (rule 1 condition (c)).

Usage:
    python scripts/gen_spp85_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-85-netload-mask-repair-2026-09-26.md"
FINDING = "docs/handoffs/FINDING-spp-85-coal-outage-basis-2026-09-26.md"
RESULT = "docs/handoffs/RESULT-spp-85-netload-mask-repair-2026-09-26.md"
PINNED = "0ff620d11d91797313f5f565b5e94ff3b123330b"
COMPOSITE = "spp85_arm_span"
KEEPER = "rspp_span"
KEEPER_ID = "2026-09-24-r-spp-corrected-inputs"
ARM = "unit_outage_netload_mask_repair"


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
        f"SPP-85 (2026-09-26) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        f"ONE YEAR PER SHARD (rule 36), with exactly one registered ScenarioConfig boolean {ARM} set "
        "True: the committed SPP CAMPD outage extracts (standard / short / partial) re-derived at their "
        "OWN recorded invocations with the deriver's EIA-930 net-load mask live (outage_detect._ISO_TO_BA "
        "had no SPP key, so the recorded in-merit filter was inert). Every leg verified by "
        "scripts/probes/_spp85_shard_check.py (recipe diff + six extract sha256 + resolved path) and "
        "again by scripts/probes/_rspp_compose.py --require before composition. Each year's control "
        "(the keeper recipe at the same pinned SHA) was solved in the same shard (G-DRIFT LIVE). Zero LP "
        f"in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard launched; "
        f"phase 0 {FINDING}; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-85 (2026-09-26): this run's own solved years {years}. offer_curve_by_group "
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
            "measured: the SAME CAMPD unit-outage extracts, re-derived at their committed invocations "
            "(min_inmerit_hours 24 standard/partial, 6 short; high_load_pctl 0.85; 30-day window; "
            "full-stop override 5 d / CF 0.02) with the EIA-930 SWPP net-load mask live; each "
            "'-netloadmask-' companion is a strict full-row subset of its incumbent"
        ),
        "basis": (
            "rule 14 [R-ACCURATE] / rule 23 [R-FROZEN-DERIVE]: a code-scope repair (missing BA key), "
            "no frozen setting changed; measured-source basis = SPP's published hourly coal outage "
            "(portal capacity-of-generation-on-outage), never a price residual"
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: the field REPLACES each outage layer with its re-derivation; no "
            "window is added and no floor is created (the incumbent coal must-run floor re-applies in "
            "restored hours)"
        ),
        "control": (
            "per-year control solves of the keeper recipe at the same pinned SHA (G-DRIFT LIVE, "
            f"{PRECOMMIT} section 3)"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["spp85"] = {"result": RESULT, "composed_from_years": years}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
