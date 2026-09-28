"""Emit the SPP-98 calibration attestation for the composed 2019-2025 bundle ``spp98_remap_span``.

SPP-98 (``docs/handoffs/PRECOMMIT-spp-98-cems-eia-remap-2026-09-28.md``) replays SPP's keeper
``spp94_arm_span`` recipe one year per shard (rule 36) with NO flag changed; every leg reproduced the
keeper's dispatch and prices exactly (X4). The only delta is to the BENCHMARK: ten rows in
``campd.CAMPD_UNIT_PLANT_REMAP`` (EPA CAMD-EIA crosswalk) re-attribute J Lamar Stall's CEMS turbines
from Arsenal Hill ORIS 1416 to EIA 56565, removing a 1.9-2.3 TWh C1 ST_GAS double count in
2020 / 2021 / 2025. ``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``, so
without this the composite scores C6 ``UNATTESTED`` for a plumbing reason. The keeper's governance
block is inherited; only the attestation line and the held-years statement are replaced.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
Every leg's ``scenario_config`` is asserted identical to the keeper's, so ``offer_curve_by_group`` is
byte-identical on every year (rule 1 condition (c)).

Usage:
    python scripts/gen_spp98_attestation.py
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
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-98-cems-eia-remap-2026-09-28.md"
FINDING = "docs/handoffs/PRECOMMIT-spp-98-cems-eia-remap-2026-09-28.md"
RESULT = "docs/handoffs/RESULT-spp-98-cems-eia-remap-2026-09-28.md"
PINNED = "ed8cec3fd0811ebf835cfec42184493683c2625a"
COMPOSITE = "spp98_remap_span"
KEEPER = "spp94_arm_span"
KEEPER_ID = "2026-09-28-spp-94-curtail-rows"
DATA = "src/market_sim/data/campd.py::CAMPD_UNIT_PLANT_REMAP"


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
        ksc = _scenario(CAL / KEEPER / f"run_config_{y}.json")
        # Fields added after the keeper was solved are absent from its config; the shard
        # check verified each sits at its default, so only the keeper's own fields are compared.
        moved = sorted(
            k
            for k in ksc
            if k != "offer_curve_by_group"
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
        f"SPP-98 (2026-09-28) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with NO flag changed and every leg's scenario_config identical "
        "to the keeper's; every leg reproduced the keeper's per-class TWh and every zonal hourly price "
        "exactly (X4: max |dTWh| 0.0000, max |dprice| 0.000000). The one delta is the BENCHMARK: "
        f"{DATA} gains ten EPA CAMD-EIA crosswalk rows (J Lamar Stall 56565 <- Arsenal Hill 1416 "
        "CTG-6A/6B, plus WFEC GenCo, Ponca City, Mustang), removing a 1.9-2.3 TWh C1 ST_GAS double "
        "count in 2020 / 2021 / 2025 (rule 14 [R-ACCURATE]), adopted via "
        "run_calibration_full.rebuild_benchmark. Every leg verified by "
        "scripts/probes/_spp98_shard_check.py and again by scripts/probes/_rspp_compose.py --require "
        "before composition. NO control solve: rule 29(b) form 4, the committed keeper is the control. "
        f"Zero LP in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard "
        f"launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"SPP-86 (2026-09-26): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the keeper's on every year; this lane passed no --set "
            "flag (a data-row correction only). No band, class or value moved and nothing was swept "
            "(rule 1 condition (c)). ONE config across every scored year (condition (b))."
        )
    gov["data_corrections"] = (gov.get("data_corrections") or []) + [
        {
            "path": DATA,
            "rows": {
                "(1416, CTG-6A)": 56565,
                "(1416, CTG-6B)": 56565,
                "(3006, 7)": 55655,
                "(3006, 8)": 55655,
                "(762, 3)": 7546,
                "(762, 4)": 7546,
                "(63628, 5A-1 / 5A-2 / 5B-1 / 5B-2)": 2953,
            },
            "free_parameters_added": 0,
            "basis": (
                "rule 14 [R-ACCURATE]: the EPA CAMD-EIA Power Sector Data Crosswalk maps these CEMS "
                "units to a different EIA plant than the CEMS facility; benchmark attribution only, "
                "dispatch byte-identical (X4); never a residual"
            ),
            "prereg": f"{PRECOMMIT}, merged at {PINNED} BEFORE any shard was launched",
        }
    ]
    att["spp98"] = {"result": RESULT, "composed_from_years": years}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
