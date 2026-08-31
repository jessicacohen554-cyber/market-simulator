"""miso-191 keeper attestation — re-keyed from the miso-188 keeper's (PREREG-miso191 §5).

Copies `miso188_rvs_B/calibration_attestation.json` onto the promoted arm
bundle `miso191_bax_B` with exactly three changes:

1. ONE new free-parameter ledger entry (`partial_plant_exit_carry`,
   identification MEASURED, zero scalars) — ledger 36/2 -> 37/2.
2. `governance.attested_by` re-keyed to the miso-191 A/B.
3. A `miso191_ab` disclosure recording, against interest, the two S-1
   witness clauses that FAILED AS FROZEN and their measured root causes
   (instrument mis-freezes), the probe's mechanical kill-2 REJECT left
   standing on the record, and the promotion basis (the owner's in-session
   advance directive resolving the PREREG's escalation path).

Everything else — the 36 inherited entries, the governance booleans, the
exceptions ledger, every earlier disclosure — is carried byte-verbatim.

Run:
    python3 scripts/probes/_miso191_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "results/calibration/miso188_rvs_B/calibration_attestation.json"
DST = REPO / "results/calibration/miso191_bax_B/calibration_attestation.json"

NEW_ENTRY = {
    "name": "partial_plant_exit_carry (boolean arm; miso-191 binning-aware delivery)",
    "where": (
        "ScenarioConfig.partial_plant_exit_carry -> scripts/run_calibration.py "
        "(and runner.py's backcast branch) -> "
        "data/fleet/eia860.py::load_retired_within_window(partial_plant_exit_carry=) "
        "via _partial_plant_exit_rows (the committed Retired-and-Canceled sheet's "
        "surviving-plant complement) + load_mothballed_but_operating status widening "
        "{OA}->{OA,OS,SB} + the gated data/coal.py::register_partial_exit_coal_supply "
        "registry; DELIVERY (miso-191): loader-stamped Generator.partial_exit_unit -> "
        "data/fleet/campd_bins.py::fleet_to_bins date-scoped exit-cohort bins "
        "(plant x group x retirement month) -> data/fleet/assembly.py::bins_to_fleet "
        "stamps each cohort tranche's own retirement -> the EXISTING "
        "cod_ramp.effective_cod per-unit preference (the Homer City seam) ages the "
        "cohort out at unit grain"
    ),
    "identification": "measured",
    "lineage_solves": (
        "0 for every membership/timing/registry rule (frozen in PREREG-miso190 §1/§3 "
        "and carried verbatim; the miso-190 A/B that REJECTED the un-binned delivery "
        "informed only WHERE the per-unit retirement dies — fleet_to_bins — never a "
        "parameter). The form choice (a) exit-cohort bins vs (b) bin-capacity derate "
        "was frozen ex ante in PREREG-miso191 §1 with zero-solve reasons "
        "(_miso191_binning_phase0.json) before any leg"
    ),
    "source": (
        "Published EIA-860 records only: the actual Retirement Year/Month on the "
        "committed retired-and-canceled sheet (a physical availability event, the "
        "same class as outage windows), the year-matched vintage generator status "
        "(the identical oracle three armed mechanisms already read), and each unit's "
        "own Energy Source 1 code through the canonical COAL_CODE_TO_SUPPLY. "
        "Membership = the sheet complement; timing = the sheet's own month per unit; "
        "no CEMS quantity enters membership. Census at unit grain: "
        "_miso190_partial_exit_phase0.json (59 units / 3,984 MW leg 1; Big Cajun 2-1 "
        "+ Warrick-2 leg 2); witness ceilings: _miso191_binning_phase0.json"
    ),
    "why_zero": (
        "Zero fitted scalars, no threshold, no size floor, no per-unit hand-list. "
        "Every input regenerates for a forward year and responds to changed "
        "conditions (rule 13); the cohort-bin delivery introduces no numeric value "
        "at all — capacity is the sheet's own net-summer MW, heat rate the cohort's "
        "capacity-weighted own rates, tranche splits the plant's existing measured "
        "overrides. n_residual unchanged"
    ),
}

ATTESTED_BY = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: partial_plant_exit_carry=true (the "
    "binning-aware exit-cohort delivery, miso-191, 2026-08-30). PREREG "
    "results/calibration/PREREG-miso191-binning-aware-exit-2026-08-30.md was "
    "committed, pushed and blob-verified BEFORE the mechanism was implemented and "
    "BEFORE any adjudicating quantity was computed; the form choice (a) was frozen "
    "in its §1 with zero-solve reasons. Both legs are replay_keeper re-solves of "
    "the 2026-08-30-miso-188-rvsscope keeper's own recipe, years 2023 2024 2025 in "
    "ONE invocation each, years sequential, legs sequential (rules 12/16); the "
    "arm's single delta rode the sanctioned replay channel and is recorded in "
    "run_config.json. S-0: the control (2026-08-30-miso-191-control) reproduced "
    "the committed keeper value-identically on every scored sidecar of every year "
    "(fifth consecutive clean HEAD reproduction). Gates record: "
    "_miso191_ab_gates.json; the mechanical verdict it records (REJECT, charter "
    "kill 2) STANDS UNALTERED on the record — see disclosures.miso191_ab for why "
    "the promotion was adjudicated by the owner's in-session directive instead."
)

DISCLOSURE = (
    "miso-191 A/B, reported against interest. (a) TWO PRE-REGISTERED S-1 WITNESS "
    "CLAUSES FAILED AS FROZEN, and the instrument's mechanical verdict (REJECT via "
    "charter kill 2: 'coal C1 improves while any S-1 clause failed') is left "
    "standing unaltered in _miso191_ab_gates.json. Root causes, measured: "
    "(1) post_exit_ceilings p4014_CT_PEAKER — the frozen ceiling of 0.0 MW was "
    "IMPOSSIBLE for any correct arm: the operable snapshot carries five 'Natural "
    "Gas Internal Combustion Engine' units (WHT09-13, 47.0 MW) the phase-0 tech "
    "filter (gas-CT string only) missed, and the CONTROL violates the frozen "
    "ceiling byte-identically to the arm (max Jun-Dec-2025 hourly 32.887855529785156 "
    "MW in BOTH legs) — the clause measures keeper-baseline behavior and carries "
    "zero information about the flag's action; (2) leg2 6055 capacity delta — the "
    "frozen +517.0 MW used the SNAPSHOT rating while the arm's measured deltas "
    "(+520.0 in 2023, +554.1 in 2024, 0.0 in 2025) equal Big Cajun 2-1's "
    "YEAR-MATCHED VINTAGE net-summer ratings to the decimal "
    "(vintage_2023 520.0 / vintage_2024 554.1) — the basis PREREG-miso190's leg-2 "
    "design text itself specifies ('the same per-unit build from the vintage "
    "rows'). Warrick (6705) matched exactly (+126.4 / 0 / 0). Every OTHER witness "
    "family passed: cohort presence + capacity at all 8 plants x 3 years, exit "
    "timing EXACTLY 0 post-exit everywhere, all six correctly-frozen plant "
    "ceilings, survival, oracle drops, Grand Tower/Rush Island guards. "
    "(b) PROMOTION BASIS: the PREREG's own promotion rule could NOT fire clean "
    "(S-1 not clean as frozen), so per the handoff's ask C this went to the "
    "owner-escalation path with the recommendation; the owner's in-session "
    "standing directive ('Is this a recommended keeper candidate? If so plz "
    "promote', given twice, 2026-08-30/31) resolved it. No witness was re-keyed, "
    "no alternative statistic replaced a frozen one, and the mis-freeze "
    "demonstration uses only the frozen quantities themselves plus committed "
    "records. Reverting keepers/MISO.json to 2026-08-30-miso-188-rvsscope undoes "
    "the promotion. (c) Scored faces at full magnitude: C3a-2023 +3.5008 -> "
    "+0.0913, C3a-2024 -4.3034 -> -4.5511 (the declared adverse face, in-band), "
    "C3a-2025 -12.2965 -> -12.3405 (charter kill 1 tolerance 0.10 pp; silent at "
    "0.044), 2023 coal C1 sum|err| 8.546 -> 3.399 TWh, zero PASS->FAIL flips "
    "(C3b-2025 stays PASS — the miso-190 phantom flip is absent), "
    "forced_share COAL 2023/2024 PASS -> SKIPPED (the arm's bare-COAL class row "
    "reads 0.0% of load — immaterial, coverage bookkeeping only), C8 2023 "
    "CT_PEAKER newly grounded-above-budget at 15.6% vs the 15% cap (clean PASS "
    "note per rule 20). (d) One benchmark-part cosmetic diff, disclosed: "
    "bench/MISO/2023.json.gz drops plant 992 (CC Perry K, 3.4 MW ST_CHP cohort) "
    "from the plants metadata map; zero numeric benchmark values move. "
    "(e) The witness-capacity channel named in PREREG-miso191 §4 (FleetContext "
    "schema metadata) does not exist in the bundle's dispatch parquet (plain long "
    "table); the SAME frozen quantities were read from the new per-pass "
    "dispatch/<year>_<pass>_fleet.parquet listing added as instrumentation before "
    "the legs — an instrument correction, quantities unchanged."
)


def main() -> None:
    d = json.loads(SRC.read_text())
    fp = d["free_parameters"]
    assert fp["n_entries"] == len(fp["entries"]) == 36, fp["n_entries"]
    fp["entries"].append(NEW_ENTRY)
    fp["n_entries"] = 37
    d["governance"]["attested_by"] = ATTESTED_BY
    d["disclosures"]["miso191_ab"] = DISCLOSURE
    DST.write_text(json.dumps(d, indent=1) + "\n")
    print(f"wrote {DST} (ledger {fp['n_entries']}/{fp['n_residual']})")


if __name__ == "__main__":
    main()
