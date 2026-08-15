"""Write ``calibration_attestation.json`` for both pjm-137 A/B arms.

Both arms replay the ``2026-07-28-pjm-136-lossurf`` recipe
(``pjm136_lossurf_B``), so the governance posture and the accepted-limitation
ledger are the keeper's, inherited unchanged:

* **arm A** (``pjm137_control_A``) is the keeper recipe VERBATIM — no delta, and
  verified byte-identical to the committed keeper on the class hourlies. Its
  attestation is therefore the keeper's, re-attested as the A/B control.
* **arm B** (``pjm137_ctheatrate_B``) adds ONE delta,
  ``measured_ct_heat_rates=true``, and therefore ONE ledger entry.

The delta adds **zero residual-identified degrees of freedom** (rule 23
``[R-DOF]``). Each plant's applied heat rate is a pure function of its own CAMPD
meter over a fixed loaded window: the frozen derive
(``scripts/data/derive_campd_ct_heat_rates.py``) takes the hours in which a unit
is at or above 0.8 x its own p95 gross load, forms ``sum(heatInput) /
sum(grossLoad)`` there, converts to a net basis with the committed parasitic
factor, and generation-weights the plant's turbines. No scale, no haircut, no
blend, no fitted anchor, and no per-plant override. So the ledger gains a
``measured-physical`` entry and ``n_residual`` is unchanged.

Usage:
    python scripts/gen_pjm137_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/pjm136_lossurf_B/calibration_attestation.json"
ARM_A = REPO / "results/calibration/pjm137_control_A/calibration_attestation.json"
ARM_B = REPO / "results/calibration/pjm137_ctheatrate_B/calibration_attestation.json"
RESULT = REPO / "results/probes/pjm137_ctheatrate_ab.json"

NEW_ENTRY = {
    "name": "Measured loaded CT heat rates (CAMPD, per plant)",
    "where": "run_config.scenario_config.measured_ct_heat_rates",
    "identification": "measured-physical",
    "lineage_solves": (
        "0 solves added to the tuning lineage — every plant's rate is derived "
        "from its own CAMPD meter by a frozen derive (rule 23 "
        "[R-FROZEN-DERIVE]) whose only re-derivation trigger is a CAMPD "
        "vintage change. Nothing was swept, and PREREG §4's no-feedback "
        "ceiling forbids ever applying a multiplier, blend, scale, floor, cap, "
        "per-plant override or band widening to the derived rates."
    ),
    "value": (
        "fleet.campd_bins.measured_ct_heat_rates('PJM') -> "
        "fleet.eia860._rows_to_generators: each CT_PEAKER plant's heat_rate "
        "becomes its measured LOADED rate in place of the eGRID plant-average "
        "ANNUAL rate. 71 plants, ALL inside the physical simple-cycle band "
        "[6.0, 25.0] MMBtu/MWh net (zero excluded); 29 move by more than 0.5 "
        "MMBtu/MWh, 35 cheaper and 36 dearer. ISO energy-weighted "
        "+0.229 MMBtu/MWh (~ +$0.80/MWh at $3.50/MMBtu); PJM_Dominion "
        "+0.634 (~ +$2.22/MWh)."
    ),
    "source": (
        "EPA CAMPD unit-level hourly grossLoad + heatInput "
        "(data/raw/campd-unit-level), unitType == 'Combustion turbine', pooled "
        "2023-2025; per unit the rate is sum(heatInput)/sum(grossLoad) over "
        "hours >= 0.8 x that unit's own p95 gross load (>= 50 qualifying "
        "hours), converted to a NET basis by the committed parasitic factor "
        "(parasitic_load_factors.parquet — the SAME map the benchmark's net "
        "actual uses, so the derived rate and the actual it is scored against "
        "share one gross-to-net convention); the plant value is the "
        "generation-weighted mean across its turbines. Artifact: "
        "data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv (+ the "
        "per-unit detail table, 281 unit rows)."
    ),
    "forward_story": (
        "A unit's loaded heat rate is a physical characteristic of the machine "
        "and regenerates for a forward year from the same pipeline: a retrofit "
        "moves it, a new unit carries its design rate, and a retired unit "
        "leaves the population. It is in the same admissibility class as the "
        "CAMPD min-stable loads and CT run horizons already ledgered."
    ),
    "rule_13_admissibility": (
        "A measured loaded heat rate is a physical INPUT, not an outcome "
        "pinned to a residual: it sets the unit's marginal cost in the "
        "objective and the LP dispatches from there. No volume is pinned to an "
        "actual and nothing is added to a price. It replaces an ESTIMATE that "
        "is demonstrably wrong at a mixed facility — eGRID publishes one heat "
        "rate per PLANT, so Doswell Energy Center's three simple-cycle peakers "
        "carried the 9.027 MMBtu/MWh plant average of a site that is mostly "
        "combined cycle, against a measured 11.350. Rule 14 [R-ACCURATE] "
        "governs the disposition: the measured rate is kept even where the "
        "backcast worsens, and the worsening is treated as a discovered "
        "miscalibration elsewhere rather than a reason to revert."
    ),
}


def _evidence() -> str:
    """The shared A/B evidence block, read from the committed scorer output."""
    if not RESULT.exists():
        raise SystemExit(
            f"missing {RESULT} — run scripts/probes/_pjm137_ctheatrate_ab.py first"
        )
    res = json.loads(RESULT.read_text())
    art = res["P2_K3_artifact"]
    parts = [
        "EVIDENCE (arms pjm137_control_A / pjm137_ctheatrate_B, all three years "
        "in one invocation, arms sequential). P2 the artifact re-prices "
        f"{art['plants_moved_gt_0p5']} of {art['plants_applied']} plants by more "
        f"than 0.5 MMBtu/MWh and is TWO-SIGNED ({art['plants_cheaper']} cheaper / "
        f"{art['plants_dearer']} dearer), energy-weighted "
        f"{art['energy_weighted_delta_mmbtu_per_mwh']:+.3f} MMBtu/MWh "
        f"({art['energy_weighted_delta_usd_per_mwh']:+.2f} $/MWh at $3.50/MMBtu) "
        "— a measurement, not a multiplier. K3 "
        f"{art['plants_excluded_by_band']} plants excluded by the physical band "
        f"({art['excluded_energy_share'] * 100:.2f} % of energy)."
    ]
    for year in ("2023", "2024", "2025"):
        row = res["per_year"][year]
        ident = row["K5_arm_a_identity"]
        sd = row["K4_slack_dump"]
        ct = row["iso_class_twh"].get("CT_PEAKER", {})
        dom = row["dominion_class_twh"].get("CT_PEAKER", {})
        ident_txt = (
            "byte-identical"
            if ident.get("identical")
            else f"max |Δ| {ident.get('max_abs_diff_mw')} MW"
        )
        dom_txt = (
            f", PJM_Dominion CT_PEAKER {dom.get('A')} -> {dom.get('B')} TWh"
            if dom
            else ""
        )
        parts.append(
            f"{year}: K5 arm A {ident_txt} vs the committed keeper; K4 slack/dump "
            f"{sd['A']['slack_mwh']:.0f}/{sd['A']['dump_mwh']:.0f} (A) and "
            f"{sd['B']['slack_mwh']:.0f}/{sd['B']['dump_mwh']:.0f} (B); ISO-wide "
            f"CT_PEAKER {ct.get('A')} -> {ct.get('B')} TWh "
            f"({ct.get('delta'):+}){dom_txt}."
        )
    for arm in ("A", "B"):
        r = res["rubric"][arm]
        if r.get("available"):
            parts.append(
                f"Arm {arm} determination {r['determination']}; criteria "
                + ", ".join(f"{k}={v}" for k, v in sorted(r["criteria"].items()))
                + "."
            )
    return " ".join(parts)


ATTESTED_BY_A = (
    "pjm-137 arm A (CONTROL) 2026-07-29: the 2026-07-28-pjm-136-lossurf keeper "
    "recipe replayed VERBATIM with no delta, as the A/B baseline for "
    "measured_ct_heat_rates. Verified against the committed keeper on the class "
    "hourlies (PREREG-pjm137-measured-ct-heat-rates-2026-07-29.md K5), so the "
    "keeper's governance posture and accepted-limitation ledger carry over "
    "unchanged and this arm adds no parameter of any kind. Its purpose is to "
    "isolate the single delta; it is NOT a candidate."
)


def _attested_by_b() -> str:
    """Arm B's attestation narrative, with the A/B evidence spliced in."""
    return (
        "pjm-137 measured loaded CT heat rates 2026-07-29: the "
        "2026-07-28-pjm-136-lossurf recipe replayed with a SINGLE delta, "
        "measured_ct_heat_rates=true, on a newly generated PJM artifact from "
        "the existing frozen derive. Chartered by "
        "FINDING-pjm137-dominion-congestion-is-subzonal-2026-07-29.md and gated "
        "by PREREG-pjm137-measured-ct-heat-rates-2026-07-29.md, committed and "
        "pushed BEFORE any arm solved. "
        "DRIVER: the zonal-congestion route to the Dominion CT leg is CLOSED BY "
        "MEASUREMENT. PJM's own day-ahead binding-constraint record "
        "(da_marginal_value, 228,795 constraint-hours over 2023-2025) puts only "
        "6.34/3.06/6.19 % of its congestion rent on a named zonal-scale "
        "interface and 80.0-87.8 % on monitored facilities rated 230 kV and "
        "below; AEP-DOM — the very boundary the pjm-133..136 lineage tried to "
        "make price — carries 0.041/0.071/0.236 %. In the top-decile "
        "DOM-separation hours the dominant constraints are PLEASNTV TX3 500 kV, "
        "GOOSECRE TX1 500 kV, PLEASNTV-ASHBURN 230 kV, ASHBURN-GOOSECRE 230 kV "
        "and BRAMBLET-EVRGREEN, every one of which returns zone = DOM from PJM's "
        "own pnode registry — BOTH ends inside PJM_Dominion. And PJM's 500 kV "
        "EHV nodes measure MORE price dispersion INSIDE the Dominion zone "
        "($6.18/$8.68/$16.78) than across the whole DOM-AEP boundary "
        "($4.76/$6.13/$14.42), a ratio of 1.30/1.42/1.16x. That is the "
        "ERCOT/MISO internal_congestion_split refusal class, established for PJM "
        "on PJM's own numbers. With that route closed, measured_ct_heat_rates "
        "was the only named lever left in the PJM queue, and it is chartered as "
        "a rule-14 [R-ACCURATE] ACCURACY correction rather than as a fix for the "
        "Dominion residual. "
        + _evidence()
        + " Rule 1 [R-STRUCT] and rule 14 [R-ACCURATE] order of reasoning, for "
        "the record: the delta was chartered because the measured loaded rate is "
        "more accurate than the eGRID plant-average estimate it replaces — "
        "demonstrably so at a mixed facility — and PREREG §2a/§4 recorded, "
        "BEFORE any arm solved, that it was expected to move the Dominion CT leg "
        "the WRONG way. Rule 14 is explicit that a measured input which worsens "
        "the backcast is kept and the worsening investigated, never buried back "
        "inside the estimate. PREREG §4's no-feedback ceiling was honoured: no "
        "multiplier, blend, scale, floor, cap, per-plant override or band "
        "widening was applied to the derived rates, and none may be."
    )


def _write(dest: Path, attested_by: str, *, add_entry: bool) -> None:
    """Write one arm's attestation from the keeper's."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=attested_by)
    fp = att["free_parameters"]
    if add_entry:
        names = {e["name"] for e in fp["entries"]}
        if NEW_ENTRY["name"] not in names:
            fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["n_entries"] = len(fp["entries"])
    # Unchanged on purpose: the delta adds no residual-identified parameter.
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {dest.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )


def main() -> int:
    """Write both arms' attestations from the keeper's."""
    keeper_residual = json.loads(KEEPER.read_text())["free_parameters"]["n_residual"]
    _write(ARM_A, ATTESTED_BY_A, add_entry=False)
    _write(ARM_B, _attested_by_b(), add_entry=True)
    print(f"keeper n_residual = {keeper_residual} (unchanged in both arms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
