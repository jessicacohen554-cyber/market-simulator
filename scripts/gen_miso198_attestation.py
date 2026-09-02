"""Generate miso198_oom_B's calibration attestation from the keeper's.

The arm is the miso-191 keeper recipe plus exactly one zero-residual-DOF
mechanism (the gen_miso186/187/188 attestation pattern): its attestation is
the superseded keeper's with one MEASURED-identified ledger entry for the
out-of-merit re-conditioning of the ST_GAS must-run floor's LEVEL, a
rewritten ``governance.attested_by`` for the miso-198 A/B, and this
session's disclosures appended AT FULL MAGNITUDE — the C3a-2023 adverse
face, the fact that NO criterion status moves at all, and the scorer's own
mis-ordered verdict line, all included. ``n_residual`` is UNCHANGED at 2:
the arm swaps one measured statistic's conditioning set for another and
introduces no fitted scalar. Exceptions carry unchanged.
"""

import json

SRC = "results/calibration/miso191_bax_B/calibration_attestation.json"
DST = "results/calibration/miso198_oom_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "st_gas_mustrun_oom_level (boolean arm)",
        "where": (
            "ScenarioConfig.st_gas_mustrun_oom_level -> "
            "data/fleet/campd_bins.py::thermal_tranche_oom_level -> the "
            "st_gas_mustrun_p25_level gather block of "
            "data/fleet/arrays.py::_compose_min_gen_floors. Population "
            "data/raw/_processed-legacy/thermal_tranches_oom_level_mw_MISO.csv, "
            "written by scripts/data/derive_thermal_tranche_oom_level_mw.py, "
            "which IMPORTS the frozen deriver's online mask, parasitic-factor "
            "net, derate source, nameplate clamp and pooled window unchanged "
            "(rule 23) and differs from it in the CONDITIONING SET alone"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0. The level is the SAME frozen percentile (p25) over the SAME "
            "pooled 2023-2025 window as the incumbent, computed over the "
            "miso-197 W3b out-of-merit hour set — hours in which the measured "
            "MISO CC_REGULAR fleet ran below 0.90 of its own p99.5 that year, "
            "i.e. cheaper CC capability demonstrably idle. Purely measured: no "
            "model dispatch, no price, no residual anywhere in the path. The "
            "SELECTION rule that admitted this candidate over three others was "
            "frozen and pushed at 88bf6af4 BEFORE any candidate's level or "
            "assertion was computed"
        ),
        "value": (
            "True (the arm carries no numeric parameter of its own; it swaps "
            "which hours the frozen percentile is taken over). Effect on the "
            "seven floored plants, cap-weighted: Sabine 286.1 -> 256.1 MW, "
            "Nine Mile Point 724.0 -> 688.0, Greenwood 89.0 -> 66.0, Lewis "
            "Creek 113.5 -> 107.7, Harding Street 226.4 -> 218.0, Little "
            "Gypsy 53.0 -> 50.0, Ames unchanged. Membership, window, mechanism "
            "id and the cheapest-first pmax x availability clip are untouched "
            "(rule 19): the SAME 7 plants are floored with an IDENTICAL "
            "floored-hour mask, verified single-delta before any solve. Raw "
            "floor assertion 10.523/11.022/11.086 -> 9.932/10.386/10.441 TWh; "
            "over-assertion share (energy asserted in hours the plant's own "
            "meter says it did not operate) 0.081/0.072/0.065 -> "
            "0.070/0.067/0.057, i.e. the arm is STRICTLY less pinning than "
            "the incumbent on the D-4 conduct direction"
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: st_gas_mustrun_oom_level=true. "
    "miso-198, 2026-09-01. PREREG results/calibration/"
    "PREREG-miso198-stgas-oom-level-2026-09-01.md was committed, pushed and "
    "blob-verified BEFORE either leg solved and BEFORE the arm existed; the "
    "two zero-solve instruments behind it (_miso198_stgas_oom_conduct_phase0.py "
    "frozen at 33facea4 and repaired at 9ad6b25c, _miso198_level_selection.py "
    "frozen at 88bf6af4) each had their rule frozen in their own docstring and "
    "pushed BEFORE any adjudicating quantity was computed. The A/B scorer "
    "(scripts/probes/_miso198_ab_gates.py) was itself committed BLIND, while "
    "the control leg was still solving and before any arm result existed. Both "
    "legs are replay_keeper re-solves of the 2026-08-30-miso-191-bexit "
    "keeper's own recipe, years 2023 2024 2025 in ONE invocation each, years "
    "sequential, legs sequential (rules 12/16 - the MISO per-plant LP peaks "
    "~13.5 GB anon RSS on this 15 GB box and OOM-killed once at 13.95 GB, so "
    "two concurrent invocations do not fit); the arm's single delta rode the "
    "sanctioned replay_keeper --set channel and both legs ran at ONE HEAD. "
    "CONTROL BIT-IDENTITY (S-0): 2026-09-01-miso-198-control reproduces the "
    "committed keeper with max|diff| = 0.0 on all 12 scored sidecars of every "
    "year, despite 39 commits of main landing underneath this branch mid-"
    "session (scenarios.py and policy/carbon.py among them) - the MISO solve "
    "path is unchanged and the comparator is sound. S-1 PASS: exactly one "
    "delta over the 763-field scenario_config dump. S-2 FLOOR LIVENESS PASS: "
    "the floor's own D-2 forced energy falls 0.4798/0.5892/0.5878 TWh against "
    "the pre-registered 0.5914/0.6366/0.6455 (81/93/91 % realised conversion), "
    "in band all three years. EVERY PRE-REGISTERED KILL SILENT: K-1 the "
    "ex-ante-NAMED CC_REGULAR-2024 and CC_REGULAR-2023 both PASS -> PASS "
    "(2024 lands +6.748 TWh against its +-8.00 band, using 0.084 of 1.336 TWh "
    "of headroom); K-2 C3b 0.081/0.108/0.182 -> 0.081/0.108/0.181; K-3 zero "
    "D-4 conduct failures and zero new; K-4 D-1 ST_GAS profile_r "
    "0.942/0.957/0.977 -> 0.941/0.957/0.978 (gate 0.80) and cv_ratio "
    "1.755/1.227/1.453 -> 1.794/1.252/1.490 (gate 0.50); K-5 ZERO PASS -> "
    "non-PASS flips across every scored record; K-6 UNSCORED, not passed - "
    "replay bundles carry no attestation, which is why this one is generated "
    "post hoc from the superseded keeper's by the established "
    "gen_miso186/187/188 pattern. THE DIRECTION WAS PRE-REGISTERED AND IT "
    "REVERSED THE INHERITED ONE: FINDING-miso197 §8(1) pre-registered "
    "CC_REGULAR-2024 DOWN / ST_GAS-2024 UP at confidence 0.85; the admissible "
    "level is LOWER than the incumbent at every floored plant, so PREREG-"
    "miso198 §2 declared the reversal - ST_GAS DOWN, CC_REGULAR UP - in "
    "writing before the solve, and the arm delivers exactly that (ST_GAS "
    "-0.145/-0.145/-0.222 TWh, CC_REGULAR +0.087/+0.084/+0.135). WHAT IT BUYS "
    "IS STRUCTURAL INTEGRITY, NOT FIT: C8 ST_GAS forced share falls in all "
    "three years, 0.2196 -> 0.2001, 0.2342 -> 0.2100, 0.3423 -> 0.3186, "
    "taking 2025 2.4 pp off its grounded over-budget note. NO CRITERION "
    "STATUS MOVES AT ALL and the determination is UNCHANGED at NOT-YET on "
    "{C3a-2025}, C3c the single ledgered caveat. PROMOTED ON RULE 1 "
    "[R-STRUCT] - 'a run is a keeper because it is the most structurally "
    "faithful, not because it has the lowest MAE' - plus the owner's standing "
    "in-session instruction that a run improving structural integrity may be "
    "promoted even where gates regress; here nothing regresses. The incumbent "
    "level was a low percentile of each plant's output over EVERY hour it was "
    "online (its OPERATING RANGE); the phenomenon the floor represents is "
    "that MISO's VLR/self-committed steamers hold load in the hours merit says "
    "shut down, and the arm measures THAT. LOYO within 2023-2025: the "
    "mechanism carries ZERO fitted parameters and its identification is a "
    "pooled multi-year percentile over a published-record hour set, so no "
    "year's parameter was identified against any year's outcome; per-year "
    "effects are reported at full magnitude above. n_residual UNCHANGED at 2. "
    "Rule 22: no year outside 2023-2025 was solved, scored or registered; "
    "MISO holds neither marker and the holdout spend freeze is untouched."
)

