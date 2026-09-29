"""Emit the SPP-100 calibration attestation for the composed 2019-2025 bundle ``spp100_arm_span``.

SPP-100 (``docs/handoffs/PRECOMMIT-spp-100-chp-conduct-scope-2026-09-28.md``) replays SPP's keeper
``2026-09-28-spp-99-remap-rederive`` one year per shard (rule 36) with two fields armed:
``chp_steam_floor_p25`` (the existing CHP steam-level swap) and ``chp_steam_floor_conduct_scope``
(the swap withheld from metered hosts metered on in <= half their hours). Adapted from
``gen_spp99_attestation.py``: the keeper's attestation is inherited, the offer curve is verified
byte-identical per year, every other scenario field is verified unmoved, and the two fields are
recorded under ``governance.mechanism_armed``.

Usage::

    python scripts/gen_spp100_attestation.py
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
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-100-chp-conduct-scope-2026-09-28.md"
RESULT = "docs/handoffs/RESULT-spp-100-chp-conduct-scope-2026-09-28.md"
PINNED = "11b72265e362a07912b2c2364a5708805697e58e"
COMPOSITE = "spp100_arm_span"
KEEPER = "spp99_remap_span"
KEEPER_ID = "2026-09-28-spp-99-remap-rederive"
ARM = {"chp_steam_floor_p25": True, "chp_steam_floor_conduct_scope": True}


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
        f"SPP-100 (2026-09-28) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with TWO fields armed: chp_steam_floor_p25 (the existing CHP "
        "steam-level swap: the tranche artifact's measured steam_level_cf supersedes the p2 floor) and "
        "chp_steam_floor_conduct_scope (new, default off: a metered CHP host takes the swap only if its "
        "pooled on-frequency steam_level_cf / median_cf exceeds constants.CHP_STEAM_ALLHOURS_MIN_ON_FRAC "
        "= 0.5, D-4's own conduct bar applied ex ante). The re-open route the owner named for SPP's "
        "chp_steam_following R cell (2026-09-24). Rule 17 / rule 14, never the residual. Every leg verified "
        "by scripts/probes/_spp100_shard_check.py (in the shard and again in the parent) and by "
        "scripts/probes/_rspp_compose.py --require before composition. NO control solve: rule 29(b) form 4, "
        f"the committed keeper is the control (G-DRIFT all INERT). Zero LP in the parent. Pre-registered in "
        f"{PRECOMMIT} (round-2 pin {PINNED[:8]}, Addendum A) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-100 (2026-09-28): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; the lane's two --set fields "
            "arms two CHP steam-floor structural gates (not price channels). No "
            "band, class or value moved and nothing was swept (rule 1 condition (c)). ONE config across "
            "every scored year (condition (b))."
        )
    ma = gov.get("mechanism_armed")
    if isinstance(ma, dict) and isinstance(ma.get("fields"), dict):
        ma["fields"].update(ARM)
    gov["mechanism_changes_spp100"] = {
        "fields": ARM,
        "free_parameters_added": 0,
        "bar": "constants.CHP_STEAM_ALLHOURS_MIN_ON_FRAC = 0.5 (D-4 per-unit conduct rider's median "
        "test applied ex ante; SPP partition identical for any bar in (0.25, 0.98))",
        "basis": (
            "rule 17 [R-FLOOR-WINDOW] / rule 14 [R-ACCURATE]: Eastman 55176 and Black Hawk 55064 run flat "
            "on their CAMPD meters (on 92-100 % of hours) and are floored at their measured steam level; "
            "Lake Road 2098 (metered on 5.5-27.7 %) keeps its p2 floor, removing SPP-75's D-4 FAIL"
        ),
        "prereg": f"{PRECOMMIT}, merged BEFORE any shard was launched; round-2 pin {PINNED}",
    }
    att["spp100"] = {"result": RESULT, "composed_from_years": years, "arm": ARM}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
