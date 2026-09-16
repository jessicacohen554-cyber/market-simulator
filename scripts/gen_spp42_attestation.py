"""Emit the SPP-42 calibration attestations for the commitment-feasibility clip.

SPP-42 arms exactly ONE new gated ``ScenarioConfig`` field —
``mustrun_commitment_feasibility_clip`` — on top of SPP keeper 11's recipe
(``2026-09-13-spp-38-vintage-cache``), across **both** of SPP's registered year
sets:

* ``results/calibration/spp42_span_a`` — 2023, 2024, 2025 (keeper 11's span);
* ``results/calibration/spp42_span_b`` — 2019-2022, the held-out years the
  SPP-40 touchpoint covers.

**Why this exists rather than ``scripts/gen_touchpoint_attestation.py``.** Two
reasons, both already on the record. (1) That shared helper refuses a run whose
years span more than one ``holdout_policy.tier_for_year`` tier, a guard SPP-40
recorded as STALE after ``[R-HOLDOUT]``'s removal (2026-09-09) — splitting a
bundle to satisfy it would violate rules 16 ``[R-ALLYEARS]`` / 32(b)
``[R-SHARD]``. It is REPORTED, not patched: it is shared infrastructure other
ISOs depend on and repairing it is not this lane's object. (2)
``replay_keeper --out-dir`` regenerates ``legitimacy_diagnostics.json`` but does
NOT propagate ``calibration_attestation.json`` into the out-dir, so without this
both bundles would score C6 ``UNATTESTED`` for a plumbing reason rather than a
governance one.

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` /
24 ``[R-REGISTRY]``). The new field is a BOOLEAN GATE over a construction rule
that reads only ``pmax``, ``availability`` and ``cc_mustrun_pmin_mw`` — arrays
the LP already holds — and introduces no threshold, share, multiplier, length,
artifact, loader or CLI input. Machine-confirmed: ``build_dof_ledger.py --iso
SPP`` at HEAD emits **5 entries / 3 residual** on both bundles, byte-identical
to keeper 11's own ledger. ``offer_curve_by_group`` is byte-identical in both
bundles (whole-mapping ``json.dumps(sort_keys=True)`` SHA-256
``090abd79…62f65``), machine-checked by each shard before it solved and by the
parent after it landed; the rule-1 authorized channel was not touched, re-cut
or swept.

Usage:
    python scripts/gen_spp42_attestation.py            # both bundles
    python scripts/gen_spp42_attestation.py --bundle results/calibration/spp42_span_a
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp38_span/calibration_attestation.json"
SPAN_A = REPO / "results/calibration/spp42_span_a"
SPAN_B = REPO / "results/calibration/spp42_span_b"

OFFER_SHA = "090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65"

_GATE = "mustrun_commitment_feasibility_clip"

_ATTESTED_COMMON = (
    "SPP-42 (2026-09-16), card R-be's open half. SPP keeper 11's recipe "
    "(2026-09-13-spp-38-vintage-cache) plus EXACTLY ONE armed ScenarioConfig "
    f"gate, {_GATE} — no other --set, no other differing behavioural key. THE "
    "DEFECT IT REPAIRS, measured at ZERO LP before any arm was solved: the "
    "per-plant must-run floor asserts a COMMITMENT (the plant synchronized at "
    "its own measured minimum online level, committed_pct x nameplate, the "
    "P5-of-online loading the tranche artifact reports and by construction the "
    "SMALLEST configuration the plant demonstrated in the CEMS record), and "
    "because a committed tranche's cc_mustrun_pmin_mw IS its own pmax the "
    "global clip reduces to EXACTLY 'tranche pmax x availability' — the "
    "commitment inherits the availability derate LINEARLY. A commitment is not "
    "linear. Where a dated outage leaves the plant less available capacity than "
    "its own minimum online level, NO configuration it has ever operated is "
    "feasible, and np.minimum silently substitutes a smaller, equally "
    "infeasible commitment instead of none: single-unit Cimarron River (1230, "
    "50 MW) is floored at a MEDIAN 1.33 MW — 6.2 % of its own 21.6 MW level — "
    "across 845 hours its own CAMPD meter reads zero, and 1235 (4.00 vs 24.0), "
    "1271 (1.68 vs 17.0) and 3008 (16.91 vs 41.9) carry the same signature "
    "while every passing plant sits at 73-92 %. That is rule 17 "
    "[R-FLOOR-WINDOW]'s signature at the per-unit grain and it is a bug BY "
    "DEFINITION, so NO residual justified this lane and none was consulted in "
    "choosing it. Rule 18 [R-PHYSICS]: eligibility is unit physics (can this "
    "plant carry the configuration the floor asserts), never a class tuple, "
    "plant list or conduct statistic — deliberately NOT "
    "mustrun_plant_exclusions, which miso-170 warns 'would bury that error "
    "inside a membership list'. Rule 13 [R-MEASURED]: NOTHING measured enters "
    "— both operands are arrays the LP already holds — so the rule is "
    "FORWARD-NATIVE (deliberately not registered in "
    "_BACKCAST_ONLY_OVERLAY_FIELDS) and responds in a forecast year to that "
    "year's own EFOR/maintenance envelope; it selects no hours from any meter, "
    "so the form SPP-46 declared INADMISSIBLE is never reached. Rule 19 "
    "[R-ONE-MECH]: the ONE floor's clip is REPLACED in the infeasible hours and "
    "nothing is stacked — the committed D-2 confirms st_gas_mustrun_per_plant "
    "is the SOLE mechanism flooring SPP ST_GAS, and membership "
    "(mustrun_plant_exclusions), window SIZE (mustrun_online_frac_per_year), "
    "PLACEMENT (mustrun_window_commitment_grain) and the lay-up hour-eligibility "
    "mask (mustrun_layup_window_mask) are four other orthogonal properties of "
    "the same floor, all off. MACHINE-VERIFIED ON THE SOLVED FLOOR ARRAYS, not "
    "merely pre-solve: every moved min_gen cell carries control-leg mechanism "
    "id 16 (st_gas_mustrun_per_plant) and arm-leg id 0, with the chp_steam "
    "(104,016 cells) and nuclear_mustrun (17,520 cells) floor arrays "
    "BYTE-IDENTICAL across legs. Rule 21 [R-DOF]: ZERO free parameters added — "
    "build_dof_ledger.py --iso SPP at HEAD emits 5 entries / 3 residual on this "
    "bundle, byte-identical to keeper 11's own ledger. Rule 25 [R-ISO-SCOPE]: "
    "the gate ships default OFF, so every other ISO's keeper is byte-identical "
    "and there is no per-ISO number to transfer; all nine matrix shards carry "
    "the cell. Rule 29 [R-SCREEN]: phase 0 first (two sibling routes killed at "
    "zero LP — mustrun_layup_window_mask alone is a rule-19 DOUBLE-SUBTRACTION "
    "on SPP, since 1089 of 1089 lay-up rows are already present in the outage "
    "extract the keeper reads with campd_outage_merit_order_guard off; and the "
    "blunt 'zero under ANY outage' variant destroys correct floors on "
    "multi-unit plants), then a screen on 2023 named in the PRECOMMIT BEFORE it "
    "ran on the mechanism's OWN largest measured footprint (0.1428 TWh against "
    "0.1154 and 0.0465) and demonstrably NOT the residual year."
)

_ATTESTED_A = (
    _ATTESTED_COMMON + " THIS BUNDLE is the 2023-2025 span: ONE --years 2023 2024 2025 "
    "invocation in ONE shard, years sequential inside it (rules 12 / 16 / "
    "32(b)). MEASURED against keeper 11's COMMITTED bundle: D-4 per-unit "
    "conduct FAIL rows 10 -> 2 (plants 1230/1235/1271 resolve in every year "
    "they failed and 3008 resolves in 2025; 3008 remains in 2023 and 2024, "
    "improved — bind_h 2047 -> 1836 and 2427 -> 1997, zero share 0.6087 -> "
    "0.5839 and 0.5777 -> 0.5108 — but not crossed). C8 ST_GAS forced share "
    "0.2001/0.1873/0.1535 -> 0.1881/0.1769/0.1423, further under the 0.30 cap "
    "in all three years. THE COST IS REPORTED AT FULL MAGNITUDE AND WAS "
    "DECLARED AT THE GATE, NOT DISCOVERED: C1 ST_GAS worsens (2023 -6.362 -> "
    "-6.494 TWh, 2024 -7.597 -> -7.703) because the arm REMOVES floor from a "
    "class already under-produced, exactly as the PRECOMMIT predicted; 2025 is "
    "the outlier and moves the OTHER way on volume (net class |error| -0.259 "
    "TWh, CT_PEAKER -0.616) while its PRICE criteria degrade the most (C3a "
    "+5.18 -> +6.05 %, C3b 0.1884 -> 0.1964 against a 0.20 band), and ST_GAS "
    "there RISES +0.113 TWh because forced energy falls while economic dispatch "
    "picks up more. No load-bearing criterion flips: C3a stays inside +/-10 % "
    "and C3b inside 0.20 in all three years, slack and dump are BYTE-IDENTICAL "
    "to the keeper (0 / 1295.6995 / 240.5966 MWh and 0 everywhere), and energy "
    "is conserved to <= 0.0002 TWh on ~285-302 TWh. The PRE-REGISTERED "
    "PLACED-VS-BINDING BOUND BIT, on one plant of four, and is recorded rather "
    "than smoothed over: phase 0 predicted 3008's PLACED median would move "
    "0.0 -> 13.8 MW, the D-4 rider scores BINDING hours, and there it stays at "
    "0.0. 3008 is the only multi-unit plant of the four and the fleet's one "
    "measured two-shifter, whose defect SPP-27 already identified as the "
    "within-day grain — never this clip."
)

_ATTESTED_B = (
    _ATTESTED_COMMON
    + " THIS BUNDLE is the 2019-2022 HELD-OUT span: ONE --years 2019 2020 2021 "
    "2022 invocation in ONE shard, replayed on the SPP-40 touchpoint's bundle "
    "so the ISO's whole registered year set carries the promoted recipe (rules "
    "34(c) [R-SHARD-PROMOTABLE] / 35(c) [R-PROMOTE]). **THE ARM IS PROVABLY "
    "INERT ON THESE FOUR YEARS AND THAT IS STATED HERE RATHER THAN LEFT TO BE "
    "INFERRED.** Its dispatch is BYTE-IDENTICAL to the 2026-09-13-spp-40-"
    "holdout-span control in every class and every year (class totals equal to "
    "4 dp; 271.8128 / 262.6208 / 269.7705 / 288.1893 TWh), its D-4 rows are "
    "byte-identical (33 FAIL rows, same plants, same binding hours, same zero "
    "shares) and its D-2 forced energy is byte-identical (5.0294 / 4.7849 / "
    "5.4248 / 5.4898 TWh). THE REASON IS A DATA-COVERAGE GAP, MEASURED not "
    "assumed: SPP's CAMPD unit-outage extracts cover 2023-2025 ONLY "
    "(campd-unit-outages-SPP.csv 880/905/936 windows in 2023/2024/2025 and ZERO "
    "rows in 2019-2022; likewise the short and lay-up companions), so "
    "availability in the held-out years is the FLAT EFOR baseline — verified "
    "directly, min availcap == p05 availcap for all 21 floored ST_GAS "
    "plant-groups in 2019 — and the clip's predicate (available capacity below "
    "the plant's own committed level) can never fire. The engine says so "
    "itself: 'mustrun_commitment_feasibility_clip ARMED (SPP 2019): 21 floored "
    "plant-groups tested, 0 infeasible plant-hours, 0.0 MWh of commitment floor "
    "released'. CAUTION ON THE C8 NUMBER, recorded because reading it the "
    "obvious way would be WRONG: ST_GAS forced_share reads 0.3423/0.3014/0.5041/"
    "0.5556 in the SPP-40 control and 0.2497/0.2844/0.4559/0.4995 here, which "
    "looks like a large improvement and IS NOT THIS ARM. forced_twh is "
    "byte-identical; only the DENOMINATOR (class_total_twh, the benchmark-side "
    "actual) moved, between SPP-40's HEAD and this base. The held-out C8 breach "
    "SPP-40 named is therefore NOT addressed by this lane and stays open; its "
    "root cause is the same missing 2019-2022 outage extract, which is routed "
    "as SPP's next data-intake item and is NOT a modelling lane. Rule 30 "
    "[R-TOUCHPOINT-FOLD] (c): a held-out year REPORTS and can neither certify "
    "nor decertify — SPP's headline determination remains the 2023-2025 "
    "train-tier verdict however these rungs score."
)


def build(bundle: Path) -> dict:
    """Return the SPP-42 attestation for one bundle: keeper 11's ledger + this run's governance."""
    att_path = bundle / "calibration_attestation.json"
    # build_dof_ledger.py --iso SPP has already refreshed `free_parameters` in
    # place from THIS bundle's own run_config.json (the like-for-like baseline
    # rule 21 [R-DOF] asks for). Read it back rather than re-deriving it here,
    # so the checker's own output is what ships.
    att = (
        json.loads(att_path.read_text())
        if att_path.exists()
        else json.loads(KEEPER.read_text())
    )
    fp = att["free_parameters"]
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    is_a = bundle.name.endswith("_a")
    gov = att["governance"]

    # Rule 1 [R-STRUCT] (b): `years_held` is checked by
    # calibration_verdict._authorized_tuning_finding as an EXACT SET EQUALITY
    # against THE RUN'S OWN scored years. Re-cut it off the bundle's dispatch
    # parquets so it cannot drift from what was actually solved (the SPP-40
    # construction, for the identical reason).
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
        "SPP-42 (2026-09-16). Re-cut to THIS run's own solved years, read off "
        "dispatch/<year>_P1.parquet. This is a statement about WHICH YEARS THIS "
        "RUN HOLDS THE CONFIG ACROSS, never a re-tuning: offer_curve_by_group is "
        f"byte-identical to keeper 11's (SHA-256 {OFFER_SHA}), this lane passes "
        f"only --set {_GATE}=true, and no band, class or value moved. Condition "
        "(c) is untouched — the 0.93 was set ex ante and was not swept here."
    )

    gov["dof_inherited_from"] = "spp38_span (SPP keeper 11)"
    gov["dof_inheritance_basis"] = (
        "SPP-42 arms ONE boolean gate over a construction rule that reads only "
        "pmax, availability and cc_mustrun_pmin_mw — arrays the LP already holds "
        "— and introduces no threshold, share, multiplier, length, artifact, "
        "loader or CLI input, so NOTHING IS ADDED to the ledger. Machine-"
        "confirmed rather than asserted: build_dof_ledger.py --iso SPP at HEAD "
        "emits 5 entries / 3 residual on this bundle, byte-identical to keeper "
        "11's. The authorized price-tuning channel is replayed BYTE-IDENTICALLY "
        f"(offer_curve_by_group SHA-256 {OFFER_SHA}) and is NOT re-cut, and the "
        "rule-23-frozen thermal_tranches_SPP.csv and campd-unit-outages-short-"
        "SPP.csv are neither regenerated nor touched."
    )
    gov["attested_by"] = _ATTESTED_A if is_a else _ATTESTED_B

    gov.setdefault("measured_input_switches", {})[_GATE] = {
        "value": True,
        "where": (
            "ScenarioConfig.mustrun_commitment_feasibility_clip -> "
            "data/fleet/arrays.py::_compose_min_gen_floors, immediately after the "
            "global np.minimum(min_gen, pmax x availability) clip and before "
            "clear_where_unfloored. Masked on MECH_CC_MUSTRUN_PER_PLANT / "
            "MECH_ST_GAS_MUSTRUN_PER_PLANT, so no other floor is reachable."
        ),
        "identification": "structural-construction",
        "source": (
            "NO measured input, artifact or loader of its own. Both operands are "
            "arrays the LP already holds: the plant-group's available capacity "
            "(sum of pmax x availability over its rows, the SAME basis the "
            "incumbent clip uses) and the committed level the floor asserts (sum "
            "of cc_mustrun_pmin_mw over its floored rows, which is the tranche "
            "artifact's P5-of-online loading)."
        ),
        "warrant": (
            "Rule 17 [R-FLOOR-WINDOW] / 18 [R-PHYSICS]: a commitment is integral, "
            "not linear. The test is the plant's own committed level against its "
            "own available capacity — it introduces NO free parameter (rule 21) "
            "and gates on unit physics rather than a class tuple or plant list."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: PASSES in its strongest form — nothing measured "
            "enters at all, so the rule regenerates in a forecast year identically "
            "and responds to changed conditions through that year's own "
            "EFOR/maintenance envelope. It is deliberately NOT registered in "
            "_BACKCAST_ONLY_OVERLAY_FIELDS. It selects no hours from any meter, so "
            "the CAMPD-online-hours form SPP-46 declared inadmissible is not "
            "reached, and it can only REMOVE an assertion the engine was making — "
            "it never adds, relocates or pins forcing."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: the ONE floor's clip is replaced in the "
            "infeasible hours; nothing is stacked. Machine-verified on the SOLVED "
            "floor arrays — every moved min_gen cell carries control-leg mechanism "
            "id 16 and arm-leg id 0, and the chp_steam and nuclear_mustrun floor "
            "arrays are byte-identical across legs. DISTINCT FROM "
            "mustrun_layup_window_mask, which subtracts a SECOND measured share "
            "and, on an ISO whose outage extract still carries its lay-up windows "
            "(SPP: 1089 of 1089), would double-subtract the identical window."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: ships default False, so every other ISO's "
            "keeper is byte-identical; the mechanism carries NO per-ISO number to "
            "transfer. All nine matrix shards carry the cell — SPP's alone is "
            "non-U."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: registered in ScenarioConfig, in "
            "_CACHE_KEY_OPTIONAL_FIELDS at its declared default (the nyiso-119 "
            "discipline, same commit as the field) and in this bundle's "
            "run_config.json. No env-var knob, no hardcoded per-plant dict, no "
            "getattr fallback literal."
        ),
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=None)
    args = ap.parse_args()
    targets = [args.bundle] if args.bundle else [SPAN_A, SPAN_B]
    for b in targets:
        att = build(b)
        out = b / "calibration_attestation.json"
        out.write_text(json.dumps(att, indent=2) + "\n")
        fp = att["free_parameters"]
        print(
            f"{b.name}: attestation written — "
            f"years_held={att['governance']['authorized_price_tuning']['years_held']} "
            f"n_entries={fp['n_entries']} n_residual={fp['n_residual']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
