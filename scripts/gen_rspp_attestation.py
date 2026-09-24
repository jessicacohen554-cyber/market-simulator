"""Emit the R-SPP calibration attestation for the composed 2019-2025 SPP bundle.

R-SPP (``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md`` §5.3.9) re-solves SPP's
incumbent keeper recipe on the F1 / F2 corrected backcast inputs, one year per shard (rule 36), composed
at zero LP into ``rspp_span`` (2019-2025). Same reason as ``gen_hydro5_attestation.py``:
``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``, so without this the
composite scores C6 ``UNATTESTED`` for a plumbing reason.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``).
Every armed field is a registered ``ScenarioConfig`` boolean whose level is a measured artifact (CAMPD
heat rates, CAMPD unit partial-derate plateaus, EIA-860 vintage + eGRID-<Y>). ``offer_curve_by_group`` is
asserted byte-identical to the incumbent's on BOTH halves, so the rule-1 authorized price-tuning channel
was not touched (condition (c)). The incumbent span's governance block is inherited; only the mechanism
record and the held-years statement are replaced.

Usage:
    python scripts/gen_rspp_attestation.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
PRECOMMIT = "docs/handoffs/PRECOMMIT-r-spp-2019-2025-inputs-2026-09-24.md"
RESULT = "docs/handoffs/RESULT-r-spp-2019-2025-inputs-2026-09-24.md"
PINNED = "ec13e5c2ad35c4f817cc496ff2363affb3fed2f9"
COMPOSITE = "rspp_span"
INCUMBENT_SPAN = "hydro5_spp_floor_span"
INCUMBENT_RUNG = "hydro5_spp_floor_rung"
INCUMBENT_ID = "2026-09-22-hydro-5-spp-floor"
ARMS = (
    "measured_ct_heat_rates",
    "measured_coal_heat_rates",
    "measured_st_heat_rates",
    "measured_cc_heat_rates",
    "measured_chp_heat_rates",
    "unit_partial_outage_windows",
    "mid_vintage_exit_carry",
    "eia860_vintage_tracks_solve_year",
)


def _offer_sha(cfg: dict) -> str:
    blob = json.dumps(cfg.get("offer_curve_by_group") or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _scenario(path: Path) -> dict:
    return json.loads(path.read_text())["scenario_config"]


def main() -> int:
    """Write the composite's attestation from the incumbent span's."""
    bundle = CAL / COMPOSITE
    att = json.loads(
        (CAL / INCUMBENT_SPAN / "calibration_attestation.json").read_text()
    )
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in bundle.glob("run_config_*.json")
    )
    ksha = {
        _offer_sha(_scenario(CAL / b / "run_config.json"))
        for b in (INCUMBENT_SPAN, INCUMBENT_RUNG)
    }
    if len(ksha) != 1:
        raise SystemExit(f"incumbent halves disagree on offer_curve_by_group: {ksha}")
    for y in years:
        sc = _scenario(bundle / f"run_config_{y}.json")
        sha = _offer_sha(sc)
        if sha not in ksha:
            raise SystemExit(f"{y}: offer_curve_by_group {sha} != incumbent {ksha}")
        off = [f for f in ARMS if sc.get(f) is not True]
        if off:
            raise SystemExit(f"{y}: arms not True: {off}")
    sha = ksha.pop()
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = (
        f"R-SPP (2026-09-24) -- incumbent keeper {INCUMBENT_ID}'s recipe (span 2023-25 + rung "
        "2019-22) replayed via scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), each year "
        "from its own incumbent bundle, with exactly the eight registered ScenarioConfig booleans "
        f"{list(ARMS)} set True. Five measured heat-rate fields + the vintage flag are F1's "
        "backcast defaults (passed explicitly); unit_partial_outage_windows is the charter's partial-"
        "derate arm; mid_vintage_exit_carry (K on the rung) is set on 2023-25 too, where phase 0 "
        "measured it fleet-inert, so the seven years are one recipe. Every leg was verified by "
        "scripts/probes/_rspp_shard_check.py (recipe diff + nine input sha256) and again by "
        f"scripts/probes/_rspp_compose.py before composition. Zero LP in the parent. Pre-registered "
        f"in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard launched; record {RESULT}."
    )
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"R-SPP (2026-09-24): this run's own solved years {years}. offer_curve_by_group "
            f"SHA-256 {sha} is byte-identical to the incumbent's on every year; this lane passed only "
            "input-correction --set flags. No band, class or value moved and nothing was swept "
            "(rule 1 condition (c)). ONE config across every scored year (condition (b))."
        )
    gov["mechanism_armed"] = {
        "fields": {f: True for f in ARMS},
        "free_parameters_added": 0,
        "level": (
            "all measured: CAMPD unit-level heat rates per (plant, class) -- the solve year's own "
            "ok row, else the plant's pooled 2019-2025 ok row, else eGRID-<Y> (F1); CAMPD unit-grain "
            "partial-derate plateaus with the plant-level detector's frozen constants (F2 extract "
            "data/raw/campd-partial-outages-SPP.csv); EIA-860 vintage_<Y> with the year-matched "
            "eGRID join (F1)"
        ),
        "basis": (
            "Owner instruction 2026-09-24 (audit §5): every backcast year on the year-correct EIA-860 "
            "vintage, plant-specific heat rates, granular CAMPD outage data. Rule 14 [R-ACCURATE]: "
            "measured inputs replace the HEAT_RATE_BINS class table (100 % of SPP thermal MW in the "
            "2019-22 rung, audit D1) and eGRID-2023-for-every-year (D2). Never the residual."
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: every heat-rate field REPLACES the base rate of the rows it "
            "covers (no stack); the partial family is the unit-grain second window shape of the "
            "armed unit-outage family, coal-scoped, and adds no floor"
        ),
        "control": (
            f"the committed incumbent {INCUMBENT_SPAN} + {INCUMBENT_RUNG} (rule 29(b) form 4); "
            f"G-DRIFT {PRECOMMIT} section 4: F1/F2 hunks LIVE by design, every other hunk INERT"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["r_spp"] = {"result": RESULT, "composed_from_years": years}
    att.pop("hydro5", None)
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {bundle.relative_to(REPO)}/calibration_attestation.json years={years}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
