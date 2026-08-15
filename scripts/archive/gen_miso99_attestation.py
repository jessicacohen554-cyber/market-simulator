"""Write ``calibration_attestation.json`` for the miso-99 measured-CHP-heat-rate arm.

``miso99_chp_hr_B`` is the ``2026-07-27-miso-98b-sectormeasured`` keeper recipe
(rebuilt from its ``meta.json``) with ONE delta:
``ScenarioConfig.measured_chp_heat_rates=True``. Governance posture and the
accepted-limitation ledger are therefore that keeper's, inherited unchanged —
no exception is added, widened, or re-scoped to absorb anything from this delta.

The delta REPLACES eGRID's steam-credited ``PLHTRT`` with the plant's own
power-only rate built from eGRID's OWN published CHP heat-input allocation, so
it adds no fitted scalar and supersedes a hand factor where it applies (rule 24
`[R-DOF]` / rule 21 `[R-REGISTRY]`). The ``free_parameters`` ledger is refreshed
from THIS bundle's ``run_config.json`` by ``scripts/build_dof_ledger.py``
(run separately).

Usage:
    python scripts/gen_miso99_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso99_chp_hr_B
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/miso98_chp_sector_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso99_chp_hr_B/calibration_attestation.json"

ATTESTED_BY = (
    "miso-99 measured power-only CHP heat rates 2026-07-28: the "
    "2026-07-27-miso-98b-sectormeasured keeper recipe, rebuilt from its "
    "meta.json (run_config.json's calibration_flags is a curated ~35-key "
    "subset and would have mis-specified the run), solved fresh for "
    "2023/2024/2025 as one process per year into one bundle, with a SINGLE "
    "delta: ScenarioConfig.measured_chp_heat_rates=True, carried on the "
    "generic prb_overrides channel so it round-trips through meta.json. "
    "WHAT IT REPLACES: the model's offer heat rate is eGRID PLNT23 PLHTRT, "
    "and at a cogeneration plant eGRID does not publish that as total fuel "
    "per net MWh -- it first removes the share of the plant's fuel it "
    "attributes to useful thermal output, so PLHTRT is a STEAM-CREDITED rate, "
    "not the rate at which the machine turns fuel into power. Fed to the LP as "
    "a marginal cost it makes CHP the cheapest thermal on the system; six ISOs "
    "measure 12-62 % understated on a consistent net basis (caiso-128 §4). "
    "WHAT IT USES INSTEAD: eGRID publishes the credit it removed. The plant "
    "sheet carries PLHTIAN (heat input allocated to electricity, the numerator "
    "of the rate the model loads) AND CHPCHTI (heat input allocated to useful "
    "thermal output), so the power-only rate is (PLHTIAN + CHPCHTI) / PLNGENAN "
    "-- the incumbent input with eGRID's own allocation undone, on the SAME "
    "net-generation denominator, same source, same vintage. NO GROSS-TO-NET "
    "FACTOR IS INVOLVED, and that is the point: caiso-128 §6(a) required the "
    "plant's own measured gross->net ratio and FINDING-miso98 §6.1 measured it "
    "firing on 0 of 19 MISO rows, because at a cogen CAMPD's grossLoad channel "
    "and EIA-923's net generation cover DIFFERENT UNIT SETS (Midland CEMS "
    "gross 7.89 TWh vs EIA-923 net 9.76 TWh; Portside 0.070 vs 0.232; Primient "
    "0.674 vs 0.389). PLNGENAN is already the model's net basis and is "
    "identical to the EIA-923 combustion net the benchmark holds out against. "
    "VALIDATED, not asserted: PLHTIAN + CHPCHTI reproduces the plant's "
    "INDEPENDENTLY METERED CAMPD annual heat input at a median ratio of "
    "1.00000 on 22 of the 25 CEMS-covered MISO CHP plants (PLHTIAN alone: "
    "1.473, 2/25); Midland matches to 3 MMBtu in 86 million. The three misses "
    "are plants with combustion units below the Part-75 threshold, where CEMS "
    "undercounts and eGRID is complete -- the check fails toward CEMS, never "
    "toward eGRID. NO HOST DOUBLE-COUNT: chp_btm_pct holds the host share out "
    "as a VOLUME (capacity, floor, benchmark subtrahend) while this is an "
    "INTENSITY applied per dispatched MWh. SCOPE is topping cycles on turbine "
    "physics (CC_CHP/CT_CHP): adding the credit back charges all the fuel to "
    "power, which is right where the fuel goes through the prime mover first "
    "and the steam is recovered from its exhaust, and wrong for a boiler-first "
    "back-pressure cogen whose turbine sits in the let-down path -- MISO "
    "ST_CHP add-backs reach 435 MMBtu/MWh, so ST_CHP is OUT of scope and keeps "
    "the existing chain. Gates are definitional and frozen at derive time "
    "(rule 23 [R-FROZEN-DERIVE]): prime mover; an unfired-topping thermal "
    "share <= 0.50, which is the arithmetic ceiling of the EPA CHP Partnership "
    "gas-turbine envelope over eGRID's T/0.8 displaced-boiler credit, not a "
    "swept threshold; the repo's EXISTING committed physical heat-rate bands "
    "on the corrected value; and a basis check excluding plants whose "
    "incumbent is a boundary repair or HEAT_RATE_BINS fallback rather than a "
    "plain PLHTRT. ZERO fitted parameters, no per-ISO literal, no tuning "
    "channel (rule 21 [R-REGISTRY]); the gate is ISO-generic and default off, "
    "and where the measurement covers a plant the legacy 1.8x hand topping "
    "factor is SKIPPED rather than stacked (rule 19 [R-ONE-MECH]). "
    "CHP_STEAM_CREDIT_HR_CORRECTION_ISOS is unchanged and MISO is NOT added. "
    "MISO effect: 25 (plant, class) rows applied, CC_CHP 81.8 % of class MW "
    "(6.70 -> 9.16 MMBtu/MWh) and CT_CHP 37.2 % (6.39 -> 9.43); 72 generators "
    "/ 6,732 MW repriced. Rule 13 [R-MEASURED] admissible: a machine's "
    "power-only heat rate is a physical property that regenerates from each "
    "eGRID vintage and responds to changed conditions, not a measured outcome "
    "fed back to close a residual. Promotion evidence: the pre-registered A/B "
    "against a same-HEAD control arm with the flag off "
    "(2026-07-28-miso-99a-chp-hr), "
    "results/calibration/FINDING-miso99-chp-heat-rate-2026-07-28.md."
)

DISCLOSURE = (
    "See metrics.json determination + reasons (NOT-YET, decided by C3a-2025, "
    "C3c and C7 COAL_PRB diurnal shape -- the miso-96 issue, entirely "
    "unrelated to this delta and UNCHANGED by it). PROMOTED ON STRUCTURAL "
    "FIDELITY (rule 1 [R-STRUCT]) AND the gates agree: against the same-HEAD "
    "flag-off control, EVERY criterion verdict is identical (C1/C2/C3b/C4/C8 "
    "PASS, C3a/C3c/C7 FAIL) and C3a mean LMP improves in ALL THREE years "
    "(-6.4/-10.2/-15.4 % -> -5.4/-9.1/-14.3 %). NO CRITERION REGRESSES. The "
    "pre-registered kill guard held: C3b price shape stays PASS (miso-98b "
    "passes it at 0.198 against a <=0.20 bound and could have flipped back; it "
    "did not). C3c is BIT-IDENTICAL in every year (1/6/0 model hours vs "
    "30/37/88 actual) -- the tail is untouched by a CHP cost change, which is "
    "the honest reading, not evidence of improvement. LEDGER UNCHANGED at 2/3: "
    "no exception is added, widened or re-scoped to absorb this delta. "
    "THE CONTROL IS AN EQUALITY CHECK, not merely structural agreement: arm A "
    "reproduces the miso-98b keeper at 0.0000 % on all 17 classes in all three "
    "years, so every arm-B movement is fully attributable to the single flag; "
    "and all NINE shared_inputs hashes plus the benchmark itself (identical on "
    "all 21 class-year rows) are the same across the arms, so the miso-98 §5 "
    "shared-bench trap is defused by measurement rather than assumption. "
    "PRE-REGISTERED AND HONOURED (FINDING-miso99 §3, committed before any arm "
    "was readable, and restating the charter's own coverage figure -- CT_CHP "
    "is 37.2 % MW-covered, not the 10.4 % the CEMS route implied, so the "
    "predicted CT_CHP degradation is correspondingly larger): CC_CHP improves "
    "materially, |err| falling in all three years (+11.8 -> -9.8 %, +11.1 -> "
    "-10.1 %, +31.7 -> -4.9 %); CT_CHP DEGRADES in 2023/2024 exactly as "
    "predicted (-33.3 -> -38.4 %, -32.9 -> -37.8 %) and improves in 2025 "
    "(+15.7 -> +6.2 %). Under rules 1 [R-STRUCT] / 14 [R-ACCURATE] the "
    "CT_CHP degradation is NOT grounds to revert: the credited rate is "
    "measurably the wrong quantity, validated to 1e-7 against metered fuel, "
    "while non-CHP classes measure 0-3 % accurate on the same pipeline. "
    "TWO ADVERSE MOVEMENTS REPORTED, NOT SMOOTHED: (a) CC_CHP's diurnal "
    "AMPLITUDE overshoots -- D-1 cv 0.026 -> 0.141 against an actual 0.066, so "
    "cv_ratio 0.392 -> 2.132 (2023) -- even though its profile CORRELATION "
    "improves (r 0.959 -> 0.989 / 0.980 -> 0.986 / 0.860 -> 0.965); (b) "
    "CT_CHP's profile correlation degrades (0.768 -> 0.652, 0.084 -> -0.104, "
    "0.627 -> 0.171). Neither class is D-1-gated (the gate covers "
    "CT_PEAKER/ST_GAS/COAL*), so no gate moves, but both are real and are the "
    "named open items. COAL_PRB's D-1 FAIL and MISO ST_CHP's -0.79 profile "
    "anti-correlation are UNCHANGED by this delta, confirming both are "
    "independent of CHP heat rates. Rule 22 [R-HOLDOUT] honoured: 2023-2025 "
    "only, all three years solved FRESH in one bundle (rule 16 [R-ALLYEARS]), "
    "no holdout year touched, MISO freeze active. LOYO: the input carries NO "
    "parameter fitted to any year -- it is a single published eGRID vintage "
    "read the same way for every year -- and the class response is stable "
    "across years (CC_CHP -19.3/-19.1 %, CT_CHP -7.6/-7.3 % in 2023/2024)."
)


def main() -> int:
    """Write the arm's attestation, inheriting the keeper's ledger unchanged."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)
    att["disclosures"] = dict(att.get("disclosures", {}), note=DISCLOSURE)
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM.relative_to(REPO)}")
    print(f"  exceptions inherited unchanged: {len(att.get('exceptions', []))}")
    print(
        "now run: python scripts/build_dof_ledger.py "
        "results/calibration/miso99_chp_hr_B"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
