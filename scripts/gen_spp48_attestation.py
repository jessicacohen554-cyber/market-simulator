"""Emit the SPP-48 calibration attestation for the mid-vintage-year exit carry.

SPP-48 arms exactly ONE new ``ScenarioConfig`` field,
``mid_vintage_exit_carry`` (default off, backcast-only), and changes nothing
else: the run is SPP's committed 2019-2022 rung
(``2026-09-16-spp-43-outage-intake``) replayed with that single ``--set`` and
no other delta.

**Why this exists rather than ``scripts/gen_touchpoint_attestation.py``.** The
same two reasons SPP-42 and SPP-43 recorded, both still live: that shared
helper refuses a multi-tier year span on a ``holdout_policy.tier_for_year``
guard that ``[R-HOLDOUT]``'s removal (2026-09-09) made stale, and
``replay_keeper --out-dir`` does not propagate ``calibration_attestation.json``
into the out-dir, so without this the bundle scores C6 ``UNATTESTED`` for a
plumbing reason rather than a governance one. Both are shared infrastructure
and repairing them is not this lane's object (rule 25 ``[R-ISO-SCOPE]``).

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` /
24 ``[R-REGISTRY]``): the new gate is a boolean whose membership is a set
difference over EIA's own two published sheets and whose timing is EIA's own
published retirement month. No threshold, share, multiplier or window is
introduced, and ``offer_curve_by_group`` is replayed byte-identically.

Usage:
    python scripts/gen_spp48_attestation.py --bundle results/calibration/spp48_arm_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp42_span_a/calibration_attestation.json"
RUNG = REPO / "results/calibration/spp43_holdout_span/calibration_attestation.json"
DEFAULT_BUNDLE = REPO / "results/calibration/spp48_arm_span"

OFFER_SHA = "090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65"

_ATTESTED = (
    "SPP-48 (2026-09-19), the mid-vintage-year whole-plant exit carry. SPP's "
    "committed 2019-2022 rung (2026-09-16-spp-43-outage-intake) replayed with "
    "EXACTLY ONE --set, mid_vintage_exit_carry=true, and no other delta: "
    "offer_curve_by_group byte-identical (SHA-256 "
    f"{OFFER_SHA}), no band, class or value moved, no threshold re-cut. "
    "THE DEFECT IT REPAIRS, root-caused by SPP-47 and reproduced independently "
    "at ZERO LP before anything was built: under "
    "eia860_vintage_tracks_solve_year the active EIA-860 directory is "
    "vintage_<solve year>/, which ships no whole-plant retiree parquet, so "
    "load_retired_within_window returns [] -- on the stated assumption that "
    "'the operable fleet already has them'. That holds for a plant retiring "
    "AFTER the vintage year and is FALSE for one retiring DURING it, because "
    "that vintage's operable sheet is a YEAR-END snapshot which has already "
    "moved the plant onto the Retired-and-Canceled sheet. The plant is then in "
    "NEITHER sheet the channel reads and is dropped from the fleet entirely "
    "with all of its real operating months. Measured: Oklaunion (plant 127, "
    "720 MW nameplate / 650 MW summer sub-bituminous coal, ba_code SWPP, EIA "
    "retirement 9/2020) is in the 2019 LP fleet as COAL_SPP-North_p127_* and "
    "ABSENT from 2020, 2021 and 2022, against 1,209.2 GWh of CAMPD-metered "
    "generation over May-September 2020. EIA's own vintages pin it: "
    "vintage_2019 operable OP with planned retirement 9/2020, vintage_2020 "
    "retired-and-canceled RE with retirement 9/2020. "
    "ONE FALSE ASSUMPTION, THREE SEAMS, and fixing only the first produces a "
    "STRUCTURALLY WRONG INPUT -- which is why all three are repaired and why "
    "the intermediate states are recorded here rather than hidden. (1) The "
    "injection gate (_mid_vintage_exit_rows): membership is the STRICT "
    "COMPLEMENT of _partial_plant_exit_rows' (which requires the plant to "
    "SURVIVE in the operable snapshot), so the two can never select the same "
    "row, and the helper returns None wherever the whole-plant retiree parquet "
    "exists, so it cannot double-count on the canonical path. With only this "
    "fixed, Oklaunion came back online in ALL TWELVE MONTHS of 2020, three of "
    "them after it had retired -- a rule 17 [R-FLOOR-WINDOW] violation by "
    "construction. (2) fleet_to_bins discards a unit's own EIA-860 retirement "
    "for a plant-binned LP -- precisely the miso-191 defect -- so the SAME "
    "exit-cohort router is reused under its own flag (rule 19 [R-ONE-MECH]: "
    "one mechanism, two memberships, neither arming the other) via a "
    "Generator.mid_vintage_exit_unit provenance stamp mirroring "
    "partial_exit_unit. That took the window to Jan-Sep and the unit ids to "
    "COAL_SPP-North_p127_r202009_*. (3) The outage derate DENOMINATOR, whose "
    "own comment already states the rule -- a within-window exit's capacity "
    "'must be in the derate denominator, else their unit-outage rows route to "
    "a (plant_code, plant_group) absent from this map and are skipped'. The "
    "committed campd-unit-outages-SPP.csv carries Oklaunion's real stops "
    "(2020-01-01 -> 2020-05-19 and 2020-09-26 -> 2020-12-31, matching CAMPD "
    "exactly) and without this they were silently dropped. That took the "
    "window to MAY-SEPTEMBER and available energy 3,933.2 -> 1,936.3 GWh. "
    "THE RESULTING ENVELOPE IS SHAPE-FAITHFUL, MEASURED NOT ASSERTED: it "
    "covers the CAMPD-metered generation in EVERY month (181.0/454.0/469.1/"
    "469.1/363.2 GWh available against 92.5/222.6/288.9/334.9/270.2 metered, "
    "implied monthly CF 0.511/0.490/0.616/0.714/0.744) and is ZERO in exactly "
    "the months metered generation is zero. "
    "RULE 14 [R-ACCURATE] IS THE ENTIRE BASIS AND THE RESIDUAL IS NOT. The "
    "repair was specified, built and gated BEFORE any LP, on a measured input "
    "defect; a criterion that degrades is a discovered root cause to route, "
    "never grounds to revert. It does NOT close the criterion it touches, "
    "which is stated so it cannot be over-bought: C1-2020 COAL_PRB moves from "
    "-10.8484 to -10.0129 TWh against an unchanged 67.0581 TWh actual -- a "
    "0.8355 TWh (7.7 %) improvement on a row that remains a clear FAIL. "
    "RULE 13 [R-MEASURED] PASSES: the retirement month is EIA's own published "
    "field and the membership is a set difference over EIA's own two published "
    "sheets. Nothing is pinned to observed generation, no offset, haircut or "
    "adder is added, and no input is rescaled so the model's output lands on "
    "an actual. The identical construction regenerates for a forward year from "
    "the then-current EIA-860 and responds to a changed fleet. "
    "RULES 21 [R-DOF] / 24 [R-REGISTRY]: ZERO free parameters. One boolean "
    "gate, registered in _CACHE_KEY_OPTIONAL_FIELDS at drop value 'False' and "
    "in the DOF identification ledger as 'EIA-860 actual retirement month "
    "(native vintage)'. No threshold, no window, no share, no multiplier. "
    "RULE 25 [R-ISO-SCOPE]: DEFAULT OFF and NOT armed in _spp_config -- SPP "
    "has no default_scenario_overrides and carries "
    "eia860_vintage_tracks_solve_year through the per-run override bag, so "
    "this arm follows SPP's own established route and a default flip remains "
    "an owner ruling. The blast radius was measured at ZERO LP over ALL 227 "
    "committed run_config records before the shared seam was touched: the "
    "defect needs a BACKCAST whose active directory is a native vintage, and "
    "the only route is this flag's parent eia860_vintage_tracks_solve_year, "
    "armed by SPP ALONE; every explicit eia860_vintage_year pin in the program "
    "belongs to a mode='forecast' hindcast, which never reaches this "
    "backcast-only channel. Other regions' canonical retiree parquet already "
    "carries their mid-vintage-year retirees (MISO 17/17, PJM 12/12, NEISO "
    "2/2, SPP 2/2). "
    "THE KEEPER CANNOT MOVE, by construction AND by test: vintage_2023/ and "
    "vintage_2024/ ship NO Retired-and-Canceled sheet at all and 2025 has no "
    "vintage directory, so the channel is inert in all three scored years -- "
    "verified byte-identical on all 14 FleetArrays LP inputs in 2021, 2023, "
    "2024 and 2025. Off-path byte-identity is STRUCTURAL rather than merely "
    "asserted: every widened outage call is made at its ORIGINAL arity while "
    "the gate is off, so the lru_cache key tuples are unchanged too. "
    "RULE 29 [R-SCREEN]: NO screen, on the SPP-38/42/43/45/47 precedent -- the "
    "screen applies to a candidate MECHANISM competing against a correct one, "
    "and a missing measured input is not a candidate mechanism. Phase 0 was "
    "nonetheless done in full and is what set the scope (three committed "
    "probes: _spp48_midvintage_blast_radius.py, _spp48_midvintage_fleet_reach.py "
    "and _spp48_benchmark_membership.py). Rule 29(b) form 4 holds and was "
    "EMPIRICALLY CONFIRMED rather than assumed: the control is the COMMITTED "
    "spp43_holdout_span bundle, and the fleet-only control leg reproduces its "
    "committed dispatch/<year>_P1_fleet.parquet EXACTLY (rows and pmax) in all "
    "four years. A separate zero-delta replay of both SPP registered runs at "
    "this base found prices identical to 1e-14 and annual class energy within "
    "0.006 % in exactly-offsetting within-family pairs (net 0.0000 TWh). "
    "REPORTED AT THE GATE, NOT DISCOVERED. (1) THE BENCHMARK DROPS THE SAME "
    "PLANT, BY A DIFFERENT DEFECT, AND THIS REPAIR DOES NOT FIX IT. SPP-47 "
    "§2.2 predicted the benchmark question becomes moot once the fleet carries "
    "Oklaunion; that is REFUTED -- two copies of the rung bundle differing "
    "ONLY in mid_vintage_exit_carry rebuild to the SAME content-addressed "
    "EIA-923 frame. The benchmark's ISO membership is _iso_plant_ids -> "
    "zone_assignment.build_zone_lookup, built from eGRID-2023 coordinates "
    "supplemented from the CANONICAL (2025ER) EIA-860 plant file; neither "
    "knows a plant that retired in 2020, the supplement is forward-only by its "
    "own docstring, and the lookup does NOT follow "
    "eia860_vintage_tracks_solve_year (measured at 830 plants with 127 absent "
    "under EVERY vintage, one interpreter per vintage). The LP fleet has a "
    "fallback-zone path for a plant eGRID lacks; the benchmark has a hard isin "
    "filter with none, so a mid-window retiree can be IN the model and OUT of "
    "the actual at once. THIS RUN IS UNAFFECTED and was checked rather than "
    "assumed: its bundle resolves eia923-cda580e2f71c, the SAME frame the "
    "committed control uses, whose 2020 COAL_PRB actual is 67.0581 TWh and "
    "which carries plant 127 at 1,209,201 MWh -- so the arm/control comparison "
    "is like-for-like and no part of the C1 movement comes from a changed "
    "denominator. The benchmark regression is filed as the NAMED SUCCESSOR, "
    "not folded in, precisely because folding it in would shrink a failing "
    "criterion by deleting real metered generation (rules 13 / 14). "
    "(2) TWO CLASSES DEGRADE in 2020 and are reported at full magnitude: "
    "ST_GAS -5.3599 -> -5.5365 TWh and COAL_LIGNITE -2.6650 -> -2.7235 TWh, "
    "against CT_PEAKER +6.7508 -> +6.3680 and CC_REGULAR +3.9269 -> +3.7332 "
    "which improve. Energy is conserved to 0.001 TWh on 262.64 TWh. "
    "(3) The injected plant carries no measured outage profile beyond the "
    "three stops the committed extract already holds for it; the rule-23 "
    "frozen thermal_tranches_SPP.csv and campd-unit-outages-short-SPP.csv are "
    "neither regenerated nor touched. "
    "(4) main at this base is RED on four pre-existing tests unrelated to this "
    "lane (the ERCOT FleetArrays golden, the NYISO solve-surface pin, the "
    "capacity-evolution soundness end-to-end and the NEISO Mystic retiree "
    "test); each fails identically at base, and for the ERCOT golden the "
    "failing availability hash is byte-identical at base and at HEAD, so this "
    "lane does not move it. "
    "RULE 30 [R-TOUCHPOINT-FOLD] (c): a held-out year REPORTS and can neither "
    "certify nor decertify -- SPP's headline determination remains the "
    "2023-2025 train-tier verdict however these rungs score, and since "
    "[R-HOLDOUT]'s removal no year in this program is a certified "
    "out-of-sample number."
)


def build(bundle: Path) -> dict:
    """Return the SPP-48 attestation: the rung's ledger plus this run's governance."""
    att_path = bundle / "calibration_attestation.json"
    for candidate in (att_path, RUNG, KEEPER):
        if candidate.exists():
            att = json.loads(candidate.read_text())
            break
    else:  # pragma: no cover - every lane has at least the keeper on disk
        raise RuntimeError("no attestation to inherit from")

    fp = att["free_parameters"]
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]

    # Rule 1 [R-STRUCT] (b): `years_held` is an EXACT SET EQUALITY check against
    # THE RUN'S OWN scored years in calibration_verdict._authorized_tuning_finding.
    # Re-cut it off the bundle's dispatch parquets so it cannot drift from what
    # was actually solved (the SPP-40 / SPP-42 / SPP-43 construction).
    apt = gov["authorized_price_tuning"]
    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")
    apt["years_held"] = solved_years
    apt["years_held_basis"] = (
        "SPP-48 (2026-09-19). Re-cut to THIS run's own solved years, read off "
        "dispatch/<year>_P1.parquet. A statement about WHICH YEARS THIS RUN "
        "HOLDS THE CONFIG ACROSS, never a re-tuning: offer_curve_by_group is "
        f"byte-identical to keeper 12's (SHA-256 {OFFER_SHA}), this lane's "
        "ONLY --set is the boolean mid_vintage_exit_carry, and no band, class "
        "or value moved. Condition (c) is untouched — the value was set ex "
        "ante and was not swept here."
    )

    gov["dof_inherited_from"] = "spp42_span_a (SPP keeper 12), via spp43_holdout_span"
    gov["dof_inheritance_basis"] = (
        "SPP-48 adds ONE ScenarioConfig field, mid_vintage_exit_carry, and it "
        "is NOT a free parameter: it is a boolean gate whose membership is a "
        "set difference over EIA's own two published sheets and whose timing "
        "is EIA's own published retirement month. No threshold, share, window "
        "or multiplier is introduced and nothing is re-cut, so the ledger's "
        "entry count is unchanged. The authorized price-tuning channel is "
        f"replayed BYTE-IDENTICALLY (offer_curve_by_group SHA-256 {OFFER_SHA}); "
        "the rule-23-frozen thermal_tranches_SPP.csv and "
        "campd-unit-outages-short-SPP.csv are neither regenerated nor touched."
    )
    gov["attested_by"] = _ATTESTED

    gov.setdefault("measured_input_switches", {})["mid_vintage_exit_carry"] = {
        "value": True,
        "where": (
            "data/raw/eia-860/vintage_<year>/"
            "eia860_generator_retired_and_canceled.parquet -> "
            "market_sim.data.fleet.eia860._mid_vintage_exit_rows -> "
            "load_retired_within_window -> the backcast fleet base; then "
            "fleet_to_bins' exit-cohort routing (via the "
            "Generator.mid_vintage_exit_unit stamp) so cod_ramp.effective_cod "
            "times each plant out on its own EIA-860 retirement month; and "
            "outages._iso_plant_capacity / _iso_plant_unit_capacity as the "
            "derate DENOMINATOR so the plant's own measured outage rows are "
            "applied rather than silently skipped."
        ),
        "identification": "measured-physical-availability-event",
        "source": (
            "EIA-860 annual releases, data/raw/eia-860/vintage_<year>/: the "
            "Retired-and-Canceled sheet's published Retirement Month / "
            "Retirement Year, and the same vintage's operable sheet for the "
            "membership complement. Corroborated against EPA CAMPD hourly "
            "unit-level generation (data/raw/campd-unit-level/) for shape, "
            "which is a CHECK on the envelope and never an input to it."
        ),
        "warrant": (
            "Rule 14 [R-ACCURATE]: a plant that demonstrably ran for five "
            "months of the solved year was absent from the fleet entirely "
            "because of a stated assumption that is false for a plant "
            "retiring DURING its own vintage year. The accurate input "
            "replaces the omission, and a worse fit would be a discovered "
            "root cause to route rather than grounds to revert."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED] PASSES: the retirement month is a published "
            "EIA field and the membership is a set difference over two "
            "published sheets — a formulaic input, not a measured outcome. "
            "Nothing is pinned to observed generation, no offset, haircut or "
            "adder is added, and nothing is rescaled so the model's output "
            "lands on an actual. The identical construction regenerates for a "
            "forward year from the then-current EIA-860 and responds to a "
            "changed fleet."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: no second mechanism. The membership is the "
            "STRICT COMPLEMENT of partial_plant_exit_carry's (that channel "
            "requires the plant to SURVIVE in the operable snapshot, this one "
            "requires it to be absent), so the two can never select the same "
            "row; the helper returns None wherever the whole-plant retiree "
            "parquet exists, so it cannot double-count on the canonical path; "
            "the rows join the same frames list and are scoped by the same "
            "retiree_vintage_status_scope oracle; and the exit-cohort router "
            "is REUSED rather than duplicated, each membership behind its own "
            "flag so neither arms the other."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: default OFF, not armed in _spp_config, and "
            "measured inert for every other region at HEAD over all 227 "
            "committed run_config records — only SPP arms the parent "
            "eia860_vintage_tracks_solve_year, and every explicit "
            "eia860_vintage_year pin belongs to a mode='forecast' hindcast "
            "that never reaches this backcast-only channel. No number crosses "
            "an ISO boundary: every retirement month is that plant's own "
            "published field."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: the gate is a ScenarioConfig field, "
            "registered in _CACHE_KEY_OPTIONAL_FIELDS at drop value 'False' in "
            "the same commit, present in this bundle's run_config.json, and "
            "carried in the DOF identification ledger as 'EIA-860 actual "
            "retirement month (native vintage)'. No env var, no hardcoded "
            "per-plant dict, no getattr fallback literal."
        ),
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = ap.parse_args()
    att = build(args.bundle)
    out = args.bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=2) + "\n")
    fp = att["free_parameters"]
    print(
        f"{args.bundle.name}: attestation written — "
        f"years_held={att['governance']['authorized_price_tuning']['years_held']} "
        f"n_entries={fp['n_entries']} n_residual={fp['n_residual']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
