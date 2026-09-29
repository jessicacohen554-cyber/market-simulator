"""Emit the SPP-102 calibration attestation for the composed 2019-2025 bundle ``spp102_arm_span``.

SPP-102 (``docs/handoffs/PRECOMMIT-spp-102-commitment-posture-2026-09-29.md``) replays SPP's keeper
``2026-09-28-spp-100-chp-scope`` one year per shard (rule 36) with one field armed:
``spp_commitment_posture`` (the per-plant relaxed commitment state with min-up / min-down). Adapted
from ``gen_spp100_attestation.py``: the keeper's attestation is inherited, the offer curve is
verified byte-identical per year, every other scenario field is verified unmoved, and the field is
recorded under ``governance.mechanism_armed``.

Usage::

    python scripts/gen_spp102_attestation.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.scenarios import _CACHE_KEY_RETIRED_FIELDS  # noqa: E402

CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-102-commitment-posture-2026-09-29.md"
RESULT = "docs/handoffs/RESULT-spp-102-commitment-posture-2026-09-29.md"
PINNED = "62ac90e26c5360cb96ce422be82ba50279b79cc8"
COMPOSITE = "spp102_arm_span"
KEEPER = "spp100_arm_span"
KEEPER_ID = "2026-09-28-spp-100-chp-scope"
ARM = {"spp_commitment_posture": True}


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
        for k, v in ARM.items():
            if sc.get(k) != v:
                raise SystemExit(f"{y}: {k} = {sc.get(k)!r}, expected {v!r}")
        ksc = _scenario(CAL / KEEPER / f"run_config_{y}.json")
        moved = sorted(
            k
            for k in ksc
            if k != "offer_curve_by_group"
            and k not in ARM
            and sc.get(k) != ksc.get(k)
            # a field deleted since the keeper (rule 26) is absent from the leg; it
            # is inert iff the keeper carried it at its frozen retired value
            and not (
                k not in sc
                and k in _CACHE_KEY_RETIRED_FIELDS
                and ksc[k] == _CACHE_KEY_RETIRED_FIELDS[k]
            )
        )
        if moved:
            raise SystemExit(f"{y}: scenario_config moved vs keeper: {moved}")
    sha = ksha.pop()
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"SPP-102 (2026-09-29) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with ONE field armed: spp_commitment_posture (new, default off, "
        "SPP-only: the ercot_commitment_posture standalone construction pooled PER CC PLANT, plus min-up "
        "15 h (SPP CAMPD CC run-length p25) and min-down 8 h (SPP MMU ASOM gas) coupling rows; measured "
        "min-load 0.209; NREL class startup; the P1 amortized startup markup zeroed on postured members, "
        "rule 19). Built on the owner decision card 'Build relaxed-UC engine' (2026-09-29). Every leg "
        "verified by scripts/probes/_spp102_shard_check.py (in the shard and again in the parent) and by "
        "scripts/probes/_rspp_compose.py --require before composition. NO control solve: rule 29(b) form 4, "
        f"the committed keeper is the control (G-DRIFT all INERT). Zero LP in the parent. Pre-registered in "
        f"{PRECOMMIT} (pin {PINNED[:8]}, Addendum A) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-102 (2026-09-29): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; the lane's one --set field "
            "arms a commitment-state structure (not a price channel). No "
            "band, class or value moved and nothing was swept (rule 1 condition (c)). ONE config across "
            "every scored year (condition (b))."
        )
    ma = gov.get("mechanism_armed")
    if isinstance(ma, dict) and isinstance(ma.get("fields"), dict):
        ma["fields"].update(ARM)
    gov["mechanism_changes_spp102"] = {
        "fields": ARM,
        "free_parameters_added": 0,
        "parameters": (
            "mlf 0.209 = constants.SPP_GAS_BRIDGE_MIN_LOAD_FRAC['gas_cc'] (SPP CAMPD, SPP-44); min-up 15 h = "
            "SPP_GAS_BRIDGE_MIN_RUN_HOURS['gas_cc'] (SPP CAMPD run-length p25); min-down 8 h = "
            "SPP_POSTURE_MIN_DOWN_HOURS (SPP MMU ASOM 2024 gas); startup = NREL/SR-5500-55433 class tables"
        ),
        "basis": (
            "rule 1 [R-STRUCT] / rule 18 [R-PHYSICS]: commitment state with measured unit physics; "
            "rule 19: one posture construction (ERCOT's), P1 startup markup zeroed on members so the start "
            "is charged once; not a floor (no D-2 id)"
        ),
        "prereg": f"{PRECOMMIT}, merged BEFORE any shard was launched; pin {PINNED}",
    }
    att["spp102"] = {"result": RESULT, "composed_from_years": years, "arm": ARM}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
