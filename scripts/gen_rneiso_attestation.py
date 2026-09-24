"""Emit the R-NEISO calibration attestation for the corrected-input composite.

R-NEISO (``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md``
§5.3.4) replays the NEISO keeper ``2026-09-22-hydro-5-neiso-ror``
(``hydro5_neiso_ror_span``) UNCHANGED except for eight registered
``ScenarioConfig`` input-correction flips, one year per shard (rule 36), composed
at zero LP into ``rneiso_span`` (2019-2025).

``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``
(the ``gen_spp71_attestation.py`` note), so without this the composite would
score C6 ``UNATTESTED`` for a plumbing reason. The keeper's governance block and
DOF ledger are inherited; **zero free parameters are added and none is re-cut**
(rules 21 / 24): every flip reads a measured or published input (EIA-860
vintage tables, eGRID, CAMPD CEMS) through a frozen derive, and
``offer_curve_by_group`` is asserted byte-identical to the keeper's, so the
rule-1 authorized price-tuning channel was not touched.

Usage:
    python scripts/gen_rneiso_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
COMPOSITE = "rneiso_span"
KEEPER = "hydro5_neiso_ror_span"
KEEPER_ID = "2026-09-22-hydro-5-neiso-ror"
PRECOMMIT = "docs/handoffs/r-neiso/PRECOMMIT-r-neiso-2026-09-24.md"
RESULT = "docs/handoffs/r-neiso/RESULT-r-neiso-2026-09-24.md"
PINNED = "c265c1c30ce0e51bffa5e0e5f5db76eafe54ae3e"
FLIPS = (
    "eia860_vintage_tracks_solve_year",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "mid_vintage_exit_carry",
    "partial_plant_exit_carry",
)


def _offer_sha(bundle: Path) -> str:
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    blob = json.dumps(cfg.get("offer_curve_by_group") or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def main() -> int:
    """Write the composite's attestation from the keeper's."""
    bundle, kb = CAL / COMPOSITE, CAL / KEEPER
    att = json.loads((kb / "calibration_attestation.json").read_text())
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    sha, ksha = _offer_sha(bundle), _offer_sha(kb)
    if sha != ksha:
        raise SystemExit(f"offer_curve_by_group {sha} != keeper {ksha}")
    for y in years:
        sc = json.loads((bundle / f"run_config_{y}.json").read_text())[
            "scenario_config"
        ]
        off = [f for f in FLIPS if sc.get(f) is not True]
        if off:
            raise SystemExit(f"{y}: flips not armed: {off}")
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"R-NEISO (2026-09-24) -- keeper {KEEPER_ID}'s recipe replayed UNCHANGED via "
        "scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), with eight registered "
        f"input-correction flips: {', '.join(FLIPS)}. Every leg verified by "
        "docs/handoffs/r-neiso/shard_check.py in its shard and again at composition. Zero LP "
        f"in the parent. Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard "
        f"launched; record {RESULT}. Owner instruction 2026-09-24: every backcast year runs on "
        "the year-correct EIA-860 vintage, plant-specific heat rates and granular CAMPD outages."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"R-NEISO (2026-09-24): this run's own solved years {years}. "
            f"offer_curve_by_group SHA-256 {sha} is byte-identical to keeper {KEEPER_ID}'s; "
            "no band, class or value moved and nothing was swept (rule 1 condition (c)). "
            "2019 is scored under the SAME config as every other year (condition (b))."
        )
    gov["inputs_corrected"] = {
        "flips": list(FLIPS),
        "free_parameters_added": 0,
        "basis": (
            "rule 14 [R-ACCURATE]: year-matched EIA-860 fleet (vintage_<Y> 2019-2024, canonical "
            "2025) with its eGRID-<Y> heat rates; measured CAMPD coal / ST / CC heat rates "
            "(CT / CHP were already armed); the CAMPD gas sub-5-day outage family (the coal one "
            "stays rejected, neiso-69); the unit partial-derate family (0 NEISO windows: inert); "
            "and the two carries that keep a year-END vintage table from dropping a plant or unit "
            "that retired DURING the year. Std >=5-day extract re-derived for 2019-2021 (+18/+20/+4 "
            "windows, F2 finding 5)."
        ),
        "control": (
            f"the committed keeper {KEEPER} (rule 29(b) form 4); G-DRIFT {PRECOMMIT} section 6"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["r_neiso"] = {
        "precommit": PRECOMMIT,
        "result": RESULT,
        "keeper_control": KEEPER_ID,
    }
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
