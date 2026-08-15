"""Write ``calibration_attestation.json`` for the caiso-146 keeper candidate.

The caiso-146 arm is the caiso-139 keeper recipe with ONE delta —
``measured_ct_heat_rates=true`` on CAISO's own newly-derived CAMPD artifact — so
this attestation is the caiso-139 keeper's attestation with:

1. a rewritten ``governance.attested_by`` describing the single delta,
2. the caiso-145 **owner** exception ledger **CARRIED FORWARD UNCHANGED IN
   SUBSTANCE**, with each entry's ``magnitude`` re-measured on this bundle, and
3. one new DOF-ledger entry for the mechanism, identification ``measured``.

**On carrying the ledger forward.** The three exceptions were adopted by the
owner at caiso-145 (2026-07-30) — two caveats over three rows: C3c-2023 and
C3c-2024 on caiso-131 §9 disposition A4 with the caiso-144 evidence, and
C3a-2025 on the caiso-141 A2 data wall. This session creates **no new caveat and
spends no new ledger slot**: it re-states the owner's own dispositions against a
bundle whose measurements for both are materially unchanged (C3c is
**bit-identical** — model 0 h in every year of both arms; C3a-2025 moves
$38.28 → $38.16, +11.3 % → +11.0 %, i.e. 0.3 pp, well inside the 1.0 pp
materiality trigger the caiso-146 prereg §8 fixed in advance). Each carried
entry records its provenance explicitly so the owner's act stays attributable
and is never mistaken for a fresh grant by this session.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso146_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

SOURCE = REPO / "results/calibration/caiso139_dumpguard_B/calibration_attestation.json"
TARGET = REPO / "results/calibration/caiso146_ctheatrate_B/calibration_attestation.json"

ATTESTED_BY = (
    "caiso-146 measured-CT-loaded-heat-rate keeper session 2026-07-31. SINGLE-flag "
    "delta on the caiso-139 dump-guard keeper recipe: measured_ct_heat_rates=true "
    "(rule 19 [R-ONE-MECH] — one mechanism, nothing stacked). ZERO new free "
    "parameters that are fitted (rule 24): the applied map is CAISO's own CAMPD "
    "artifact, data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv, written by "
    "scripts/data/derive_campd_ct_heat_rates.py --iso CAISO --years 2023 2024 2025 "
    "at this session's HEAD. Every value in it is a measured loaded heat rate — per "
    "unit, sum(heatInput)/sum(grossLoad) over hours at >=0.80 x that unit's own p95 "
    "gross load (>=50 qualifying hours), converted to the NET basis by the SAME "
    "committed parasitic-factor artifact the benchmark's own net actual uses, then "
    "generation-weighted across a plant's turbines. No threshold, percentile, "
    "margin, multiplier or residual-derived value enters, and no parameter was "
    "chosen with reference to any residual. "
    "WHY IT IS CHARTERED (rule 14 [R-ACCURATE]): eGRID publishes ONE PLANT-AVERAGE "
    "ANNUAL heat rate, which the non-ERCOT fleet loader hands every combustion "
    "turbine. That number is wrong twice for a peaker — an annual average blends "
    "startup fuel and part-load tails into the figure that sets the offer, and at a "
    "mixed facility it is not even the right technology's rate. CAISO's Glenarm "
    "(plant 422) is the second defect in the flesh and is in this artifact: the "
    "model carries 4 CT_PEAKER units (138.4 MW) AND 2 CC_REGULAR units (84 MW) "
    "there on a single eGRID figure of 10.3895, while CAMPD tags GT3/GT4 as "
    "'Combustion turbine' and GT5 as 'Combined cycle'; the artifact prices the "
    "turbines at their own measured 10.6702 and leaves the CC blocks alone. "
    "RULE 13 [R-MEASURED] ADMISSIBILITY: a unit's loaded heat rate is a physical "
    "characteristic of the machine, it regenerates for a forward year from the same "
    "pipeline, and it responds to changed conditions (a retrofit moves it; a new "
    "unit carries its design rate) — an INPUT, never a measured outcome fed back to "
    "close a residual. It also clears caiso-119 R4's own standing guardrail, which "
    "forbids 'marking peaker offers down until 4 TWh appears': the magnitude here is "
    "set by the meter, not by the gap, and the prereg predicted +0.1 to +0.8 TWh "
    "against a ~4 TWh miss BEFORE the solve. "
    "COVERAGE: 43 plant rows, ALL flag=='ok' (zero excluded by the physical band); "
    "76.8 % of CT_PEAKER capacity but 99.9 % of the class's own metered CAMPD CT "
    "energy (8.015/8.025 TWh). The 90 uncovered plants are the Part-75 reporting "
    "boundary — median 2.2 MW and ZERO metered CT energy, so there is nothing to "
    "swap in and they correctly keep eGRID; no adverse selection (covered "
    "capacity-weighted eGRID HR 10.819 vs uncovered 11.004). The swap is one-sided "
    "in CAISO — 41 plants / 5,649 MW cheaper vs 2 plants / 198 MW dearer, "
    "capacity-weighted -1.159 MMBtu/MWh (-10.7 %), generation-weighted -0.884 "
    "(-8.9 %) — which differs from the NYISO and PJM precedents and is reported as "
    "CAISO's own result (rule 25 [R-ISO-SCOPE]: no verdict or parameter transferred; "
    "CAISO's artifact is derived from CAISO's data). "
    "PRE-REGISTERED GATES (PREREG-caiso146-ct-heat-rates-2026-07-31.md, committed and "
    "pushed BEFORE either arm solved) ALL PASS: K1 flag fidelity (B true / A false, "
    "43/43 rows applied); K2 control integrity on the pre-registered scorecard basis "
    "(arm A reproduces the keeper's criterion statuses — the same {C3a, C3c} failing "
    "set, everything else PASS); K3 liveness (max |delta CT_PEAKER| 1660/1510/1709 MW, "
    "far above the 50 MW floor); K4 single delta (run_config differs in exactly the "
    "one boolean); K5 year span [2023, 2024, 2025] with no out-of-training year "
    "(rule 22 — CAISO holds NO calibration-complete marker and none was written); K6 "
    "the Delano broken-meter sensitivity (the class move survives excluding plant "
    "58122 with the same sign at 80/84/66 % of its size). "
    "RESULT: CT_PEAKER — the most under-produced class in the ISO and caiso-119 R4's "
    "named defect — moves materially toward reality in all three years, 1.088 -> "
    "1.727 / 0.423 -> 0.634 / 0.272 -> 0.455 TWh against actuals 4.128/4.326/2.374, "
    "i.e. 26 % -> 42 %, 10 % -> 15 %, 11 % -> 19 % of measured. The displaced energy "
    "is CC_REGULAR (-0.399/-0.130/-0.093 TWh, 94->93 / 94->93 / 90->90 % of actual, "
    "a ~1 pp cost against a 5-16 pp gain), ST_GAS and imports. Every criterion "
    "verdict is UNCHANGED from the control; C3a improves slightly in all three years "
    "(+3.6->+2.8 %, +8.2->+7.8 %, +11.3->+11.0 %) and C3c is BIT-UNCHANGED (model 0 h "
    "in every year of both arms). PROTECTIVE GATES HOLD AND IMPROVE: C7/D-1 "
    "CT_PEAKER profile_r 0.903/0.951/0.837 -> 0.885/0.936/0.864, all above the 0.80 "
    "floor, and 2025 — the keeper's most exposed number, with only 0.036 of headroom "
    "— IMPROVES; cv_ratio 2.635/2.048/2.087 -> 1.613/1.805/2.172 moves TOWARD the "
    "measured off-peak variability in two of three years; C8/D-2 forced share "
    "0.0032/0.0104/0.0012 -> 0.0016/0.0055/0.0007 against a 0.15 peaker cap, falling "
    "because the denominator grew. D-4 off-window binding stays 0.000 on every "
    "floor; this arm arms no floor. "
    "REPORTED, NOT TUNED TOWARD (prereg §8): the ledgered C3a-2025 caveat moves "
    "0.3 pp (+11.3 % -> +11.0 %), well inside the 1.0 pp materiality trigger fixed in "
    "advance, so no leave-one-year-out re-scoring was required and the lever is NOT "
    "offered as a C3a or C3c lever. It does not close either ledgered caveat and was "
    "not selected to. "
    "OPEN ITEM CARRIED (not caused by this arm, and reported rather than buried): "
    "the caiso-139 keeper's COMMITTED sidecars no longer reproduce at HEAD. The "
    "zero-delta control diverges from the committed keeper by up to 2.1/1.7/3.2 GW "
    "on a class-hour, netting to a CC_REGULAR <-> import swap of +0.45/+0.46/+0.85 "
    "TWh with total generation identical to three decimals and CA lambda +$0.19/"
    "+$0.06/+$0.14. It does NOT touch CT_PEAKER (+0.007/0.000/0.000 TWh), so the A/B "
    "signal — an order of magnitude larger — is unaffected, and both arms sit at the "
    "SAME HEAD with one flag between them, which is why a same-HEAD control was "
    "solved rather than comparing against the committed keeper (the neiso-69 "
    "drift-control precedent). Promoting this arm re-bases CAISO's keeper onto HEAD "
    "so the committed bytes reproduce again. The drift's cause is NOT identified "
    "here — 15 commits touched src/market_sim between the keeper's basis "
    "(fa9971b) and HEAD (db02071) — and bisecting it needs full solves, so it is "
    "filed as an open item, not silently absorbed."
)

#: Provenance stamp prepended to each carried exception's ``reason``.
CARRY = (
    "CARRIED FORWARD UNCHANGED from the caiso-139 keeper's ledger by caiso-146 "
    "(2026-07-31, single-flag measured_ct_heat_rates delta). This session creates NO "
    "new caveat and spends NO new ledger slot — the disposition below is the OWNER's "
    "act of 2026-07-30 (caiso-145), re-stated against a bundle whose measurement for "
    "it is materially unchanged, with the magnitude field re-measured on this "
    "bundle's own bytes. ORIGINAL REASON FOLLOWS. "
)

#: Per-(criterion, year) magnitude re-measured on the caiso-146 arm-B bundle.
REMEASURED = {
    ("price_tail", 2023): (
        "model 0h [energy-only LMP] vs RT actual 47h (0.00x, >$200) — BIT-IDENTICAL "
        "to the control and to the caiso-139 keeper; the CT re-price buys zero tail "
        "hours, exactly as the caiso-146 prereg §5.5 predicted in advance. "
    ),
    ("price_tail", 2024): (
        "model 0h [energy-only LMP] vs RT actual 35h (0.00x, >$200) — BIT-IDENTICAL "
        "to the control and to the caiso-139 keeper; the CT re-price buys zero tail "
        "hours, exactly as the caiso-146 prereg §5.5 predicted in advance. "
    ),
    ("price_mean", 2025): (
        "model $38.16 vs RT actual $34.39 = +11.0% (band ±10%, so the overshoot "
        "beyond band is +1.0 pt), against the caiso-139 keeper's +10.9% and this "
        "session's own control at +11.3%. The measured CT re-price moves it 0.3 pp — "
        "INSIDE the 1.0 pp materiality trigger the prereg fixed before the solve, so "
        "no leave-one-year-out re-scoring was triggered and nothing was tuned toward "
        "this residual. The caveat stands on the caiso-141 A2 data wall, unchanged. "
    ),
}

NEW_DOF = {
    "name": "measured_ct_heat_rates",
    "where": "run_config.scenario_config.measured_ct_heat_rates",
    "identification": "measured",
    "lineage_solves": "1 (caiso-146 A/B, 2026-07-31)",
    "value": True,
    "source": (
        "data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv (43 plant rows, "
        "all flag=='ok') + campd_ct_heat_rates_CAISO_units.csv (87 unit rows), "
        "written by scripts/data/derive_campd_ct_heat_rates.py --iso CAISO --years "
        "2023 2024 2025. Consumed by fleet.campd_bins.measured_ct_heat_rates('CAISO') "
        "-> eia860._rows_to_generators, class-scoped to CT_PEAKER rows only."
    ),
    "note": (
        "NOT a fitted parameter and not a tunable: it is a boolean that selects "
        "MEASURED per-plant loaded heat rates over eGRID's plant-average ANNUAL rate "
        "(rule 14 [R-ACCURATE]). It carries no threshold or scalar of its own — every "
        "number it applies is a CAMPD measurement of a specific machine, on the same "
        "gross-to-net basis as the benchmark it is scored against. Per rule 24 "
        "[R-FROZEN-DERIVE] the artifact re-derives ONLY when CAMPD publishes new or "
        "revised vintages, never because a residual moved, and any re-derivation "
        "commit must cite the data change. Per rule 25 [R-ISO-SCOPE] this is CAISO's "
        "own artifact from CAISO's own data; the PJM/NYISO/MISO K verdicts transfer "
        "nothing to it."
    ),
    "known_limitation": (
        "One applied row is a broken meter channel, sized and NOT repaired here: "
        "Delano Energy Center (58122, 60.5 MW = 1.03 % of covered capacity, 0.22 % of "
        "covered energy) reads 6.5725 MMBtu/MWh, below any real simple-cycle machine "
        "yet above the derive's 6.0 plant-level floor, because a minority of its "
        "loaded hours under-report heatInput (hourly rate p05 0.81 / p25 3.20 against "
        "a median 7.89). This is a property of the SHARED derive in every ISO, not a "
        "CAISO defect — sub-floor loaded hours run 3.46 % (CAISO), 2.45 % (NYISO), "
        "1.55 % (PJM), 0.30 % (MISO), worth +0.114/+0.122/+0.081/+0.014 MMBtu/MWh "
        "energy-weighted (scripts/probes/_caiso146_hourly_hr_integrity.py). An "
        "hour-grain screen would move THREE committed keepers' inputs, which is not a "
        "CAISO session's call, so it is filed as a cross-cutting audit item. The "
        "prereg's K6 gate proves the verdict does not hinge on it: excluding Delano, "
        "the CT_PEAKER move keeps its sign at 80/84/66 % of its size "
        "(+0.513/+0.176/+0.121 vs +0.638/+0.211/+0.183 TWh)."
    ),
}


def main() -> int:
    """Write the caiso-146 attestation from the caiso-139 keeper's."""
    att = json.loads(SOURCE.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY

    for exc in att["exceptions"]:
        key = (exc.get("criterion"), int(exc.get("year", 0)))
        if key in REMEASURED:
            exc["magnitude"] = REMEASURED[key] + "PRIOR MAGNITUDE: " + exc["magnitude"]
        exc["reason"] = CARRY + exc["reason"]
        exc["carried_from"] = (
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
