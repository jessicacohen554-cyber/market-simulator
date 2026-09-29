"""Emit the SPP-99 calibration attestation for the composed 2019-2025 bundle ``spp99_remap_span``.

SPP-99 (``docs/handoffs/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md``) replays SPP's keeper
``spp98_remap_span`` recipe one year per shard (rule 36) with ONE field armed:
``campd_split_remap_companions`` (miso-280's mechanism, extended to SPP's plain tranche family). The
keeper reads four SPP CAMPD-derived artifacts that were derived before SPP-98's CEMS->EIA remap rows
existed; the flag selects their ``-splitremap-`` companions -- each the incumbent with only the remap
plants' lines replaced by the same deriver's lines under the remap (splice control PASS on all four).
``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``, so without this the
composite scores C6 ``UNATTESTED`` for a plumbing reason. The keeper's governance block is inherited.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
Every leg's ``scenario_config`` is asserted identical to the keeper's apart from the one flag, so
``offer_curve_by_group`` is byte-identical on every year (rule 1 condition (c)).

Usage:
    python scripts/gen_spp99_attestation.py
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
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-99-remap-rederive-2026-09-28.md"
RESULT = "docs/handoffs/RESULT-spp-99-remap-rederive-2026-09-28.md"
PINNED = "289d4baf7b0819e7d0b5279cb6ac71930e12ec09"
COMPOSITE = "spp99_remap_span"
KEEPER = "spp98_remap_span"
KEEPER_ID = "2026-09-28-spp-98-cems-remap"
ARM = {"campd_split_remap_companions": True}
COMPANIONS = {
    "data/raw/campd-unit-outages-netloadmask-splitremap-SPP.csv": "41ee31e0",
    "data/raw/campd-unit-outages-splitremap-SPP.csv": "8cd6dbd9",
    "data/raw/_processed-legacy/campd_cc_heat_rates-splitremap-SPP.csv": "c144ddd7",
    "data/raw/_processed-legacy/thermal_tranches-splitremap-SPP.csv": "92ed67de",
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
        f"SPP-99 (2026-09-28) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with ONE field armed: campd_split_remap_companions (miso-280's "
        "split-remap mechanism, extended to SPP's plain tranche family on the owner decision card "
        "'Extend miso-280 (Rec.)'; rule 19, no new field). It selects four -splitremap- companions of "
        "SPP CAMPD-derived artifacts (std net-load-masked and base outage extracts, measured CC heat "
        "rates, plain tranches), each the incumbent with only the SPP-98 remap plants' lines swapped for "
        "the same deriver's lines under the remap; splice control PASS on all four (derivers with the "
        "SPP rows stripped reproduce every incumbent byte-for-byte). Rule 23: the trigger is the "
        "attribution change, never a residual. Every leg verified by scripts/probes/_spp99_shard_check.py "
        "(in the shard and again in the parent) and by scripts/probes/_rspp_compose.py --require before "
        "composition. NO control solve: rule 29(b) form 4, the committed keeper is the control (G-DRIFT "
        f"all INERT). Zero LP in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before "
        f"any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-86 (2026-09-26): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; the lane's single --set "
            "is campd_split_remap_companions (an input-attribution selector, not a price channel). No "
            "band, class or value moved and nothing was swept (rule 1 condition (c)). ONE config across "
            "every scored year (condition (b))."
        )
    gov["data_corrections"] = (gov.get("data_corrections") or []) + [
        {
            "path": "campd_split_remap_companions -> " + ", ".join(COMPANIONS),
            "sha256_prefix": COMPANIONS,
            "free_parameters_added": 0,
            "basis": (
                "rule 14 [R-ACCURATE] / rule 23 [R-FROZEN-DERIVE]: SPP-98's CAMPD_UNIT_PLANT_REMAP rows "
                "reach the solve only through re-derived artifacts; each companion is a plant-scoped "
                "splice (scripts/data/build_campd_split_remap_companions.py, families stdbase / stdmask / "
                "cc / tranches) with a byte-for-byte splice control; never a residual"
            ),
            "prereg": f"{PRECOMMIT}, merged at {PINNED} BEFORE any shard was launched",
        }
    ]
    att["spp99"] = {"result": RESULT, "composed_from_years": years, "arm": ARM}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
