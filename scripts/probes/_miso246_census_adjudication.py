"""miso-246 — the census ADJUDICATION LEDGER. Zero LP, no measurement.

Applies PREREG-miso246 §3's ordered classification rule to the enumeration
E1 (the shard's backcast-lane-reachable O/U cells, read mechanically) plus E2
(the curated named items) and E3 (the three handoff items). The classes are
``A`` already-adjudicated, ``G`` rule/owner-refused, ``D`` no DOF-free form,
``B`` data-blocked, ``S`` structurally blocked, ``LIVE``, and — disclosed in
ADDENDUM 2 §2 as a class the PREREG did not provide — ``Q`` open attribution
with no candidate mechanism.

**THE CONSERVATIVE DEFAULT, fixed before the table was written and applied
without exception: where the committed record is AMBIGUOUS or SILENT for MISO,
the route is classified `LIVE`.** That is the direction that makes the queue
NON-EMPTY, i.e. the direction against a convenient conclusion.

Each row carries its ``basis``: ``MEASURED`` (this session measured it),
``READ-EXPLICIT`` (the committed record contains an explicit MISO adjudication
or structural statement), or ``NONE`` (no MISO record — conservative default).

This script asserts that the hand-authored ledger covers EXACTLY the E1 set the
probe enumerates, so a cell cannot be silently dropped from the census.

Usage: ``python3 scripts/probes/_miso246_census_adjudication.py``
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "probes"))
OUT = REPO / "results/calibration/_miso246_census_adjudication.json"

# (class, basis, one-line reason with its citation)
E1: dict[str, tuple[str, str, str]] = {
    # ---- I: inert at MISO, on an explicit statement in the committed record ----
    "historic_outage_overlay": (
        "I",
        "READ-EXPLICIT",
        "base row: SUPERSEDED, now INERT ON THE DISPATCH",
    ),
    "startup_co2_reporting": (
        "I",
        "READ-EXPLICIT",
        "base row: reporting column, NEVER IN LP, so it cannot change a backcast solve",
    ),
    "state_carbon_pricing": (
        "I",
        "READ-EXPLICIT",
        "base row: registry prices exist for CAISO/NYISO/NEISO, NO-OP ERCOT/MISO (MISO has no RGGI/CARB member state). The base row flags the modelling choice as worth an explicit verdict; that is a documentation item, not an untested lever",
    ),
    "nyiso_ct_peaker_bands_measured": (
        "I",
        "READ-EXPLICIT",
        "MISO shard ev: five of six ISO CT_PEAKER curves price the min-load band above their own measured avg_committed_p50 and MISO IS THE ONE THAT GROUNDED IT (1.025/1.025), so the defect the mechanism repairs does not exist here; the shipped field additionally raises ValueError on any non-NYISO ISO",
    ),
    # ---- A: already adjudicated / not a mechanism ----
    "outage_artifact_provenance": (
        "A",
        "READ-EXPLICIT",
        "base row: CROSS-ISO AUDIT ROW, NOT A MECHANISM (no ScenarioConfig field), CLOSED at xiso-2 2026-08-02",
    ),
    # ---- S: structurally blocked by MISO's own corpus (miso-192, explicit) ----
    "coal_perplant_offer_level": (
        "S",
        "READ-EXPLICIT",
        "miso-192: MISO's offer corpus is masked with no fuel/technology attribute and the class bridge was REFUTED at miso-138 - 'Do not charter them'",
    ),
    "coal_peak_offer_margin": (
        "S",
        "READ-EXPLICIT",
        "miso-192, same corpus mask; miso-179 (R) / miso-180 (I) adjudicated the distributional form it forced",
    ),
    "coal_offer_net_revenue_margin": (
        "S",
        "READ-EXPLICIT",
        "miso-192, same corpus mask",
    ),
    "cc_committed_offer_margin": ("S", "READ-EXPLICIT", "miso-192, same corpus mask"),
    # ---- B: no MISO object of the kind the mechanism needs ----
    "winter_fuelsec_posture": (
        "B",
        "READ-EXPLICIT",
        "miso-194: NO MISO OBJECT IN KIND - the posture is an ISO-NE PROGRAM (FERC ER14-2407 oil-tank inventory in barrels); MISO's winter instruments are cold-weather operating procedures and Max Gen Events, and its oil-fired steam fleet is trivial. The ev states this is NOT a verdict and carries no DO-NOT-REDO",
    ),
    # ---- LIVE: the fuel family, MISO's most advanced open route ----
    "gas_variable_transport": (
        "LIVE",
        "READ-EXPLICIT",
        "O. Owner ruling 2026-09-06 fixed the convention as marginal commodity PLUS VARIABLE TRANSPORT, CONDITIONED on a measured transport component sourced first with zero fitted scalars; miso-225 phase 0 SOURCED it (frozen derive -> data/raw/reference/miso_gas_variable_transport.csv, CC_REGULAR v=$0.209/MMBtu of a $0.452 wedge, regression-free cross-check r=0.975). The joint arm passed the C1 gate that killed miso-224 and DIED ON G-3 BY 37 MW. Verdict not reached; cell still O",
    ),
    "gas_marginal_commodity_pricing": (
        "LIVE",
        "READ-EXPLICIT",
        "O, and rule 19 [R-ONE-MECH]: ONE PHENOMENON with gas_variable_transport - the ruled form arms them together. Counted ONCE in the LIVE route total. The bare-hub form miso-224 screened is refused by the same owner ruling",
    ),
    # ---- LIVE: the input-seam family, each with a MEASURED MISO footprint ----
    "f923_gas_price_plausibility_screen": (
        "LIVE",
        "MEASURED",
        "U, and the ONLY declared default flip on the backcast solve path since the keeper's own sha (203c031e, 2026-09-08 06:40Z, 49 min AFTER d059fcf7; default True at HEAD, frozen drop value False). ABSENT from the keeper's recorded scenario_config. SPP-49 measured MISO's footprint at zero LP: CT cheaper by $19/$13/$9 per MWh class-wide, CT +3.6/+2.5/+1.0 TWh",
    ),
    "nearby_fuel_price_zone_donor_guard": (
        "LIVE",
        "READ-EXPLICIT",
        "U. caiso-243 measured MISO's exposure as the LARGEST OF THE SIX (12 anomalous plant-months across 9 plants, max $198.46/MMBtu, 79 rows > $20); the MISO keeper runs the nearby fallback with no hub overlay, so the layer is live in all 36 months",
    ),
    "fleet_state_from_eia860": (
        "LIVE",
        "READ-EXPLICIT",
        "U, same measured exposure; the state tier is empty at MISO so the F923 state-tier reachability repair is untested here",
    ),
    "gas_offer_margin_anchor_vintage": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Row minted pjm-169, BUILT and default-off; MISO carries the same construction in kind (one frozen 2023-2025 anchor applied to whatever year is solved) and it is this lane's to adjudicate on its own market's data (rule 25)",
    ),
    # ---- LIVE: the outage / capacity-basis family ----
    "campd_per_unit_attribution": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Built by nyiso-176; the NARROWER form (unit_outage_mixed_gas_routing) is armed K at MISO, so this is a rule-19 reconcile, not a stack. Whether nyiso-175b's measured disagreement exists at MISO's armed facilities is UNMEASURED and is this lane's own zero-LP census",
    ),
    "campd_outage_merit_order_guard": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Built by nyiso-177; composes with the per-unit routing as its second, separately-adjudicated rung",
    ),
    "unit_outage_extract_basis_share": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Built by nyiso-196; the defect is a per-ISO DATA property and the transfer question is MISO's own zero-LP census (the _extract_basis_census construction)",
    ),
    "eia860_vintage_tracks_solve_year": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Built by pjm-167; ISO-agnostic engine, per-ISO verdict, MISO's own registry gap UNMEASURED",
    ),
    "cc_duct_peaking_row_scoped": (
        "LIVE",
        "READ-EXPLICIT",
        "U. Built by nyiso-198; the size of the defect is a per-ISO FLEET property and the transfer question is MISO's own zero-LP census. DIRECTION-MATCHED to item (c) - see M-c2",
    ),
    "cc_nameplate_summer_derate": (
        "LIVE",
        "READ-EXPLICIT",
        "U. miso-141 refused it as INSUFFICIENT for the summer double-count repair but states explicitly that NO TESTED VERDICT IS LICENSED and none is minted. DIRECTION-MATCHED to item (c)",
    ),
    "cc_summer_derate_reconciled_basis": (
        "LIVE",
        "NONE",
        "U, no MISO record. DIRECTION-MATCHED to item (c)",
    ),
    "cc_capacity_reconcile_path": (
        "LIVE",
        "NONE",
        "U, no MISO record. DIRECTION-MATCHED to item (c)",
    ),
    "cc_winter_capability_basis": (
        "LIVE",
        "NONE",
        "U, no MISO record. DIRECTION-MATCHED to item (c) only in winter",
    ),
    "unit_outage_lp_capacity_basis": ("LIVE", "NONE", "U, no MISO record"),
    "coal_nameplate_summer_derate": ("LIVE", "NONE", "U, no MISO record"),
    "coal_drop_pof": ("LIVE", "NONE", "U, no MISO record"),
    # ---- LIVE: the rest, conservative default ----
    "cc_steam_part_reclass": (
        "LIVE",
        "READ-EXPLICIT",
        "U. MISO is deliberately OUT of CC_STEAM_PART_RECLASS_ISOS and its only member (1004 Edwardsport) is a real coal-gasification CC the model holds as COAL; a MISO form needs its OWN charter and its OWN measured identification, which is a route, not a refusal",
    ),
    "hydro_budget_period_by_instrument": (
        "LIVE",
        "READ-EXPLICIT",
        "U, and a byte-identical NO-OP as shipped (HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT carries no MISO entry). The ROUTE - deriving MISO's own periods from its own projects' governing instruments - is untested. Landed mid-session at 5df6192f; it is the 313th cell that failed G-PARSE",
    ),
    "hydro_dispatch_envelope": ("LIVE", "NONE", "U, no MISO record"),
    "hydro_ror_split": ("LIVE", "NONE", "U, no MISO record"),
    "gas_commitment_bridge": (
        "LIVE",
        "MEASURED",
        "U, but DIRECTION-ADVERSE for item (c): M-c1 measures the model's CC_REGULAR running EXCESS overnight (shape deficit argmin at h0, -96.6/-63.1/-800.8 MW at the cheapest decile) and SHORT at h19, so a min-gen bridge worsens the measured shape. miso-130's descriptive pool census agrees (3/1,601 MW of day-anchored night-off CC in July 2023, 0 in 2024-25). LIVE as a cell (no verdict minted), NOT a candidate for (c)",
    ),
    "gas_st_startup_spread": ("LIVE", "NONE", "U, no MISO record"),
    "measured_ramp_capability": (
        "LIVE",
        "READ-EXPLICIT",
        "U, explicitly STILL UNTESTED and DELIBERATELY NOT MINTED at miso-156. WEAKENED by two committed MISO measurements the ev names: the model UNDER-ramps its measured fleet at every quantile (0.83/0.83/0.88 at p99) but miso-153's D-4 found reserves INERT at the summer peak (zero binding hours, dual $0.00), and a qualifier tightening a never-binding constraint cannot move a price",
    ),
    "lcr_tsl_published": (
        "LIVE",
        "NONE",
        "U, no MISO record; MISO's published analogues are LRR/LCR/CIL",
    ),
    "mass_cap_lp_row": ("LIVE", "NONE", "U, no MISO record"),
    "tac_load_coverage": (
        "LIVE",
        "NONE",
        "U, no MISO record (K at CAISO; rule 25 transfers nothing)",
    ),
    "td_loss_factor": ("LIVE", "NONE", "U, no MISO record"),
    "egrid_family_heat_rates": ("LIVE", "NONE", "U, no MISO record"),
    "egrid_identity_heat_rates": (
        "LIVE",
        "NONE",
        "U, no MISO record (K at NYISO; rule 25 transfers nothing)",
    ),
    "egrid_steam_collapse_heat_rates": ("LIVE", "NONE", "U, no MISO record"),
    "pumped_storage_cycling_depth": ("LIVE", "NONE", "U, no MISO record"),
    "storage_vintage_ramp": ("LIVE", "NONE", "U, no MISO record"),
}

# E2 — the curated named items, enumerated by hand from section 5.4's queue
# stamps and the miso-232..245 FINDINGs' handed-forward sections.
E2: dict[str, tuple[str, str, str]] = {
    "miso-174 item 1 — the seam-envelope hour-key rotation": (
        "A",
        "READ-EXPLICIT",
        "CLOSED BY PROMOTION: miso_seam_envelope_hour_ending_key is K on the keeper (miso-175)",
    ),
    "miso-174 item 2 — the coincident-peak seam-response object": (
        "A",
        "READ-EXPLICIT",
        "miso_seam_coincident_envelope is R at MISO, and the 2026-09-06 owner ruling excluded it by name ('explicitly not the miso-181 coincident-peak envelope (R)')",
    ),
    "miso-174 item 3 — M2M/CMP seam data scoped to the seam class": (
        "LIVE",
        "READ-EXPLICIT",
        "miso-77 section 2a: hourly per-flowgate FFE and M2M flows are publicly fetchable, EXT coverage 90/90/88 %; the no-PTDF blocker is materially weaker at a seam modelled as ONE link. Never chartered; shadow prices stay ANSWER-class",
    ),
    "miso-174 item 4 — the South under-EXPORT (+0.63/+0.35/+1.19 GW)": (
        "LIVE",
        "READ-EXPLICIT",
        "the second-largest disclosed component, NEVER SEPARATELY CHARTERED. South's neighbour-state route is closed and South is routed upstream to the gas price-out lane, but the under-export QUANTITY object is not adjudicated",
    ),
    "miso-241 — the SPP quantity-side charter": (
        "D",
        "READ-EXPLICIT",
        "REFUSED, NO DOF-FREE FORM, on miso-241 PREREG section 5's own rule; candidates C1-C7 with the C7 census over ALL of data/raw completed. Do not re-open without a new admissible measured series or an owner ruling",
    ),
    "miso-241 section 8.3 — lifting the envelope freeze (the C1 state-partition)": (
        "D",
        "READ-EXPLICIT",
        "costs EXACTLY ONE new free parameter (partition granularity, identification 'declared', DOF -> 42/2), reach bounded at ~25 % of SPP seam hours; an OWNER question that miso-241 explicitly did not ask",
    ),
    "miso-241 section 8.4 / miso-245 section 9.3 — the SPP seam is spread-driven and idle": (
        "Q",
        "MEASURED",
        "the model's SPP seam is 0.70-0.79 spread-correlated against a measured +0.0409/-0.0200/+0.0502, and sits at exactly zero flow in 42/41/48 % of hours. Reported, NOT a verdict, NAMES NO MECHANISM. This session's M-a4/P-a5 sharpen its cause: the seam's merit operand p_bus IS the model's own internal Midwest price (identity in 8,754/8,759/8,760 hours), so the seam is spread-driven BY CONSTRUCTION",
    ),
    "miso-236 section 5.4 — PJM's residual price alignment": (
        "Q",
        "READ-EXPLICIT",
        "OPEN and now WITHOUT A CANDIDATE EXPLANATION - the (month x hod) template was removed as the cause at miso-236 section 3",
    ),
    "miso-236 section 4 — MISO's OWN state is an UNUSED input on every seam": (
        "Q",
        "READ-EXPLICIT",
        "R^2_B 0.1243/0.0891/0.1802 (PJM), 0.1765/0.1916/0.1608 (SPP), 0.0453/0.0388/0.0501 (South) of each seam's MEASURED residual is explained by MISO's own state, and the model reproduces NONE of it. Named as 'an UNUSED input, not a missing one - cheaper to reach and requiring no new data at all'. NO MECHANISM NAMED, so not LIVE on the PREREG's own definition; the nearest form is refused by the same envelope freeze as C1",
    ),
    "miso-241 section 8.6 — the export-leg asymmetry on SPP/South/Manitoba": (
        "Q",
        "READ-EXPLICIT",
        "open, re-based by miso-241 section 2a (the repaired export leg is live in 1,244/1,416/1,595 hours, not 402/949/389). No mechanism named",
    ),
    "miso-245 section 9.2 — the seam-ladder source-data vintage": (
        "B",
        "READ-EXPLICIT",
        "WHICH hours of which series moved, and when, cannot be answered from the on-disk record: neither corpus carries SHA256SUMS.txt, the interchange README records no MISO re-fetch or merge event, and `git log --no-merges` returns only a post-rewrite commit because of the 2026-08-16 history rewrite",
    ),
    "miso-245 section 9.1 — the solve-surface cache-key gap": (
        "G",
        "READ-EXPLICIT",
        "NOT MISO'S TO CLOSE: market_sim.model.interchange.spec is explicitly outside the capx-D79 solve-surface phase 1 by design, and adding it from a MISO lane would re-key other ISOs' bundles (rule 24 / rule 25). Referred to the capx lane",
    ),
    "C3c — the designated frontier (2026-07-20)": (
        "G",
        "READ-EXPLICIT",
        "model 3/7/11 h > $200 against a measured 30/37/88. Opens ONLY by a new admissible measured identification under its own charter PLUS an owner ruling - never by an offer adder, ORDC offset, scarcity multiplier or any level tuned to the tail. misoenergy.org 5-minute workbooks are allowlist-blocked (HTTP 403)",
    ),
}

# E3 — the three handoff items, adjudicated by this session's own measurements.
E3: dict[str, tuple[str, str, str]] = {
    "(a) model bus-price compression (miso-242 Q-B)": (
        "Q",
        "MEASURED",
        "UNRESOLVED on my own pre-registered rule: M-a4 FAILED in 2023 (limb (ii) |dsigma| $1.0027 against a $0.05 bar) and M-a3's lever enumeration PROVABLY DID NOT CLOSE, both for the same reason the measurement gives. NOT a seam object: p_bus equals the internal Midwest price to the cent in 8,754/8,759/8,760 hours and the ladder explains 0.07/0.01/0.00 % of hours exclusively",
    ),
    "(b) Manitoba determinism (miso-236 section 5.3)": (
        "Q",
        "MEASURED",
        "M-b2 answered its own question - MERIT 3-0, Gamma_merit +0.1791/+0.1866/+0.3559 against Gamma_ceiling -0.1290/-0.1912/+0.1254 - and handed the object to item (a), which did not answer its own. INHERITS (a)'s UNRESOLVED status",
    ),
    "(c) CC_REGULAR 2024->2025 shape emergence (miso-234)": (
        "LIVE",
        "MEASURED",
        "REPRODUCED at HEAD and the direction is now named: the model runs CC_REGULAR EXCESS overnight (shape argmin h0) and SHORT at h19, span 270.8 -> 593.2 -> 1,254.8 MW. M-c2's candidate set splits: gas_commitment_bridge is DIRECTION-ADVERSE, the four coal/CC offer cells are S (masked corpus), and the CC CAPACITY-BASIS family (cc_duct_peaking_row_scoped, cc_nameplate_summer_derate, cc_summer_derate_reconciled_basis, cc_capacity_reconcile_path) is DIRECTION-MATCHED, untested at MISO and DOF-free in kind. LIVE",
    ),
}


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "p", REPO / "scripts/probes/_miso246_lever_queue_census_phase0.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    base = m.parse_base_rows(
        (REPO / "docs/codebase-site/data/mechanism-matrix.js").read_text()
    )
    cells = m.parse_shard(
        (REPO / "docs/codebase-site/data/mechanism-matrix/MISO.js").read_text()
    )
    enumerated = {
        k
        for k, v in cells.items()
        if v["cell"] in ("O", "U") and base[k]["mode"] in ("B", "BF")
    }
    missing = sorted(enumerated - set(E1))
    extra = sorted(set(E1) - enumerated)
    if missing or extra:
        print(f"LEDGER DOES NOT COVER E1 EXACTLY: missing={missing} extra={extra}")
        return 1

    def tally(d):
        out: dict[str, int] = {}
        for c, _, _ in d.values():
            out[c] = out.get(c, 0) + 1
        return dict(sorted(out.items()))

    # rule 19: gas_marginal_commodity_pricing + gas_variable_transport are ONE
    # phenomenon, so the LIVE ROUTE count is the LIVE CELL count minus one.
    live_cells = sum(1 for c, _, _ in E1.values() if c == "LIVE")
    rep = {
        "probe": "miso-246 census adjudication ledger",
        "prereg": "results/calibration/PREREG-miso246-the-backcast-lever-queue-census-2026-09-08.md",
        "zero_lp": True,
        "conservative_default": (
            "where the committed record is AMBIGUOUS or SILENT for MISO the route "
            "is classified LIVE — the direction that makes the queue NON-EMPTY"
        ),
        "E1_covered_exactly": True,
        "E1_n": len(E1),
        "E1_tally": tally(E1),
        "E1_live_cells": live_cells,
        "E1_live_routes_after_rule19_merge": live_cells - 1,
        "E2_n": len(E2),
        "E2_tally": tally(E2),
        "E3_n": len(E3),
        "E3_tally": tally(E3),
        "VERDICT": "QUEUE NON-EMPTY",
        "verdict_rule": (
            "PREREG §3: QUEUE EMPTY iff the LIVE set is empty. It is not: "
            f"{live_cells - 1} LIVE routes at the shard grain (E1), plus "
            f"{sum(1 for c, _, _ in E2.values() if c == 'LIVE')} at the curated "
            f"grain (E2) and {sum(1 for c, _, _ in E3.values() if c == 'LIVE')} "
            "of the three handoff items (E3)"
        ),
        "Q_class_disclosure": (
            "class Q (open attribution, no candidate mechanism) is a class the "
            "PREREG did not provide, disclosed in ADDENDUM 2 §2. On the PREREG's "
            "own verdict rule a Q route is NOT LIVE. |Q| is reported separately "
            "so a reader who holds otherwise can apply their own reading."
        ),
        "Q_counts": {
            "E1": sum(1 for c, _, _ in E1.values() if c == "Q"),
            "E2": sum(1 for c, _, _ in E2.values() if c == "Q"),
            "E3": sum(1 for c, _, _ in E3.values() if c == "Q"),
        },
        "E1": {
            k: {"class": v[0], "basis": v[1], "reason": v[2]}
            for k, v in sorted(E1.items())
        },
        "E2": {
            k: {"class": v[0], "basis": v[1], "reason": v[2]} for k, v in E2.items()
        },
        "E3": {
            k: {"class": v[0], "basis": v[1], "reason": v[2]} for k, v in E3.items()
        },
    }
    OUT.write_text(json.dumps(rep, indent=1) + "\n")
    print(f"E1 covered exactly: {len(E1)} routes")
    print(f"E1 tally: {rep['E1_tally']}")
    print(f"E2 tally: {rep['E2_tally']}   E3 tally: {rep['E3_tally']}")
    print(
        f"LIVE cells {live_cells}, LIVE ROUTES after the rule-19 merge {live_cells - 1}"
    )
    print(f"Q (open attribution, no mechanism): {rep['Q_counts']}")
    print(f"VERDICT: {rep['VERDICT']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
