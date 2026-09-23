"""Emit the hydro-5 calibration attestations for the three promoted hydro arms.

hydro-5 arms exactly ONE registered ``ScenarioConfig`` boolean on each ISO's
keeper recipe, solved one year per shard (rule 36) and composed at zero LP:

* SPP   ``hydro_min_flow_floor`` — ``hydro5_spp_floor_span`` (2023-2025, on
  ``spp71_ensemble_span``) and ``hydro5_spp_floor_rung`` (2019-2022, on
  ``spp71_ensemble_rung``);
* NEISO ``hydro_ror_split`` — ``hydro5_neiso_ror_span`` (2020-2025, on
  ``neiso112_mer_span``);
* MISO  ``hydro_ror_split`` — ``hydro5_miso_ror_span`` (2020-2025, on
  ``miso264_anchor_span``).

**Why this exists rather than the shared helper** — the reason
``gen_spp71_attestation.py`` records: ``replay_keeper --out-dir`` does not
propagate ``calibration_attestation.json``, so without this every composite
scores C6 ``UNATTESTED`` for a plumbing reason, not a governance one.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` /
24 ``[R-REGISTRY]``). Each flag is a registered field; the RoR classifier is
categorical-external and its level is each plant's own monthly budget; the
floor's level is the ISO's own measured EIA-930 Q95 with the frozen
``HYDRO_MIN_FLOW_PERCENTILE``. ``offer_curve_by_group`` is asserted
byte-identical to the keeper's, so the rule-1 authorized price-tuning channel
was not touched. The keeper's governance block is inherited; only the
mechanism record and the held-years statement are added. The DOF ledger is
re-seeded afterwards by ``build_dof_ledger.py`` and must match the keeper's
entry and residual counts.

Usage:
    python scripts/gen_hydro5_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/PRECOMMIT-hydro-5-2026-09-22.md"
RESULT = "docs/RESULT-hydro-5-2026-09-22.md"
PINNED = "fda9ece3d854d747a263f3078285df96fb4f0fe1"

#: (composite, keeper bundle, keeper run id, flag)
TARGETS = (
    (
        "hydro5_spp_floor_span",
        "spp71_ensemble_span",
        "2026-09-22-spp-71-ensemble-syncfloor",
        "hydro_min_flow_floor",
    ),
    (
        "hydro5_spp_floor_rung",
        "spp71_ensemble_rung",
        "2026-09-22-spp-71-rung-ensemble",
        "hydro_min_flow_floor",
    ),
    (
        "hydro5_neiso_ror_span",
        "neiso112_mer_span",
        "2026-09-19-neiso112-mer-year-isolated",
        "hydro_ror_split",
    ),
    (
        "hydro5_miso_ror_span",
        "miso264_anchor_span",
        "2026-09-20-miso-264-anchor-vintage",
        "hydro_ror_split",
    ),
)

_LEVEL = {
    "hydro_min_flow_floor": (
        "the ISO's OWN measured EIA-930 NG:WAT monthly Q95 (frozen "
        "HYDRO_MIN_FLOW_PERCENTILE, the mirror of the envelope's 95), allocated "
        "per plant pro-rata by its own monthly budget and clipped to the month's "
        "average power. SPP's NG:WAT admissibility was MEASURED (0 hours above the "
        "3,103.5 MW conventional nameplate, 0 negative hours, 2019-2025)"
    ),
    "hydro_ror_split": (
        "NO LEVEL PARAMETER. The classifier (ORNL EHA FY2024 Mode + the HILARRI / "
        "Corps-dam completion) is categorical and was reviewed on this BA's own "
        "labelled subset (rule 25); a run-of-river plant dispatches flat at its own "
        "monthly budget / hours"
    ),
}


def _offer_sha(bundle: Path) -> str:
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    blob = json.dumps(cfg.get("offer_curve_by_group") or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def write(comp: str, keeper: str, keeper_id: str, flag: str) -> None:
    """Write one composite's attestation from its keeper's."""
    bundle, kb = CAL / comp, CAL / keeper
    att = json.loads((kb / "calibration_attestation.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    sha, ksha = _offer_sha(bundle), _offer_sha(kb)
    if sha != ksha:
        raise SystemExit(f"{comp}: offer_curve_by_group {sha} != keeper {ksha}")
    sc = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    if sc.get(flag) is not True:
        raise SystemExit(f"{comp}: {flag} is not armed")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"hydro-5 (2026-09-22) -- keeper {keeper_id}'s recipe replayed UNCHANGED via "
        f"scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), with exactly one "
        f"registered ScenarioConfig flag added: {flag}=true. Every leg was verified "
        "keeper-recipe-plus-one-flag by scripts/probes/_hydro5_shard_check.py and again "
        "by scripts/probes/_hydro5_compose_span.py before composition. Zero LP in the "
        f"parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any "
        f"shard launched; record {RESULT}. Promoted on the owner's standing ruling "
        "(2026-09-23): 'Is this a recommended keeper candidate? If so plz promote.'"
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"hydro-5 (2026-09-22): this run's own solved years {years}. "
            f"offer_curve_by_group SHA-256 {sha} is byte-identical to keeper "
            f"{keeper_id}'s; this lane passed only --set {flag}=true. No band, class "
            "or value moved and nothing was swept (rule 1 condition (c))."
        )
    gov["mechanism_armed"] = {
        "field": flag,
        "value": True,
        "level": _LEVEL[flag],
        "free_parameters_added": 0,
        "basis": (
            "rule 1 [R-STRUCT] / rule 14 [R-ACCURATE] structural repair: the budget LP "
            "gave every hydro plant full within-month shaping freedom with no lower "
            "bound, so the fleet parked at exactly 0 MW for up to 37 % of the year "
            "and banked water onto peaks; the measured fleet never goes near zero"
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: hydro_min_flow_floor and hydro_ror_split are one "
            "family and were tested as SEPARATE arms, never stacked; this run arms one"
        ),
        "window": "all 24 hours by physics (D-4 MECH_HYDRO_MIN_FLOW / MECH_HYDRO_ROR_FLAT rows)",
        "control": (
            f"the committed keeper {keeper} (rule 29(b) form 4); G-DRIFT "
            f"{PRECOMMIT} section 6 classified every solve-path hunk INERT"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["hydro5"] = {
        "result": RESULT,
        "gates": (
            "G1 live in every year; G2 annual hydro energy within 0.1 % in every year; "
            "G3 hours-at-0 -> 0, top-decile share and within-month daily CV down in "
            "every year; G4 zero PASS->FAIL flips on C1/C2/C3a/C3b. Misses reported at "
            "full magnitude in the RESULT (SPP floor 2019 G1 9.3 MW nameplate clip; "
            "SPP floor 2025 May G2 +0.276 %)."
        ),
    }
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )


def main() -> int:
    """CLI: write every composite that exists."""
    n = 0
    for comp, keeper, keeper_id, flag in TARGETS:
        if (CAL / comp / "run_config.json").exists():
            write(comp, keeper, keeper_id, flag)
            n += 1
    return 0 if n else 1


if __name__ == "__main__":
    raise SystemExit(main())
