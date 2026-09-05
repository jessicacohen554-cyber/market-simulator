"""Generate miso170_layup_B2's calibration attestation from the keeper's.

Arm-2 of the miso-170 lay-up membership correction: the keeper recipe
(2026-08-19-miso-170-membership, which already carries the census ledger
entry) with the SAME census re-stamped at SITE grain into the reliability
coefficient CSV (PREREG-miso170 §7 dated amendment) — no new ScenarioConfig
field, no new ledger entry, zero new scalars. Only the governance narrative
and disclosures move: the K-1 residual is repaired substantively (Burlington's
CT_PEAKER floor removed on the site's own conduct) rather than by
re-attributing the instrument.
"""

import json

SRC = "results/calibration/miso170_membership_B/calibration_attestation.json"
DST = "results/calibration/miso170_layup_B2/calibration_attestation.json"

d = json.load(open(SRC))

d["governance"]["attested_by"] = (
    "ARM-2 - THE SITE-GRAIN RE-STAMP OF THE KEEPER'S OWN CENSUS, NO NEW "
    "MECHANISM AND NO NEW LEDGER ENTRY: reliability_floor_plant_exclusions="
    "true + mustrun_plant_exclusions=true over the SAME 15-plant lay-up "
    "census the keeper carries, with patch_reliability_coeffs amended to "
    "stamp each census SITE on every (zone, plant_class) limb its model "
    "tranches occupy (PREREG-miso170-stgas-floor-membership-2026-08-19.md "
    "SS7, dated amendment committed BEFORE arm-2 solved; 9 CT_PEAKER-limb "
    "cells change, first-17-column identity byte-verified, census CSV "
    "byte-identical, default cache key unmoved at 603c2498bf71d21d). "
    "miso-170b, 2026-08-19. Arm-2 is a replay_keeper re-solve of the "
    "miso-169 recipe with both exclusion flags via --set, --year 2023 2024 "
    "2025 in ONE invocation, years sequential (rules 12/16). CONTROL "
    "BIT-IDENTITY holds through the chain: the canonical miso-170 control "
    "(2026-08-19-miso-170-control) reproduces the miso-169 keeper at "
    "max|diff|=0 on all scored sidecars, and this session's independently "
    "solved pair (miso170_layup_A/B) reproduces miso170_membership_A/B "
    "BIT-IDENTICALLY (probe --identity, max|diff|=0 every scored sidecar "
    "every year) - an independent replication that also proves the "
    "intervening ERCOT/NYISO/CAISO merges MISO-inert. GATES (arm-2 vs the "
    "canonical control, results/calibration/_miso170b_sitegrain_ab.json): "
    "K-1 PASS - ZERO census rows remain on either mechanism in any year "
    "(the SS7 repair repairs); K-2 liveness PASS in band all years (shed "
    "0.5336/0.8766/0.9487 TWh vs predicted 0.5044/0.7531/0.7853 +/-50%); "
    "K-3 PASS (D-4 conduct failures 18 -> 1, ZERO new, the pre-named 1402 "
    "survivor present); K-5 PASS (zero record-grain PASS->FAIL flips); K-6 "
    "PASS (ST_GAS D-1 shape held, profile_r 0.951/0.958/0.975, cv_ratio "
    "1.422/1.109/1.265). K-4: C8 ST_GAS 2024 AND 2025 both FAIL -> PASS "
    "(grounded above budget - all binding mechanisms clear D-4); 2023 stays "
    "FAIL on plant 1402 exactly as pre-registered. ALL KILLS SILENT: the "
    "candidate rule of PREREG SS6 is met without the structure-over-gates "
    "clause. Rule 22: no year outside 2023-2025 was solved, scored or "
    "registered; MISO holds neither complete nor final and the holdout "
    "spend freeze is untouched."
)

d["disclosures"]["miso170b_note"] = (
    "miso-170b (arm-2) disclosures. (a) THE K-1 RESIDUAL IS REPAIRED "
    "SUBSTANTIVELY, NOT RE-ATTRIBUTED: Burlington (1104)'s CT_PEAKER "
    "tranches - 777/763 unit-hours under the MISO-Plains CT netload limb "
    "with the SITE metered dark in 98.7%/91.8% of exactly those binding "
    "hours - are excluded because the census verdict is computed on the "
    "facility-summed meter, every unit included: lay-up is a property of "
    "the SITE and the majority-class-only stamping under-implemented the "
    "prereg's own identification (rule 17 [R-FLOOR-WINDOW]). The "
    "keeper-disclosure instrument item STANDS SEPARATELY: "
    "aggregate_floors_by_plant still labels a mixed-class plant by its "
    "most common unit group, which affects any ISO with mixed-class sites "
    "- an open cross-ISO scorer item, now decoupled from MISO's C8. "
    "(b) C8 STILL FAILS 2023 on plant 1402 (the pre-registered expected "
    "survivor): the per-plant must-run window is an online_frac POOLED "
    "over 2023-2025 (0.508) against per-year metered online shares "
    "0.2495/0.6134/0.6548 - a ~2.3x 2023 over-commitment that is a REAL "
    "window defect with its own named successor (per-year online_frac; "
    "own prereg, own A/B, own DOF answer). 1402 is NEVER added to the "
    "census to buy 2023. (c) C3a-2025 is UNCHANGED at the keeper's level "
    "to the reported digit - the CT floor removed is ~0.01 TWh across "
    "three years - and the determination stays NOT-YET on C3a-2025 plus "
    "C8-2023; nothing here is claimed against the miso-163/miso-170 "
    "model-class rulings. (d) The site-grain stamps for 1464/2123/6358 "
    "CT_PEAKER limbs are GUARDS, measured live-inert: no arm floors those "
    "sites' CT tranches in any solved year."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    "attestation written;",
    d["free_parameters"]["n_entries"],
    "ledger entries /",
    d["free_parameters"]["n_residual"],
    "residual",
)