d["disclosures"]["miso198_ab"] = (
    "A/B verdict record: results/calibration/_miso198_ab_gates.json "
    "(S-0/S-1/S-2 + K-1..K-6, none of which fire). DISCLOSURES AGAINST "
    "INTEREST. (1) THE FROZEN SCORER'S OWN VERDICT LINE READS 'INERT - every "
    "scored record identical', and that label is WRONG: it computes "
    "records_identical from criterion STATUSES and orders that branch ahead "
    "of the kills-silent branch, so a run that moves every value without "
    "flipping a status reads as inert. The arm is demonstrably NOT inert - "
    "S-2 passes and C1, C3a, C3b and C8 all move. The defect is in the "
    "verdict ORDERING; it was found only AFTER the numbers were read, and it "
    "is recorded here rather than repaired in the frozen file, so the "
    "scorer's mechanical output stands unaltered on the record. (2) C3a-2023 "
    "WORSENS, +0.0913% -> +0.1522% (+0.061 pp adverse), reported at full "
    "magnitude. The C3a face was pre-registered UP - the direction that would "
    "HELP the sole failing criterion - precisely so that the 2024 (-4.5511 -> "
    "-4.4892) and 2025 (-12.3405 -> -12.2745) improvements could never be "
    "presented as the reason the arm was kept; they are reported and they are "
    "NOT the justification (rule 1). (3) NO CRITERION IMPROVES ITS STATUS. "
    "This promotion buys a better-grounded level and less forced energy, and "
    "nothing else; the determination is unchanged. (4) THIS KEEPER DOES NOT "
    "FIX THE DOMINANT DEFECT. The miso-198 census partitioned the ST_GAS "
    "out-of-merit gap EXACTLY (identity, residual 0.0e+00) into "
    "population/window/LEVEL at 0.162/0.197/0.640, 0.138/0.163/0.699, "
    "0.183/0.153/0.665 - LEVEL dominant 3 of 3 - and yet the level family is "
    "EXHAUSTED: under a criterion frozen before any candidate's number, only "
    "the most conservative candidate was admissible and it is LOWER than the "
    "incumbent. The candidates that would have recovered the ~4-5 TWh/yr buy "
    "about half of it by asserting 2.02/1.79/2.10 TWh/yr in hours the plants' "
    "own meters say they did not operate (1.65-2.12x the incumbent's "
    "over-assertion share), which rule 17 [R-FLOOR-WINDOW] makes a bug by "
    "definition. The binding defect is the floor's WINDOW BASIS - it ranks "
    "hours by SYSTEM LOAD while the conduct's own hour set is the plant's "
    "COMMITMENT STATE - and that is the named successor, NOT another level "
    "move. (5) The population channel is NOT repaired: only 5 of the 10 "
    "plants in it pass the lay-up census's own operating test, so "
    "mustrun_plant_exclusions' cycler/mothball boundary (R D Green 6639 reads "
    "laid_up=True at an online_share of 0.326 with 0.42 TWh/yr metered) is a "
    "named, unrepaired object. (6) ST_CHP is effectively INVISIBLE to CEMS "
    "(0.0004/0.0004/0.0022 TWh measured against a C1 deficit of "
    "-2.96/-2.93/-2.13), so no CAMPD-conditioned statistic can identify it; "
    "its D-1 profile_r is negative in every year (-0.809/-0.733/-0.650, "
    "ungated) and it belongs to chp_steam_following's EIA-923 basis. CT_CHP "
    "IS visible but through only 5 of 41 model-class plants. (7) INSTRUMENT "
    "DEFECT, found and repaired BEFORE the adjudicating record: the first "
    "census run omitted load_shape, and the runtime floor block falls through "
    "to an all-hours target without it (arrays.py:2841), collapsing the "
    "window channel into the level channel. Repaired to read the solve's own "
    "demand.sum(axis=0) from the keeper's committed hourly/system_<year> "
    "sidecar, pushed and blob-verified at 9ad6b25c before the record was "
    "written; it moved W 0.355/0.118/0.099 -> 1.548/1.733/1.360 and L "
    "5.584/8.276/6.394 -> 5.024/7.420/5.924 and did NOT move the verdict. "
    "(8) D-1 cv_ratio rises slightly on ST_GAS (1.755/1.227/1.453 -> "
    "1.794/1.252/1.490) - movement away from 1.0, well inside the 0.50 gate, "
    "disclosed. (9) The solve builds the ST_GAS floor TWICE per year with "
    "DIFFERENT values (control 2023 11.29 then 10.52 TWh); the second is "
    "load-bearing and the probes match it to 2 dp on every year and both "
    "legs. This independently re-confirms miso-196's incidental finding that "
    "_CC_PMAX_RECONCILED_PLANTS (eia860.py:776) is a last-writer-wins global "
    "whose first build differs from later ones - a named, unchartered "
    "solve-affecting defect, not repaired here. (10) Not this lane's but "
    "recorded: 11 tests/unit/config cache-key pin tests fail on clean main "
    "because the capx-d24 repair deliberately moved the default key "
    "(603c2498bf71d21d -> 7a57fadff595ca83, owner ruling Q20 b') without "
    "updating its literal pins; verified pre-existing by stashing this "
    "session's changes."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
