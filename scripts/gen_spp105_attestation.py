"""Emit the SPP-105 calibration attestation for a composed 2019-2025 arm bundle ``spp105<A|B>_span``.

SPP-105 (``docs/handoffs/PRECOMMIT-spp-105-gas-family-outage-2026-09-30.md``) replays SPP's keeper
``2026-09-28-spp-100-chp-scope`` one year per shard (rule 36) with ONE gas-family outage carrier:
arm A = ``wefor_residual 0.0`` + ``wefor_residual_groups`` CC/ST (existing fields); arm B =
``spp_gas_crow_residual_outage``. Adapted from ``gen_spp104_attestation.py``: the keeper's
attestation is inherited, the offer curve is verified byte-identical per year, every other scenario
field is verified unmoved, and the arm's fields are recorded under ``governance.mechanism_armed``.

Usage::

    python scripts/gen_spp105_attestation.py --arm B
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.scenarios import _CACHE_KEY_RETIRED_FIELDS  # noqa: E402

CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-105-gas-family-outage-2026-09-30.md"
RESULT = "docs/handoffs/RESULT-spp-105-gas-family-outage-2026-09-30.md"
PINNED = "5e0599c86c5e12c7f75c86588e1a561ddd551080"
KEEPER = "spp100_arm_span"
KEEPER_ID = "2026-09-28-spp-100-chp-scope"
ARMS = {
    "A": {
        "wefor_residual": 0.0,
        "wefor_residual_groups": ["CC_CHP", "CC_REGULAR", "ST_CHP", "ST_GAS"],
    },
    "B": {"spp_gas_crow_residual_outage": True},
}
DESCRIBE = {
    "A": (
        "carrier A: wefor_residual 0.0 with wefor_residual_groups CC_REGULAR/CC_CHP/ST_GAS/ST_CHP "
        "(existing fields) removes the statistical WEFOR from the CAMPD-covered gas classes (rule 19 repair)"
    ),
    "B": (
        "carrier B: spp_gas_crow_residual_outage (new, default off, SPP-only) replaces every gas row's "
        "statistical WEFOR/POF with SPP's published hourly Natural Gas outage minus the CAMPD event MW, "
        "allocated on the incumbent class key; DECLARED rule-13 pin in 41-94 % of hours (owner override)"
    ),
}


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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    arm = ap.parse_args().arm
    ARM = ARMS[arm]
    bundle = CAL / f"spp105{arm}_span"
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
        f"SPP-105 arm {arm} (2026-09-30) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        f"ONE YEAR PER SHARD (rule 36), with ONE carrier: {DESCRIBE[arm]}. Built on the owner decision card "
        "'Build carrier a and b' (2026-09-30). Every leg verified by scripts/probes/_spp105_shard_check.py "
        "(in the shard and again in the parent) and by scripts/probes/_rspp_compose.py --require before "
        "composition. NO control solve: rule 29(b) form 4, the committed keeper is the control (G-DRIFT all "
        "INERT, Addendum A). Zero LP in the parent. "
        f"Pre-registered in {PRECOMMIT} (pin {PINNED[:8]}) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-105 (2026-09-30): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; the lane's one --set field "
            "arms an availability input (not a price channel). No "
            "band, class or value moved and nothing was swept (rule 1 condition (c)). ONE config across "
            "every scored year (condition (b))."
        )
    ma = gov.get("mechanism_armed")
    if isinstance(ma, dict) and isinstance(ma.get("fields"), dict):
        ma["fields"].update(ARM)
    gov[f"mechanism_changes_spp105{arm}"] = {
        "fields": ARM,
        "free_parameters_added": 0,
        "parameters": (
            "arm A: 0.0 is the carrier's definition (no statistical residual), not a selected value"
            if arm == "A"
            else "data/raw/spp-gen-outage (SPP portal capacity-of-generation-on-outage, sha c2baf1c2); "
            "allocation key = the incumbent statistical class rates"
        ),
        "basis": DESCRIBE[arm],
        "prereg": f"{PRECOMMIT}, merged BEFORE any shard was launched; pin {PINNED}",
    }
    att[f"spp105{arm}"] = {"result": RESULT, "composed_from_years": years, "arm": ARM}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
