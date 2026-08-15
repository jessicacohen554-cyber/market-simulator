"""Write ``calibration_attestation.json`` for the caiso-153 keeper candidate.

The caiso-153 arm is the caiso-151 keeper recipe with **no flag change at all**
— every ``ScenarioConfig`` field is identical. The delta is the CONTENT of two
measured input files the keeper already arms
(``caiso_offer_surface_measured`` / ``caiso_offer_surface_conditional``):
they are re-derived under caiso-152's corrected ``dam-public-bids`` RLE grain
and caiso-153's re-identified gas-coupling classifier.

So this attestation is the caiso-151 keeper's attestation with:

1. a rewritten ``governance.attested_by`` describing the input re-derivation,
2. the caiso-145 **owner** exception ledger **CARRIED FORWARD UNCHANGED IN
   SUBSTANCE**, with each entry's ``magnitude`` re-measured on this bundle, and
3. one new DOF-ledger entry for the measured offer surface — an armed keeper
   input that carried NO ledger entry before, identification ``measured``.

**On carrying the ledger forward.** The three exception rows were adopted by the
owner at caiso-145 (2026-07-30): C3c-2023 and C3c-2024 on caiso-131 §9
disposition A4 with the caiso-144 evidence, and C3a-2025 on the caiso-141 A2
data wall. This session creates **no new caveat and spends no new ledger slot**.

**C3a-2025 moved and the movement is stated, not buried.** Measured against the
same-HEAD zero-delta control on a load-weighted system basis: **+9.42 % →
+9.92 %, i.e. +0.50 pp**. It is reported explicitly against the caiso-145
ledgered caveat exactly as ``PREREG-caiso153`` §7 required, and it does **not**
reopen the caveat: reopening requires new evidence against a named
caiso-140/141/142/143/144 DO-NOT-REDO cell or the owner-funded non-public
hourly pumped-storage intake.

C3c is **bit-identical** across the two arms — model 0 h > $200 in every year,
identical maxima ($188 / $149 / $74).

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso153_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

SOURCE = REPO / "results/calibration/caiso151_clip_B/calibration_attestation.json"
TARGET = REPO / "results/calibration/caiso153_reid_B/calibration_attestation.json"

ATTESTED_BY = (
    "caiso-153 (2026-08-02): the caiso-151 keeper recipe with NO flag change — "
    "every ScenarioConfig field is byte-identical to the control. The delta is "
    "the CONTENT of the two measured offer-surface files the keeper already "
    "arms, re-derived under caiso-152's corrected dam-public-bids RLE grain "
    "(the parser carried only 47.9 % of real GENERATOR EN curve-hours, "
    "dropping exactly the stable-bid ones, and charged 18.0 % of them to the "
    "wrong net-load bin) and caiso-153's RE-IDENTIFIED gas-coupling "
    "classifier. FINDING-caiso152 §F left this input UNREPRODUCIBLE: the "
    "committed artifact could not be regenerated from its own script and "
    "corpus (25 CT units vs the recorded 102, G1 0.235 vs the recorded 1.416 "
    "PASS). caiso-153 diagnoses that as ESTIMATOR ATTENUATION, not the body "
    "probe FINDING-caiso152 §I proposed: the CA-composite citygate reaches "
    "$24.29/MMBtu in January 2023 against a 2023-25 median near $3-4, so the "
    "pooled OLS slope is levered on a few days of one month of one year and "
    "attenuates toward zero for any resource that did not track that spike "
    "proportionally, while its correlation survives — precisely the r >= 0.6 "
    "with slope < 4 MMBtu/MWh population that is physically impossible for a "
    "thermal unit. Identified on a frozen 3x3 body-probe x estimator grid "
    "(PREREG-caiso153 §4) over the full contiguous 1,095-day corpus, selected "
    "by a rule declared EX ANTE and BLIND to both the derive gates and the "
    "committed artifact (PREREG §5): physical level-identity admissibility "
    "(implied non-fuel adder <= $20/MWh against a $2.0-3.5 VOM) applied FIRST, "
    "then out-of-sample split-half slope stability. All three OLS cells are "
    "inadmissible ($32.7-37.5/MWh); all six Theil-Sen / TRIM cells are "
    "admissible ($9.6-12.7). Winner P035_TS keeps the INCUMBENT body probe and "
    "changes only the estimator. ZERO new free parameters and no threshold "
    "moved: hr_cut stays 8.5 and G1-G4 stay frozen (rule 23 "
    "[R-FROZEN-DERIVE]), and the unmodified deriver then passes ALL FOUR on "
    "the re-identified classifier — G1 CC 0.871 / CT 1.306 (vs 0.876 / 0.235 "
    "on the incumbent), G2/G3/G4 PASS. Corroboration the selection rule never "
    "saw: the re-derived static bands reproduce the COMMITTED artifact to "
    "within tolerance everywhere (max delta +0.053 on CC peak against a 0.133 "
    "tolerance), and the SHIPPED deriver reproduces this bundle's artifact "
    "exactly — restoring the reproducibility FINDING-caiso152 §F found absent. "
    "Single-delta A/B against a same-HEAD zero-delta control solved in the "
    "same session; every criterion verdict is UNCHANGED and both protective "
    "gates (C7 shape, C8 forced share) PASS on both arms. The corrected input "
    "costs +0.04-0.06 $/MWh of DA price MAE, which rule 1 [R-STRUCT] and rule "
    "14 [R-ACCURATE] make a discovered-cost to record rather than a reason to "
    "revert an accurate measured input. Evidence: FINDING-caiso153, "
    "PREREG-caiso153, FINDING-caiso152 §F/§I."
)

CARRY = (
    "CARRIED FORWARD from the caiso-151 keeper unchanged in substance; "
    "originally adopted by the OWNER at caiso-145 (2026-07-30). caiso-153 "
    "creates no new caveat and spends no new ledger slot. "
)

REMEASURED = {
    ("price_tail", 2023): (
        "RE-MEASURED on caiso153_reid_B: model 0 h > $200 (max $188) vs RT "
        "actual 47 h — BIT-IDENTICAL to the same-HEAD control. "
    ),
    ("price_tail", 2024): (
        "RE-MEASURED on caiso153_reid_B: model 0 h > $200 (max $149) vs RT "
        "actual 35 h — BIT-IDENTICAL to the same-HEAD control. "
    ),
    ("price_mean", 2025): (
        "RE-MEASURED on caiso153_reid_B: +9.92 % vs RT actual, against the "
        "same-HEAD control's +9.42 % (load-weighted system basis) — a movement "
        "of +0.50 pp, reported explicitly as PREREG-caiso153 §7 required. "
        "Stated, not built upon; the caveat is NOT reopened by it. "
    ),
}

NEW_DOF = {
    "name": (
        "caiso_offer_surface_measured + caiso_offer_surface_conditional / "
        "caiso_offer_curve_measured.json + caiso_offer_surface_condbinned.json"
    ),
    "where": (
        "config.scenarios ScenarioConfig fields -> "
        "data.fleet.build_caiso_offer_surface_conditional_markup and the "
        "measured static band replacement of _CAISO_OFFER_CURVE's gas "
        "multipliers; artifacts under data/raw/_validation-source/"
    ),
    "identification": "measured",
    "lineage_solves": (
        "1 A/B (caiso-153), single-delta vs a same-HEAD zero-delta control; "
        "the mechanism itself was armed at caiso-51"
    ),
    "source": (
        "CAISO OASIS Public Bid Data (PUB_DAM_GRP, 90-day lag) — every DAM "
        "energy bid AS SUBMITTED, full contiguous 2023-2025 span (1,095 trade "
        "days; 2023-06-01 is the documented OASIS archive hole), at the "
        "datatype's declared per-hour grain after caiso-152's RLE expansion. "
        "Gas resources are identified WITHOUT fuel or physics columns (the "
        "feed is masked) by the physics of daily fuel-cost passthrough: a "
        "per-resource THEIL-SEN regression of the daily body bid on the "
        "CA-composite citygate series placed on gas flow days, whose slope IS "
        "the marginal heat rate. Theil-Sen rather than least squares is the "
        "caiso-153 re-identification: the regressor's variance is dominated "
        "by the January-2023 spike, which attenuates an OLS slope toward zero "
        "while leaving its correlation intact. The estimator was selected on "
        "a frozen grid by an ex-ante rule blind to the derive gates and to "
        "the committed artifact, so it is not fitted to either. NO fitted "
        "scalar and NO tuned threshold: hr_cut, the gas gates and G1-G4 are "
        "frozen against residuals per rule 23 [R-FROZEN-DERIVE] and re-run "
        "only on a source-corpus change — here, caiso-152's grain correction. "
        "Forward-reproducible (rule 13 [R-MEASURED]): OASIS publishes "
        "continuously at a 90-day lag, the multipliers are ratios to a "
        "forward-driver basis (citygate gas + CARB allowance at the class "
        "base heat rate), so they apply unchanged in a forecast year."
    ),
    "root_cause": (
        "CLOSED by caiso-153: FINDING-caiso152 §F recorded this armed keeper "
        "input as not reproducible from its own script and corpus. The "
        "shipped deriver now regenerates this bundle's artifact exactly."
    ),
}


def main() -> int:
    """Write the caiso-153 attestation from the caiso-151 keeper's."""
    att = json.loads(SOURCE.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY

    for exc in att["exceptions"]:
        key = (exc.get("criterion"), int(exc.get("year", 0)))
        if key in REMEASURED:
            exc["magnitude"] = REMEASURED[key] + "PRIOR MAGNITUDE: " + exc["magnitude"]
        exc["reason"] = CARRY + exc["reason"]
        exc["carried_from"] = (
            "2026-07-31-caiso-151-firm-selfsched -> "
            "2026-07-31-caiso148-nuclear-availability -> "
            "2026-07-31-caiso147-chp-heat-rates -> "
            "2026-07-29-caiso139-dump-guard-offer (owner ledger, caiso-145)"
        )

    dof = att["free_parameters"]
    dof["entries"] = [e for e in dof["entries"] if e.get("name") != NEW_DOF["name"]] + [
        NEW_DOF
    ]
    dof["n_entries"] = len(dof["entries"])
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e.get("identification") == "residual"
    )

    TARGET.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {TARGET}")
    print(f"  exceptions carried: {len(att['exceptions'])}")
    print(
        f"  DOF entries: {dof['n_entries']} ({dof['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
