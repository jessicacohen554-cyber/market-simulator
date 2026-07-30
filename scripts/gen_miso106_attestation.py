"""Write ``calibration_attestation.json`` for the miso-106 measured-CT-heat-rate arm.

``miso106_ctheatrate_B`` is the ``2026-07-28-miso-101b-tempgrain`` keeper recipe
(rebuilt from its ``meta.json``) with ONE delta:
``ScenarioConfig.measured_ct_heat_rates=True``. Governance posture and the
accepted-limitation ledger are therefore that keeper's, inherited **unchanged**
— no exception is added, widened, or re-scoped to absorb anything from this
delta, and the non-protective ledgered-caveat budget stays saturated at 3/3
(C3a, C3b, C3c) exactly where miso-90 left it.

The delta REPLACES eGRID's plant-average ANNUAL heat rate on CT_PEAKER rows with
the machines' own CAMPD-measured LOADED rate, so it adds no fitted scalar (rule
21 ``[R-DOF]`` / rule 24 ``[R-REGISTRY]``). The ``free_parameters`` ledger is
refreshed from THIS bundle's ``run_config.json`` by
``scripts/build_dof_ledger.py`` (run separately).

Two measured input defects it repairs, both MISO's own (rule 14 ``[R-ACCURATE]``,
rule 25 ``[R-ISO-SCOPE]`` — nothing is transferred from the NYISO or PJM
promotions of the same flag):

1. An annual average is not a loaded rate. South Fond Du Lac (7203, 326.5 MW)
   carried eGRID **26.544 MMBtu/MWh**, above the physical simple-cycle ceiling
   of 25.0, because its four turbines ran at CF ~0.5 % and the annual mean is
   dominated by start and part-load fuel. Measured loaded rate **14.014**.
2. At a mixed facility eGRID publishes one rate per PLANT, so a peaker inherits
   its site's combined-cycle number. 19 MISO CT_PEAKER plants / 1,651 MW carry
   an eGRID rate below 9.0; the artifact covers 7 of them (1,068 MW).

Usage:
    python scripts/gen_miso106_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso106_ctheatrate_B
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/miso101_tempgrain_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso106_ctheatrate_B/calibration_attestation.json"

ATTESTED_BY = (
    "miso-106 measured CT loaded heat rates 2026-07-30: the "
    "2026-07-28-miso-101b-tempgrain keeper recipe, rebuilt from its meta.json "
    "(run_config.json's calibration_flags is a curated subset and would have "
    "mis-specified the run), solved fresh for 2023/2024/2025 as ONE PROCESS "
    "PER YEAR chained with --reuse-solved into one bundle (rule 12/16; a "
    "single-process three-year solve was OOM-killed at 15.9 GB anon-rss on a "
    "15 GB box), with a SINGLE delta: ScenarioConfig.measured_ct_heat_rates="
    "True, carried on the generic prb_overrides channel so it round-trips "
    "through meta.json. "
    "WHAT IT REPLACES: the non-ERCOT fleet loader gives every combustion "
    "turbine eGRID's plant-average ANNUAL heat rate. Two things are wrong with "
    "that number for a peaker, and MISO's own data shows both. (1) An annual "
    "average is not a loaded rate: it blends startup, part-load and shutdown "
    "fuel into the figure that sets the offer. South Fond Du Lac (7203, "
    "326.5 MW, 4 turbines) carried 26.544 MMBtu/MWh -- ABOVE the physical "
    "simple-cycle ceiling of 25.0 and roughly 2x any operating turbine -- "
    "because its units ran at CF ~0.5 % (2.2-3.7 GWh each in 2024); their "
    "loaded rate is 13.79-13.93 gross, 14.014 net. It is one of 5 MISO "
    "CT_PEAKER plants (445 MW) the model priced outside [6, 25]. (2) At a "
    "mixed facility it is not even the right technology's rate: eGRID keys one "
    "heat rate per PLANT, so 19 MISO CT_PEAKER plants / 1,651 MW (7.4 % of "
    "class MW) carried an eGRID rate below 9.0 -- a COMBINED-CYCLE number on a "
    "peaker. CAMPD's own unitType tag separates them decisively: at Perryville "
    "(55620) units 1-1/1-2 are tagged 'Combined cycle' and unit 2-1 "
    "'Combustion turbine', and the model priced that 152.7 MW peaker at 6.890 "
    "against a measured 10.774; at Zeeland (55087) CC1/CC2 are tagged "
    "'Combustion turbine' (matching the model's 318.2 MW of CT_PEAKER) against "
    "CC3/CC4 'Combined cycle', and the model priced them at 8.587 against a "
    "measured 10.922. "
    "WHAT IT USES INSTEAD: per CAMPD unit with unitType == 'Combustion "
    "turbine', sum(heatInput)/sum(grossLoad) over hours at >= 0.80 x p95 of "
    "that unit's OWN gross load with >= 50 such hours, converted to a NET "
    "basis by the committed parasitic_load_factors.parquet -- the same map the "
    "benchmark's net actual uses, so the derived rate and the generation it is "
    "scored against share one gross-to-net convention -- pooled 2023-2025 and "
    "aggregated to the plant generation-weighted. "
    "DERIVED FROM MISO'S OWN FLEET, NOTHING TRANSFERRED (rule 25): the same "
    "flag is a keeper in NYISO (nyiso-89) and PJM (pjm-137), and NEITHER "
    "ISO's rates, coverage, or direction crossed the boundary; MISO's artifact "
    "is built from MISO's CAMPD over MISO's 14 states against MISO's own model "
    "fleet. pjm-95's refutation of the committed literature slopes on PJM's "
    "own CAMPD is the precedent for deriving locally rather than transferring, "
    "and pjm-137's own pre-registration was refuted IN DIRECTION by PJM's "
    "artifact -- so MISO's prediction was built only from MISO's numbers. "
    "COVERAGE: 86 of 168 CT_PEAKER plants, 19,121 of 22,289 MW (85.8 % of "
    "class capacity), covering ~92-96 % of the class's real energy. ZERO "
    "plants excluded by the physical band [6.0, 25.0]. Two-signed -- 56 "
    "cheaper / 30 dearer, 51 moved > 0.5 MMBtu/MWh -- so it is not a "
    "multiplier in disguise. ISO capacity-weighted 12.290 -> 11.868 (-3.4 %); "
    "generation-weighted 11.436 -> 11.427 (-0.1 %). "
    "ZERO FITTED PARAMETERS. Every threshold in the derivation is a frozen "
    "physical/data-integrity constant unchanged since nyiso-89 (loaded-window "
    "0.80 x p95, >= 50 qualifying hours, physical band [6, 25]); none was "
    "chosen against a MISO residual, and rule 23 [R-FROZEN-DERIVE] binds "
    "re-derivation to a CAMPD vintage change. "
    "RULE 19 [R-ONE-MECH]: the only mechanism touching CT_PEAKER is the h14-21 "
    "reliability_floor, which is a QUANTITY floor; this is a COST input on the "
    "same class. Nothing is stacked, no floor is added or widened, and no "
    "window is declared, so rule 17 [R-FLOOR-WINDOW] has nothing to bind on. "
    "RULE 22: 2023-2025 only, all three in one bundle, no holdout year solved, "
    "scored or registered; MISO carries no calibration-complete marker and the "
    "freeze is respected."
)

NOTE = (
    "PROMOTED ON RULE 1 [R-STRUCT] STRUCTURAL FIDELITY, WITH THE COSTS ON THE "
    "RECORD. Against a same-HEAD flag-off control (2026-07-30-miso-106a-ct-hr) "
    "EVERY criterion verdict is IDENTICAL -- 8 scored / 5 target-grade / 3 "
    "fails in both arms, C7 FAIL on COAL_PRB and C8 PASS in both -- so no gate "
    "moves in either direction, and the case for the arm is that the model now "
    "prices 19,121 MW of peaking capacity at the rate its machines actually "
    "burn fuel at instead of a plant-average that was physically impossible on "
    "445 MW of it and a combined-cycle number on another 1,068 MW. "
    "WHAT IMPROVES: C3a mean LMP in ALL THREE YEARS (-1.4 -> -1.2 %, "
    "-6.7 -> -6.6 %, -14.3 -> -14.2 %); D-1 CT_PEAKER off-peak cv_ratio moves "
    "toward 1.0 in 2024 (0.848 -> 0.931) and 2025 (0.805 -> 1.046) with "
    "profile_r flat-to-better (0.971 -> 0.973 / 0.971 / 0.985). C3c is "
    "BIT-IDENTICAL (1/6/0 model hours in both arms) and is stated as unchanged "
    "rather than claimed as a gain. "
    "REPORTED HONESTLY, NOT PATCHED -- FOUR THINGS MOVE THE WRONG WAY AND THE "
    "ARM IS PROMOTED ANYWAY (rules 1/14): (a) C1 CT_PEAKER |err| DEGRADES in "
    "all three years -- 2023 -20.18 -> -26.35 %, 2024 +1.31 -> -3.63 %, 2025 "
    "+2.73 -> -3.69 % -- and the pre-registration was WRONG IN DIRECTION for "
    "2024/2025: it predicted both would improve toward zero, and instead the "
    "volume fall (~1 TWh/yr, correctly predicted in sign) OVERSHOT past zero. "
    "All three stay far inside the +-8 TWh band so C1 holds PASS. (b) D-2 "
    "CT_PEAKER forced share RISES 11.77 -> 14.21 % (2023), 8.39 -> 10.14 %, "
    "8.78 -> 10.51 %, leaving only 0.79 pp of headroom under the 15 % peaker "
    "cap in 2023; the forced ENERGY itself rises 1.188 -> 1.743 TWh (+47 %), "
    "because correctly-priced peakers want to run less and the h14-21 "
    "reliability floor therefore binds harder. That is a REAL structural "
    "signal about the floor, recorded as an open item -- NOT to be closed by "
    "relaxing the floor or reverting the input. (c) C3b price shape worsens in "
    "2025, 0.190 -> 0.192 against the 0.20 veto; the direction was "
    "pre-registered as the mechanism's expected cost (it removes the top of "
    "the CT curve and MISO's standing diagnosed defect is diurnal spread "
    "compression, miso-89) and the gate HOLDS with 0.008 of headroom. (d) "
    "Zeeland's CTs really do run hard in reality (4.45 TWh of CAMPD gross over "
    "2023-2025, CF 0.532) and making them ~$6-8/MWh dearer cuts their model "
    "run hours -- rule 14's named scenario, kept as the accurate input with "
    "the root cause left open rather than buried back in a wrong heat rate. "
    "COAL_PRB's D-1 FAIL is UNCHANGED (cv_ratio 0.467/0.476/0.318 -> "
    "0.462/0.475/0.313), confirming MISO's determination blocker is "
    "independent of CT heat rates. D-4 off-window binding stays EXACTLY 0.000 "
    "on every limb in both arms. "
    "THE CONTROL IS A BOUNDED NOISE FLOOR, NOT A BIT-EQUALITY. The "
    "pre-registered G3 (arm A reproduces the committed keeper at max |delta| < "
    "1e-6 MW) FAILED and is recorded as a fail: the threshold was "
    "mis-specified, written without first checking that main had moved 21 "
    "files / 1,312 insertions under src/market_sim/ since the keeper's code "
    "basis (model/lp/costs.py, model/lp/model.py, pipeline/year.py, runner.py, "
    "data/loss_surface.py among them), so bit-identity to a bundle built on "
    "older code was never obtainable. What the control DOES establish, "
    "measured: total generation reproduces the keeper at +0.000000 % in all "
    "three years, load-weighted mean LMP to within $0.0001, and the worst "
    "per-class ANNUAL divergence across 17 classes x 3 years is 0.00630 %. The "
    "912.5 MW class-hour maxima are alternate-optima reallocation (2025 nets "
    "to +-0.01 MWh on EVERY class over the whole year; hydro nets to exactly "
    "0.00 across 1,536-1,770 hours; the largest delta sits on `import`, served "
    "by 32 equally-priced tranches). The A/B attribution therefore carries a "
    "0.00630 % per-class-year noise floor rather than zero -- and every "
    "movement claimed above is orders of magnitude larger (class-hour max "
    "|delta| between arms 766 / 920 / 1,354 MW). "
    "LEDGER UNCHANGED at 3/3 (C3a, C3b, C3c): no exception added, widened or "
    "re-scoped. DETERMINATION and criterion profile are the SAME as the "
    "outgoing keeper's, decided by the same C7 COAL_PRB diurnal shape issue "
    "(miso-96) that this delta does not touch."
)


#: Rule 21 [R-DOF]. ``build_dof_ledger.py`` seeds the ledger from the tunables
#: it can enumerate and leaves this one out — the flag carries no free scalar,
#: so the automated pass sees nothing to record. It is listed EXPLICITLY anyway,
#: on pjm-137's precedent: "each free parameter with its identification source"
#: is better served by naming the input and where its value comes from than by
#: silence. The entry adds ZERO residual-identified parameters; the ledger stays
#: 25 entries / 2 residual, the same two as the outgoing keeper.
NEW_ENTRY = {
    "name": "Measured loaded CT heat rates (CAMPD, per plant)",
    "where": "run_config.scenario_config.measured_ct_heat_rates",
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — every plant's rate is derived "
        "from its own CAMPD meter by a frozen derive (rule 23 "
        "[R-FROZEN-DERIVE]) whose only re-derivation trigger is a CAMPD "
        "vintage change. Nothing was swept: the artifact was derived ONCE, "
        "before either arm was solved, and committed with the pre-registration "
        "(PREREG-miso106, commit 166339f) so the gates were fixed before any "
        "result was readable. No multiplier, blend, scale, floor, cap, "
        "per-plant override or band widening may ever be applied to the "
        "derived rates."
    ),
    "value": (
        "fleet.campd_bins.measured_ct_heat_rates('MISO') -> "
        "fleet.eia860._rows_to_generators: each CT_PEAKER plant's heat_rate "
        "becomes its measured LOADED rate in place of the eGRID plant-average "
        "ANNUAL rate. 86 plants / 19,121 MW (85.8 % of class capacity, ~92-96 "
        "% of the class's real energy), ALL inside the physical simple-cycle "
        "band [6.0, 25.0] MMBtu/MWh net (zero excluded); 51 move by more than "
        "0.5 MMBtu/MWh, 56 cheaper and 30 dearer. ISO capacity-weighted "
        "12.290 -> 11.868 (-3.4 %); generation-weighted 11.436 -> 11.427 "
        "(-0.1 %). Verified live at the fleet seam with no LP: flipping the "
        "flag moves 254 generators / 19,120.7 MW, every one CT_PEAKER, zero "
        "leakage into any other class."
    ),
    "source": (
        "EPA CAMPD unit-level hourly grossLoad + heatInput over MISO's own 14 "
        "states (data/raw/campd-unit-level), restricted by CAMPD's own "
        "unitType == 'Combustion turbine' to plants carrying a CT_PEAKER "
        "generator in MISO's model fleet; loaded window >= 0.80 x p95 of each "
        "unit's own gross load with >= 50 qualifying hours; net basis via the "
        "committed parasitic_load_factors.parquet; pooled 2023-2025, plant "
        "value generation-weighted. Derive: "
        "scripts/data/derive_campd_ct_heat_rates.py --iso MISO. Artifact: "
        "data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv (+ _units). "
        "MISO-derived only — no NYISO (nyiso-89) or PJM (pjm-137) value "
        "crosses the boundary (rule 25 [R-ISO-SCOPE])."
    ),
}


def main() -> int:
    """Carry the keeper's attestation onto the miso-106 arm, unchanged but for provenance."""
    att = json.loads(KEEPER.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM}")
    print(
        f"  exceptions carried forward unchanged: {len(att['exceptions'])} "
        f"(ledgered caveat budget stays 3/3 — C3a, C3b, C3c)"
    )
    return 0


def add_ledger_entry() -> int:
    """Append :data:`NEW_ENTRY` to the arm's ``free_parameters`` ledger.

    Run AFTER ``scripts/build_dof_ledger.py``, which overwrites the block.
    Idempotent: a second run replaces the entry rather than duplicating it.
    """
    att = json.loads(ARM.read_text())
    fp = att["free_parameters"]
    fp["entries"] = [e for e in fp["entries"] if e.get("name") != NEW_ENTRY["name"]]
    fp["entries"].append(NEW_ENTRY)
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"  ledger: {fp['n_entries']} entries, {fp['n_residual']} residual "
        "(the measured input adds ZERO residual-identified parameters)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main() or add_ledger_entry())
