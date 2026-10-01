"""Emit the SPP-104 calibration attestation for the composed 2019-2025 bundle ``spp104_arm_span``.

SPP-104 (``docs/records/spp/PRECOMMIT-spp-104-ct-lole-efor-2026-09-30.md``) replays SPP's keeper
``2026-09-28-spp-100-chp-scope`` one year per shard (rule 36) with one field armed:
``spp_ct_lole_efor`` (SPP's own LOLE-study EFOR replaces the CT_PEAKER WEFOR). Adapted
from ``gen_spp102_attestation.py``: the keeper's attestation is inherited, the offer curve is
verified byte-identical per year, every other scenario field is verified unmoved, and the field is
recorded under ``governance.mechanism_armed``.

Usage::

    python scripts/gen_spp104_attestation.py
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
PRECOMMIT = "docs/records/spp/PRECOMMIT-spp-104-ct-lole-efor-2026-09-30.md"
RESULT = "docs/records/spp/RESULT-spp-104-ct-lole-efor-2026-09-30.md"
PINNED = "264dbb2af75fdd73f3ff5450bef110bce37ebff8"
COMPOSITE = "spp104_arm_span"
KEEPER = "spp100_arm_span"
KEEPER_ID = "2026-09-28-spp-100-chp-scope"
ARM = {"spp_ct_lole_efor": True}


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
        f"SPP-104 (2026-09-30) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with ONE field armed: spp_ct_lole_efor (new, default off, SPP-only: "
        "SPP's own 2023 LOLE Report Tables 9/10 seasonal natural-gas EFOR by unit size, capacity-weighted per "
        "plant over the EIA-860 unit roster, REPLACES the CT_PEAKER statistical WEFOR, rule 19). Built on the "
        "owner decision cards 'Build LOLE-EFOR CT swap' and 'Solve all 7 years' (2026-09-30). Every leg "
        "verified by scripts/probes/_spp104_shard_check.py (in the shard and again in the parent) and by "
        "scripts/probes/_rspp_compose.py --require before composition. NO control solve: rule 29(b) form 4, "
        f"the committed keeper is the control (G-DRIFT all INERT, Addenda A/B). Zero LP in the parent. "
        f"Pre-registered in {PRECOMMIT} (pin {PINNED[:8]}) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-104 (2026-09-30): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; the lane's one --set field "
            "arms an availability input (not a price channel). No "
            "band, class or value moved and nothing was swept (rule 1 condition (c)). ONE config across "
            "every scored year (condition (b))."
        )
    ma = gov.get("mechanism_armed")
    if isinstance(ma, dict) and isinstance(ma.get("fields"), dict):
        ma["fields"].update(ARM)
    gov["mechanism_changes_spp104"] = {
        "fields": ARM,
        "free_parameters_added": 0,
        "parameters": (
            "constants.SPP_LOLE_GAS_EFOR_BY_SIZE = 2023 SPP LOLE Report s4.3.2 Tables 9/10 (GADS 2015-2022); "
            "calendar-hour basis = SERVM's own ttf = ttr(1-EFOR)/EFOR steady state (report Appendix A)"
        ),
        "basis": (
            "rule 13 [R-MEASURED] / rule 14: SPP's own published forced-outage rate replaces the national "
            "GADS WEFOR x wefor_multiplier for CT_PEAKER; rule 19: replaces, never stacks; rule 25: SPP-only"
        ),
        "prereg": f"{PRECOMMIT}, merged BEFORE any shard was launched; pin {PINNED}",
    }
    att["spp104"] = {"result": RESULT, "composed_from_years": years, "arm": ARM}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
