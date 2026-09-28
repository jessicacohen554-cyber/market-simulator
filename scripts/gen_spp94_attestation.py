"""Emit the SPP-94 calibration attestation for the composed 2019-2025 arm bundle ``spp94_arm_span``.

SPP-94/95 (``docs/handoffs/PRECOMMIT-spp-94-curtail-rows-2026-09-27.md``) replays SPP's keeper
``spp86_arm_span`` recipe one year per shard (rule 36) with NO flag changed. The only delta is a DATA
change: SPP's own published 2020 (244 MW, ASOM 2022 p. 53) and 2021 (725 MW, ASOM 2021 p. 60) average
hourly wind curtailment rows in ``data/raw/spp-hsl/spp_wind_curtailment_annual.csv`` (sha256 dd6c2898...),
which the armed ``vre_reference_rate_year_own`` seam now reads instead of the 9.65 % 2023-25 mean.
``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``, so without this the
composite scores C6 ``UNATTESTED`` for a plumbing reason. The keeper's governance block is inherited;
only the attestation line and the held-years statement are replaced.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
Every leg's ``scenario_config`` is asserted identical to the keeper's (bare ``COAL`` offer key excluded,
see ``_offer_sha``), so ``offer_curve_by_group`` is byte-identical on every year (rule 1 condition (c)).

Usage:
    python scripts/gen_spp94_attestation.py
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
PRECOMMIT = "docs/handoffs/PRECOMMIT-spp-94-curtail-rows-2026-09-27.md"
FINDING = "docs/handoffs/FINDING-spp-94-curtail-rows-2026-09-28.md"
RESULT = "docs/handoffs/RESULT-spp-95-curtail-rows-2026-09-28.md"
PINNED = "020bb1c5cb38b73da686dc4e83d1620c415b1437"
COMPOSITE = "spp94_arm_span"
KEEPER = "spp86_arm_span"
KEEPER_ID = "2026-09-26-spp-86-coal-extract"
DATA = "data/raw/spp-hsl/spp_wind_curtailment_annual.csv"


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
        f"SPP-95 (2026-09-28) -- keeper {KEEPER_ID}'s recipe replayed via scripts/replay_keeper.py, "
        "ONE YEAR PER SHARD (rule 36), with NO flag changed and every leg's scenario_config identical "
        f"to the keeper's. The one delta is DATA: {DATA} gains SPP's own published 2020 (244 MW, ASOM "
        "2022 p. 53) and 2021 (725 MW, ASOM 2021 p. 60) average hourly wind curtailment rows, so the "
        "armed year-own seam (vre_reference_rate_year_own) applies 2.55 % / 6.37 % instead of the "
        "9.65 % 2023-25 mean in those two years (rule 14 [R-ACCURATE]). Every leg verified by "
        "scripts/probes/_spp94_shard_check.py and again by scripts/probes/_rspp_compose.py --require "
        "before composition. NO control solve: rule 29(b) form 4, the committed keeper is the control. "
        f"Zero LP in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard "
        f"launched; phase 0 {FINDING}; record {RESULT}."
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
    gov["data_corrections"] = [
        {
            "path": DATA,
            "rows": {
                "2020": "244 MW (ASOM 2022 p. 53)",
                "2021": "725 MW (ASOM 2021 p. 60)",
            },
            "free_parameters_added": 0,
            "basis": (
                "rule 14 [R-ACCURATE]: SPP's own published measurement replaces the 2023-25 mean "
                "estimate; same average-hourly-MW wind basis as every committed row; never a residual"
            ),
            "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
        }
    ]
    att["spp94"] = {"result": RESULT, "composed_from_years": years}
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
