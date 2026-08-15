"""Write ``calibration_attestation.json`` for the nyiso-100 KEEPER-RECOMMENDED arm.

``2026-07-30-nyiso-100-silretire`` (``results/calibration/nyiso100_silretire``)
passes every pre-registered gate in
``docs/PREREG-nyiso100-simultaneous-import-retire-2026-07-30.md`` §3. This
script builds the C6 attestation the promotion requires (rule 21 ``[R-DOF]``:
every keeper carries a DOF ledger), inheriting the nyiso-99 keeper's UNION'd
23-entry ledger and adding ONE entry for the arm's single delta.

The delta **removes** a free parameter rather than adding one. The retired
4,350 MW scalar was, moreover, a solve-affecting constant that carried NO
ledger entry of its own — so retiring it also closes a rule-24 ``[R-REGISTRY]``
gap. ``n_entries`` goes 23 -> 24 (the new entry documents the removal) while
``n_residual`` stays 6.

**C3c EXCEPTIONS LEDGER (added 2026-07-31, owner decision).** The same
attestation now also carries the ``exceptions`` block that reclassifies C3c
(``price_tail``) from an undocumented FAIL to a documented caveat, which is what
moves NYISO's determination NOT-YET -> CALIBRATED-WITH-CAVEATS. The entries are
NOT a claim that the benchmark is wrong: the measured RT tail is real and the
model under-produces it. They record that the tail is a **structural
representation-frontier limitation with the lever queue exhausted**, in the
shape MISO's own ``price_tail`` entry established — the honest classification,
not a borrowed measured-input excuse. Rule 1 ``[R-STRUCT]`` is why this is a
ledger entry and not a mechanism: the remaining ways to lift the tail are
fitted, and a fitted tail is worse than a missing one.

Usage:
    python scripts/gen_nyiso100_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRIOR_KEEPER = (
    REPO / "results/calibration/nyiso99_demandfix/calibration_attestation.json"
)
DEST = REPO / "results/calibration/nyiso100_silretire/calibration_attestation.json"

NEW_ENTRY = {
    "name": (
        "NYISO_simultaneous_import RETIRED (nyiso_import_sil_retire) — "
        "mis-attributed G-J locality limit removed from the external seam"
    ),
    "where": (
        "ScenarioConfig.nyiso_import_sil_retire -> "
        "model.interchange.import_nodes.retire_misattributed_sil, applied in "
        "interchange.spec.apply_interchange_topology; drops the "
        "EXTERNAL_SIMULTANEOUS_LIMITS['NYISO'] InterfaceLimit"
    ),
    "identification": "measured-physical",
    "lineage_solves": (
        "1 A/B pair, 0 sweeps. Built to a pre-registration "
        "(docs/PREREG-nyiso100-simultaneous-import-retire-2026-07-30.md, "
        "committed AND PUSHED before any LP ran) on top of an identification "
        "that used NO solve at all (the finding is a provenance + posted-"
        "ratings argument read off published tables and the committed keeper "
        "sidecars). No value was swept and none was adjusted after the "
        "result — there is no value to adjust, because the arm sets no "
        "number."
    ),
    "value": (
        "NO PARAMETER — the entry records a REMOVAL. The retired scalar was "
        "4,350 MW; nothing replaces it. The seam's aggregate bound becomes "
        "the sum of the four border-link TTCs already in the topology, "
        "6,800 MW, which is not a new constant but an emergent consequence "
        "of per-link ratings that were already there. Realised arm import "
        "maxima 6,518.9 / 6,470.0 / 6,075.0 MW (2023/2024/2025) — below the "
        "link sum, so the LP is bounded by the priced ladder and the "
        "per-link ratings, not by a scalar."
    ),
    "source": (
        "The 4,350 MW value is EXACTLY the published NYISO G-J LOCALITY Bulk "
        "Power Transmission Limit for capability year 2024/2025 "
        "(data/raw/capacity-deliverability/nyiso/nyiso.csv, area 'G-J', "
        "metric import_limit; 2024-25 Locality Bulk Power Transmission "
        "Capability Report p.7) — an INTERNAL New York transfer boundary "
        "(Load Zones G,H,I,J), not the external NYCA seam. Exactly one row "
        "in the whole published table matches the constant, and the "
        "published G-J series MOVES by capability year (3,425 / 3,425 / "
        "4,350 / 4,500 for 2022/23-2025/26) while the constant was frozen at "
        "the 2024/25 reading across all three solve years. The originally "
        "cited source does not contain it: extraction over all three Gold "
        "Books on disk finds ZERO pages naming a simultaneous import or "
        "transfer limit, and Table VI-1 is redacted as Critical Energy "
        "Infrastructure Information in every edition. The retained per-link "
        "bounds ARE posted ratings (NYISO MIS P-32 external limits): NYC "
        "1,000 MW vs HTP 660 + Linden-VFT 315 = 975 posted; Long_Island "
        "1,200 MW vs Neptune 660 + Cross-Sound 330 + NPX-1385 200 = 1,190 "
        "posted. No residual was consulted (rule 23 [R-FROZEN-DERIVE])."
    ),
    "forward_story": (
        "Strictly stronger forward than what it replaces: there is no scalar "
        "left to regenerate. The bound that remains is the per-link posted "
        "rating, which re-derives from the P-32 posting for any year and "
        "responds to changed conditions (CHPE enters the same feed as a "
        "nineteenth interface in 2026). The retired constant, by contrast, "
        "was a single capability year of an INTERNAL locality's limit and "
        "would have had to be hand-refreshed — against the wrong boundary — "
        "for every forward year."
    ),
    "rule_13_admissibility": (
        "No measured OUTCOME enters the model. The measured simultaneous "
        "flow series (EIA-930 metered, MIS P-32 scheduled) are used ONLY to "
        "FALSIFY the retired constant and to bound an admissible interval "
        "for an aggregate cap — never to set one, which is precisely why the "
        "reconcile retires the scalar instead of restating it at a measured "
        "extreme. Rule 14's misalignment clause is why the naive measured "
        "replacement (the ~10.7 GW sum of posted per-interface limits) is "
        "rejected: it is the sum of several parallel paths this five-zone "
        "network collapses into one link. The quantities that DO enter are "
        "posted ratings already in the topology."
    ),
}

ATTESTED_BY = (
    "nyiso-100 KEEPER-RECOMMENDED 2026-07-30: the 2026-07-29-nyiso-99-"
    "demandfix keeper recipe re-solved via scripts/replay_keeper.py (which "
    "reads the keeper's own meta.json, so the recipe is reproduced exactly) "
    "with ONE delta — nyiso_import_sil_retire. THE SESSION'S PRIMARY RESULT "
    "IS AN IDENTIFICATION, AND IT IS A PROVENANCE RESULT, NOT A NEW NUMBER. "
    "The nyiso-99 charter carried this forward as 'a hand-set estimate "
    "measurement contradicts'. That framing was too generous: 4,350 MW is a "
    "REAL published NYISO quantity measured on the WRONG BOUNDARY — the G-J "
    "LOCALITY Bulk Power Transmission Limit for capability year 2024/2025 "
    "(Load Zones G,H,I,J, an INTERNAL New York transfer boundary), installed "
    "as the EXTERNAL NYCA simultaneous-import cap and frozen at one "
    "capability year of a series that moves 3,425 / 3,425 / 4,350 / 4,500. "
    "Three corroborations that this is mis-attribution and not coincidence: "
    "(a) exactly ONE row in the entire published import_limit table equals "
    "the constant, and it is the G-J row, while the constant is applied "
    "unchanged to 2023 whose own capability-year value is 3,425; (b) the "
    "constant's OWN justification comment argued from INTERNAL downstate "
    "interfaces ('Dunwoodie-South 3.9 GW into NYC, cable-limited 1.65 GW "
    "into LI') — an internal-boundary rationale attached to an external "
    "limit — and its border-link arithmetic omitted the Capital_Hudson link "
    "entirely (it summed 5.2 GW against a real 6.8 GW); (c) the CITED SOURCE "
    "DOES NOT CONTAIN IT — extraction over all three 2023-2025 Gold Books on "
    "disk finds ZERO pages naming a simultaneous import or transfer limit, "
    "and Table VI-1 is REDACTED as Critical Energy Infrastructure "
    "Information in every edition, so NYISO publishes no aggregate external "
    "simultaneous import limit available to this repo at all. MEASUREMENT "
    "FALSIFIES IT AS AN EXTERNAL BOUND: NYCA net import reached 5,929 / "
    "5,662 / 5,872 MW metered (EIA-930) and 7,078 / 7,298 / 6,727 MW "
    "scheduled (MIS P-32), exceeding 4,350 MW in 287/314/145 h and "
    "865/685/388 h respectively — and the P-32 sum is cross-validated as "
    "NYCA net interchange rather than a double-count of the three HQ rows "
    "(UTC-joined r 0.910/0.906/0.879, bias +17/-179/-262 MW on means of "
    "2,677/2,322/2,612 MW; a double-count would bias ~+1,200 MW). WHY THE "
    "RECONCILE RETIRES RATHER THAN RAISES: the naive measured replacement — "
    "the sum of posted per-interface P-32 limits, 10,575/10,715/10,450 MW — "
    "is PRECISELY rule 14's named misalignment exception, several parallel "
    "paths this five-zone network collapses into one link, and NYISO "
    "publishes no external simultaneous limit to substitute. But the "
    "misalignment does NOT extend to every path: for the two links whose tie "
    "sets are point-to-point HVDC converters there is no parallel-path "
    "ambiguity at all, and the model is ALREADY at the posted rating (NYC "
    "1,000 vs 975 posted; Long_Island 1,200 vs 1,190 posted), with the AC "
    "seams sitting behind the internal Central-East chain the topology "
    "already carries (2,850 MW model vs a P-32 CENTRAL EAST - VC posted "
    "median of 2,865 MW). Retiring the scalar therefore introduces NO new "
    "number and REMOVES a free parameter; the resulting aggregate, the "
    "border-link sum 6,800 MW, lies INSIDE the measured admissible interval "
    "[5,929 lower bound, 10,715 posted-rating upper bound], where the "
    "retired 4,350 MW lay OUTSIDE it in all three years. Rule 19 "
    "[R-ONE-MECH] reinforces it: shared-upstream-capacity limitation already "
    "has a mechanism here (the internal interface chain); the scalar was a "
    "second one, stacked on the first and pointed at the wrong boundary. "
    "RULE-24 [R-REGISTRY] SIDE EFFECT: the retired constant was a solve-"
    "affecting value that carried NO DOF ledger entry of its own, so the "
    "retire also closes a registry gap."
)

RESIDUALS_NOTE = (
    "SCORED EFFECT vs the nyiso-99 keeper. EVERY PRE-REGISTERED GATE PASSED; "
    "the two REPORTED diagnostics moved slightly adversely and are recorded "
    "here without being used to justify anything (rule 1 [R-STRUCT]: a "
    "structurally-correct mechanism is never judged on whether the residual "
    "moved, in EITHER direction). G0 CONTROL IDENTITY: a separate same-HEAD "
    "zero-delta control (2026-07-29-nyiso-100-control-zerodelta) reproduces "
    "the nyiso-99 keeper BIT-FOR-BIT in all three years — max |delta class "
    "MW| 0.000000 and max |delta price| 0.000000 $/MWh — so this container "
    "reproduces the keeper and every arm delta below is attributable to the "
    "single flag. G1 LIVE-MECHANISM (nyiso-89 section 4a): the arm's solved "
    "topology carries ZERO import-node interface limits and the control "
    "exactly one at 4,350 MW, confirmed both by topology rebuild and by the "
    "arm's own solve log; the arm is not a silent no-op. G2 THE MECHANISM "
    "RELEASES: model import maximum 4,350.0 -> 6,518.9 / 6,470.0 / 6,075.0 "
    "MW, hours pinned AT the old cap 548/689/176 -> 0/2/0, hours above it "
    "0/0/0 -> 436/587/161. Every annual maximum lands inside the "
    "pre-registered (4,350, 6,800] window. G3 VOLUME STAYS BAND-HELD: the "
    "+-2% monthly reconciliation band holds in every month of every year "
    "(ratio range [1.020,1.020] in 2023/2024, [0.995,1.020] in 2025) and the "
    "count of months at the upper edge RISES 10/11/11 -> 12/12/11, so the "
    "arm reallocates a band-bounded quota rather than escaping it. Import "
    "energy therefore moves only +0.041/+0.070/+0.035 TWh (+0.17/+0.34/"
    "+0.18 %), all of it the band ceiling being reached in two more months. "
    "G4 C1 PROTECTION: 'C1 all 14/14 · free 10/10', IDENTICAL to the keeper. "
    "The knife-edge 2023 CC_REGULAR cell still passes and DOES move under this "
    "delta, unlike under nyiso-99's: -2.79 of +-2.94 in the control (32.512 "
    "TWh, the prior keeper's own value) -> -2.80 in the arm (32.497 TWh), a "
    "~15 GWh/yr CC_REGULAR shift, still comfortably inside band. G5 "
    "PROTECTIVE GATES: C7 PASS and C8 PASS. The fragile 2024 ST_GAS "
    "grounded-above-budget cell moves 30.4 % -> 30.6 % forced, i.e. slightly "
    "further above the 30 % cap — but it remains a GROUNDED pass and its "
    "grounding evidence IMPROVES on both legs (D-1 profile r 0.954 -> 0.958, "
    "off-peak CV ratio 0.957 -> 0.972), with every binding mechanism still "
    "clearing D-4. G6 C3c REPORTED, NOT TARGETED AND NOT CLAIMED: hours > "
    "$300 4/0/7 -> 3/0/7 against actuals 10/12/42, i.e. 2023 loses one hour "
    "and 2024/2025 are unchanged; mean LMP 33.56/36.32/58.98 -> "
    "33.49/36.22/58.95. C3c REMAINS THE SOLE DETERMINATION BLOCKER and the "
    "determination stays NOT-YET, exactly as for every prior NYISO keeper. "
    "The pre-registration predicted C3c would tick UP (band-fixed volume "
    "reallocated overnight leaving less import at peak); it ticked DOWN "
    "slightly instead, because volume was not in fact fixed — reaching the "
    "band ceiling in two more months added ~0.15 TWh of supply. THAT "
    "PREDICTION IS RECORDED AS WRONG rather than re-narrated. G7 ITEM-9 "
    "IMPORT SHAPE REPORTED: r_hr 0.598/0.623/0.453 -> 0.584/0.605/0.451, "
    "worse in all three years — as the pre-registration predicted, and for "
    "the reason it gave: the retired cap was binding 54/59/62 % OVERNIGHT "
    "(h21-h03) and only 3/2/2 % in h16-h18, so releasing it lets the LP buy "
    "more of its quota in the model's wrong-phase overnight peak. This is "
    "NOT evidence against the arm: item 9 is CLOSED as an attributed C3c "
    "symptom (nyiso-99, matrix row import_shape_lever -> G), the import "
    "node is EXONERATED, and the phase inversion is a property of NYISO's "
    "too-flat INTERNAL price swing (0.58/0.52/0.46 of the real one), not of "
    "the seam. A cap that improved r_hr by truncating the model in hours the "
    "REAL system imported LESS than the cap in 84/89/94 % of cases was "
    "flattering the statistic, not modelling the market. SLACK AND DUMP "
    "STAY EXACTLY 0.0 MWh in every year, both runs."
)

OPEN_ITEMS = [
    "FOLLOW-ON LEVER, DELIBERATELY NOT ARMED HERE (single-delta discipline): "
    "the published G-J locality limit is a REAL NYISO constraint the "
    "topology does not represent AT ITS OWN BOUNDARY, and retiring the "
    "scalar removes its only (misplaced) representative. Representing it "
    "belongs on the INTERNAL G-J interface in the nyiso_nyc_lcr_tsl / "
    "nyiso_li_lcr_tsl family — a published locality limit applied to an "
    "internal link inside its design-condition window — never on the "
    "external seam. It enters the mechanism matrix as U (untested). NOTE it "
    "owes its own rule-14 boundary reconciliation first: the five-zone "
    "aggregation carries no clean G-J cutset (Zone G sits in "
    "Capital_Hudson, H+I in Lower_Hudson, J is NYC).",
    "C3c remains the SOLE determination blocker and a DIAGNOSED, UNCLOSED "
    "structural limitation of the five-zone representation with an EMPTY "
    "lever queue (nyiso-94/95/96/97 closed every candidate; re-open "
    "conditions FINDING-nyiso97 section 5, none currently satisfiable). "
    "Unchanged by this arm and not targeted by it.",
    "PRE-EXISTING AND UNCHANGED, INHERITED NOT CAUSED: D-5 forecast/backcast "
    "parity FAILs on nyiso_local_selfsupply ('active backcast-only for this "
    "config but NOT on the declared backcast-overlay list'). The nyiso-99 "
    "keeper's own committed legitimacy_diagnostics.json carries the "
    "identical row, as does this session's zero-delta control. It is a "
    "declaration-list gap, not a dispatch defect, and needs its own session.",
    "Carried from nyiso-96/98/99: the keeper-lineage meta still arms "
    "dual_fuel_oil_reattribution for NYISO — a recording basis the CLI has "
    "since pinned NEISO-only; dropping it is a zero-dispatch-delta cleanup "
    "for the next re-solve (queue item 10).",
    "Carried from nyiso-98: two 2025 months (Feb, Apr) hit the frozen "
    "nuclear SCALE_CLIP 1.25 and reconcile only to -0.62 %/-0.32 %, inside "
    "WEDGE_TOL but at its edge; re-check if a future NRC year lands "
    "(rule 23 — data change only, never a residual).",
    "Carried from nyiso-99 and STILL OPEN: the EIA-930 exactly-0.0 "
    "zero-dropout audit was swept cross-ISO for the Demand column only. The "
    "NG:* COMPONENT series of the other five ISOs were never swept. "
    "Instrument to copy: scripts/probes/nyiso99_import_benchmark_provenance"
    ".py. Method note carried forward and re-confirmed this session: align "
    "MIS/instrument feeds on UTC, never positionally — the model clock is "
    "8,760 h even in leap-year 2024 while P-32 posts all 8,784, and "
    "positional alignment shears the series after Feb 29 (r 0.906 -> 0.774).",
    "NOT re-tested and NOT to be re-opened: the import ladder's price "
    "granularity (2,970 MW of the 6,580 MW ladder carries a per-year "
    "constant price). A finer ladder cannot fix a spread that peaks at the "
    "wrong hour — nyiso-99 characterisation, unchanged here.",
]


# C3c exceptions ledger (owner decision 2026-07-31). One entry per scored year —
# scripts/calibration_verdict.py::_ledger_match keys on (criterion, year), and
# the criterion is only lifted out of FAIL when EVERY failing year is covered.
# Counted as ONE ledgered caveat against MAX_LEDGERED_CAVEATS = 3.
_C3C_FRONTIER = (
    "NYISO C3c is a DIAGNOSED, UNCLOSED STRUCTURAL LIMITATION of the five-zone "
    "representation with an EXHAUSTED lever queue — not an untried gate. Every "
    "candidate is adjudicated on the record (docs/mechanism-testing-matrix.md "
    "§5.5): the J/K-commitment and reserve-tier routes closed in full "
    "(nyiso-83/84, SRMC roof ~$258 mainland); DA virtual depth and the TSA "
    "transfer derate REFUSED ex-ante on identification (nyiso-94/95 — NYISO "
    "publishes no submitted-curve equivalent, and P-59 zonalBidLoad carries no "
    "price axis, so net(λ) would need an assumed price distribution = a fitted "
    "scalar, rule 21); unit_outage_short_windows INERT ex-ante (nyiso-93, "
    "coal-only detector and NYISO has no coal); the CT start-frequency lane "
    "closed and tranche_startup_amortization tested (nyiso-96); the LAST "
    "surviving candidate — SCUC load-pocket security commitment + BPCG "
    "(NYC/LI sub-zonal) — closed ex-ante on CONTENT, not merely access "
    "(nyiso-97: the as-enforced AORR is MyNYISO-walled AND the public "
    "2008-vintage Appendix B carries no derivable NYC parameter, every Con Ed "
    "in-city commitment row being condition-triggered on TO contingency "
    "analysis with parameters in unpublished SO procedures); the import hourly "
    "shape REFUSED as an attributed C3c SYMPTOM with the seam exonerated "
    "(nyiso-99); the G-J locality limit REFUSED ex-ante for want of a "
    "representable boundary (nyiso-101 — Capital_Hudson straddles the "
    "locality, and two of its four real boundary legs are not LP quantities). "
    "The one nominally-open item, nyiso_iroquois_winter_spread (item 4), is "
    "blocked on a JOINT summer scarcity lever and its construction conserves "
    "the annual spread, so re-arming alone just moves the miss to summer — and "
    "the summer lever queue is precisely what is exhausted: nyiso-92 dated the "
    "actual RT tail as SUMMER (2025 Jun 23-25 alone = 18 of 42 h; the Jan-2024 "
    "storm produced ZERO >$300 hours), capping the winter-fuel lane at ~4-5 "
    "h/yr. RULE 1 [R-STRUCT] IS WHY THIS IS A LEDGER ENTRY AND NOT A "
    "MECHANISM: every remaining way to lift the tail is fitted to the tail "
    "residual, and a tail reached through a mechanism that isn't real is worse "
    "than a missing tail. RE-OPEN CONDITION (satisfiable, unlike the gate "
    "itself): a Capital_Hudson -> Zone-F/Zone-G TOPOLOGY SPLIT, which makes "
    "the sub-zonal load pocket representable — it needs its own owner charter "
    "(the ERCOT West/Panhandle class, CLOSED) and is NOT a mechanism-flag "
    "lever. Evidence: docs/FINDING-nyiso97-load-pocket-identification-"
    "2026-07-29.md §5, docs/FINDING-nyiso-c3c-scarcity-formation-2026-07-26.md."
)
EXCEPTIONS = [
    {
        "criterion": "price_tail",
        "year": year,
        "metric": "hours RT-expressible LMP > $300/MWh (C3c scarcity tail, actual RT hourly gate)",
        "magnitude": magnitude,
        "classification": (
            "MODEL MISS (structural — five-zone representation cannot form the "
            "sub-zonal NYC/LI load-pocket scarcity that sets NYISO's real RT "
            "tail; representation-frontier caveat, every admissible mechanism "
            "tried on record per rule 1 [R-STRUCT])"
        ),
        "reason": _C3C_FRONTIER,
    }
    for year, magnitude in (
        (2023, "model 3h vs RT actual 10h (0.30x, >$300); DA actual 1h"),
        (2024, "model 0h vs RT actual 12h (0.00x, >$300); DA actual 0h"),
        (2025, "model 7h vs RT actual 42h (0.17x, >$300); DA actual 12h"),
    )
]


def main() -> int:
    """Build nyiso-100's attestation from the nyiso-99 keeper's."""
    att = json.loads(PRIOR_KEEPER.read_text())
    gov = dict(att.get("governance", {}))
    gov["attested_by"] = ATTESTED_BY
    gov["residuals_note"] = RESIDUALS_NOTE
    att["governance"] = gov
    att["_open_items"] = OPEN_ITEMS
    att["exceptions"] = EXCEPTIONS
    fp = att["free_parameters"]
    names = {e["name"] for e in fp["entries"]}
    if NEW_ENTRY["name"] not in names:
        fp["entries"] = [*fp["entries"], NEW_ENTRY]
    fp["seeded"] = (
        "2026-07-30 nyiso-100 — UNION'd forward from the nyiso-99 keeper "
        "ledger (23 entries) and NOT rebuilt (a blind build_dof_ledger.py "
        "rebuild drops the curated measured/published entries — the failure "
        "mode the nyiso-81/87/89/92/96/98/99 notes all recorded). ONE new "
        "entry, and it records a REMOVAL: the mis-attributed 4,350 MW "
        "NYISO_simultaneous_import scalar is retired and NOTHING replaces "
        "it (the seam's aggregate bound becomes the sum of border-link TTCs "
        "already present, an emergent consequence of per-link posted "
        "ratings rather than a new constant). n_residual STAYS 6 — the arm "
        "adds zero free parameters and subtracts one unledgered constant. "
        "The retired scalar had NO ledger entry of its own, so this also "
        "closes a rule-24 [R-REGISTRY] gap."
    )
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"wrote {DEST.relative_to(REPO)} — {fp['n_entries']} DOF entries "
        f"({fp['n_residual']} residual-identified)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
