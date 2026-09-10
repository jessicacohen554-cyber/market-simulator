"""Emit the SPP-64 calibration attestation for ``results/calibration/spp64_span``.

SPP-64 is the SPP-62 keeper recipe (``results/calibration/spp62_span``, SPP
keeper 7) plus **exactly one change**: ``st_gas_mustrun_per_plant`` is armed.
The per-plant commitment floor holds each gate-armed ST_GAS plant's measured
committed tranche (``committed_pct`` = P5-of-online = the LSL) in its top
``online_frac`` fraction of hours ranked by the model's own system load.

**THE DOF LEDGER IS INHERITED UNCHANGED — this lane adds ZERO free parameters**,
which is the substantive difference from the SPP-63 template this file is
adapted from. ``st_gas_mustrun_per_plant`` is a boolean gate, not a parameter;
the floor LEVEL (``committed_pct``) and the window SIZE (``online_frac``) are
each plant's own CAMPD record read from the rule-23-frozen
``thermal_tranches_SPP.csv``, which this lane neither regenerates nor touches.
No scalar is introduced, none is tuned, and nothing was swept against any gate.
So ``n_entries`` stays 3 and ``n_residual`` stays 2.

WHY IT EXISTS AT ALL is the object ``docs/handoffs/FINDING-spp-46-2026-09-07.md``
§0.2 named and left open — "the vertically-integrated steam cohort at plausible
inputs, whose admissible construction is a market-design (self-commitment)
object". Its items (1) and (2) landed (the EIA-923 gas-price plausibility screen
and the simple-cycle heat-rate floor, both armed in keeper 7) and (3) was carried
by SPP-62's census. Item (4) is this arm. Record:
``docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`` and
``docs/handoffs/FINDING-spp-64-2026-09-10.md``.

This is NOT the ``replay_keeper --out-dir`` attestation gap being papered over:
that driver does not propagate ``calibration_attestation.json`` into an
``--out-dir`` bundle (SPP-62 §8 routed the shared-path defect), so without this
script the span scores C6 UNATTESTED for a plumbing reason rather than a
governance one.

Usage:
    python scripts/gen_spp64_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp62_span/calibration_attestation.json"
BUNDLE = REPO / "results/calibration/spp64_span"


def build() -> dict:
    """Return the SPP-64 attestation: keeper 7's ledger, unchanged, plus the switch."""
    att = json.loads(KEEPER.read_text())

    fp = att["free_parameters"]
    fp["inherited_from"] = "spp62_span (SPP keeper 7)"
    fp["inheritance_basis"] = (
        "SPP-64 is the SPP-62 recipe plus ONE armed ScenarioConfig gate, "
        "st_gas_mustrun_per_plant. Every keeper-7 entry carries over unchanged: "
        "no offer band, structural share, shared default or solve-path code is "
        "touched, and the authorized price-tuning channel declared below is "
        "replayed VERBATIM at 0.93 and NOT re-cut by this lane. NOTHING IS "
        "ADDED: the gate is a boolean, and the floor's level (committed_pct) "
        "and window size (online_frac) are each plant's own CAMPD record in the "
        "rule-23-frozen thermal_tranches_SPP.csv, which this lane does not "
        "regenerate or touch. n_entries stays 3 and n_residual stays 2."
    )
    # Rule 21 [R-DOF]: recomputed from the inherited entries, never retyped.
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]
    gov["attested_by"] = (
        "SPP-64 (2026-09-10): SPP keeper 7's recipe "
        "(2026-09-10-spp-62-vintage-census — the R-ay coal supply-class census "
        "repair on keeper 6's eia860_vintage_tracks_solve_year, itself on "
        "SPP-52a's authorized offer-curve level) plus ONE change: "
        "st_gas_mustrun_per_plant armed, with st_gas_mustrun_p25_level left "
        "FALSE. ONE --years 2023 2024 2025 invocation, years sequential "
        "(rules 12 / 16). The authorized price-tuning channel declared above is "
        "replayed VERBATIM at 0.93 on all four bands of the ten registered "
        "fossil classes and is NOT re-cut by this lane; no multiplier was swept "
        "against any gate (rule 1 [R-STRUCT] condition (c)). Rule 21 [R-DOF]: "
        "ledger inherited from keeper 7 with ZERO additions — n_entries 3, "
        "n_residual 2, both unchanged. The arm was screened on 2023 — the year "
        "of the mechanism's own largest measured footprint, named in the "
        "PRECOMMIT before the solve and demonstrably NOT the failing-residual "
        "choice (2024 carries the larger C1 miss and the smaller footprint) — "
        "against six structural STOP gates, none of which reads the target "
        "C1 ST_GAS row."
    )

    gov["measured_input_switches"]["st_gas_mustrun_per_plant"] = {
        "value": True,
        "p25_level_armed": False,
        "where": (
            "ScenarioConfig.st_gas_mustrun_per_plant. Applied in "
            "data/fleet/arrays.py as a per-(unit, hour) min_gen floor stamped "
            "MECH_ST_GAS_MUSTRUN_PER_PLANT: each gate-armed ST_GAS plant's "
            "committed tranche level is held in its top round(online_frac * "
            "8760) hours ranked by the model's own system load "
            "(np.argsort(-sys_load)), each tranche clipped to pmax * "
            "availability that hour so an outage relaxes the floor."
        ),
        "identification": "measured-physical",
        "source": (
            "data/raw/_processed-legacy/thermal_tranches_SPP.csv — SPP's own "
            "CAMPD record, 22 ST_GAS plants. LEVEL = committed_pct "
            "(P5-of-online = the minimum stable load). WINDOW SIZE = "
            "online_frac (0.286-0.954, mean 0.518). Rule 23 [R-FROZEN-DERIVE]: "
            "the artifact is not regenerated by this lane and no value in it is "
            "re-derived. Rule 25 [R-ISO-SCOPE]: SPP's own data only; nothing is "
            "carried from MISO or any other ISO."
        ),
        "warrant": (
            "Rule 17 [R-FLOOR-WINDOW] triple. DRIVER: SPP's gas-steam fleet is "
            "100.0 % EIA-860 Sector 1 'Electric Utility' — 9,515 of 9,515 MW, "
            "zero IPP (OG&E 2,887.5, PSO 2,111.0, Southwestern Public Service "
            "1,772.0, SWEPCO 1,543.0, plus four co-ops/municipals). A "
            "vertically-integrated utility self-commits its own steam to serve "
            "native load rather than making a merchant start/stop decision "
            "against the LMP. Sector is a published per-plant integer — the same "
            "admissibility class the owner ruled on for PJM at capx D53/D78 "
            "(Q56: 'zero free parameters, a partition on one published per-plant "
            "boolean'). The reading is not vacuous: the same census reads "
            "CC_REGULAR 68.9 % Sector 1 / 31.1 % IPP and CT_PEAKER 99.7 %. "
            "WINDOW: each plant's own measured synchronization fraction placed "
            "in the top system-load hours, self-limiting so a genuine cycler "
            "floors only its top-load sliver. FORWARD STORY: committed_pct and "
            "online_frac re-derive from each new multi-year CAMPD vintage, and a "
            "retired or deregulated plant leaves the artifact. This is the "
            "object FINDING-spp-46 §0.2 named and left open."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED] admissibility is met, and the distinction from "
            "what SPP-46 refused is the whole point. SPP-46 declared INADMISSIBLE "
            "'the measured-state form (CAMPD online hours as the floor window)' — "
            "a window that replays the meter's own on/off record — and SPP-44 "
            "killed the P0-anchored form. THIS window is neither: it is a SCALAR "
            "FRACTION placed by the MODEL'S OWN system-load rank, so it "
            "regenerates for a forward year from forward drivers and responds to "
            "changed conditions (a different load shape re-composes the floored "
            "hour set). No output is pinned to an actual: dispatch above the "
            "floor stays free. SPP-44's stated re-test condition was 'a MEASURED "
            "commitment-state membership on the ST_GAS fleet ... never this leg "
            "re-armed on the P0 pattern', and this is that membership and not "
            "that pattern. The lane records that this is a judgement at the edge "
            "of a prior adjudication, put to the gates rather than asserted."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH], MACHINE-VERIFIED. Keeper 7's own committed "
            "legitimacy_diagnostics.json D-2 lists every forcing mechanism in the "
            "run — nuclear_mustrun and chp_steam (CC_CHP / CT_CHP / ST_CHP) — and "
            "ST_GAS does not appear at all. Corroborated by two on-recipe "
            "run_year(fleet_only=True) rebuilds of the 2023 recipe: ST_GAS "
            "min_gen 0.0000 -> 3.8701 TWh with EVERY other class moving exactly "
            "0.0000. pmin_mw, min_run_hours, min_down_hours and "
            "startup_cost_per_mw are 0 on every SPP fossil unit, so this adds ONE "
            "mechanism to ONE class that had none. Nothing is stacked and nothing "
            "is replaced. st_gas_mustrun_p25_level is NOT armed: its rationale is "
            "MISO's own out-of-market VLR record (Entergy South) and rule 25 "
            "forbids carrying that driver to SPP."
        ),
        "level_choice": (
            "Rule 1 [R-STRUCT]: the level was fixed ex ante and is the SMALLEST "
            "of the three the artifact offers — committed_pct (the LSL, 9.090 "
            "TWh on an all-on basis) against p25_cf (14.427) and median_cf "
            "(23.319). It is the level the field's own docstring calls 'the "
            "correct min-stable-load'. A level chosen to close a gap would have "
            "been one of the larger two."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: the gate is armed for SPP alone via --set, "
            "the shared dataclass default stays False, and every other ISO and "
            "every committed keeper is byte-identical. The floor is driven "
            "entirely by SPP's own per-ISO CAMPD artifact; no MISO verdict, "
            "level or window fills this cell."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: one registered ScenarioConfig field plus one "
            "registered committed artifact. No env-var knob, no per-plant dict "
            "in a data/ module, no getattr fallback literal in the offer path."
        ),
        "forced_budget": (
            "Rule 20 [R-FORCED-BUDGET] is DECLARED AT THE GATE, not discovered "
            "after: ST_GAS carries a materially raised forced share against "
            "d2_merchant_max_share 0.30, and ST_GAS is not in d2_exempt_classes. "
            "Two things the scored span adjudicates rather than this file: "
            "(i) whether a class measured 100 % regulated-utility is a MERCHANT "
            "class within the rule's own words; (ii) failing that, the rule's "
            "conditional pass on provenance + shape, for which the D-4 window "
            "entry already exists ((MECH_ST_GAS_MUSTRUN_PER_PLANT, 'ST_GAS'): "
            "(0, 24), self-windowing, so off-window binding is nil by "
            "construction) and D-1 profile_r >= 0.80 / cv_ratio >= 0.50 is the "
            "genuinely uncertain leg. If the span lands over budget and D-1 "
            "misses, this arm is not a keeper and the lane says so."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-64 span bundle."""
    att = build()
    out = BUNDLE / "calibration_attestation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")
    print(f"  entries: {[e['name'] for e in fp['entries']]}")


if __name__ == "__main__":
    main()
