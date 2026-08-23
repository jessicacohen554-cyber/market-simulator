# FINDING — caiso-217: THE FUNDED caiso-216 PACKET EXECUTED — the measured generator-hub-membership crosswalk landed fleet-wide (Ask 1) and the one funded 3-year solve run on the exact caiso-200 keeper recipe + the crosswalk (Ask 2), scored under the §G pre-registered gate table (2026-08-23)

**Authority:** owner, 2026-08-23 (verbatim: "Is this a recommended keeper
candidate? If so plz promote. If structural integrity improves but gates
regress that may still be a keeper.. [...] give handoff prompt for a new
suggestion to continue work on calibration tuning for rubric failures") —
funding BOTH asks of FINDING-caiso216 §G and setting the promotion standard
(the ercot-221/caiso-200 structural-integrity pattern: disclosed gate
regressions do not bar a structurally-superior arm; disclose, never hide).
The caiso-201 rest is superseded for this chartered work only; the lever is
off-queue under the caiso-216 charter chain (queue EMPTY at caiso-200).

## §A — Phase A: the crosswalk intake (Ask 1), landed

**The deliverable:** `data/raw/reference/caiso-plant-hub-membership.csv` —
the measured CAISO plant → trading-hub membership crosswalk (446 plants,
41.1 GW = 43.6 % of member-fleet MW) — plus its JSON sidecar (per-tech
coverage, the §E witness gates, THE FULL MOVER TABLE as the committed review
surface), the frozen derive
`scripts/data/derive_caiso_plant_hub_membership.py` [R-FROZEN-DERIVE], the
`curate_reference` clean table (`reference/caiso-hub-membership`) with a
raw/clean parity test, and the `zone_assignment` CAISO FIRST-CHECK:
`load_caiso_hub_membership()` + `_caiso_zone_from_hub()` applied in BOTH
`build_zone_lookup` and `assign_zone` — measured membership overrides the
lat-cut/county-lift estimate wherever joined [R-ACCURATE]; unjoined plants
keep the geographic rule; a crosswalk row can only re-zone a plant already
in the population, never widen it. `TH_SP15` carries no sub-zone
information, so the LCR-pocket resolution (LA_BASIN / SDGE / SP15_rest) is
preserved from the geographic rule — no pocket membership moved.

**The construction** (all committed bytes; zero free parameters). Pnode →
hub from the committed `ATL_PNODE_MAP` at each pnode's LATEST effective
window (9 pnodes with a mid-history hub change, reported); substation → hub
only where every gen pnode at the substation agrees (caiso-172 tier-1 rule;
5 ambiguous substations dropped). Plants join through four evidence tiers,
highest wins, hub-unanimity enforced inside every tier:

| tier | evidence | joined (as best tier) |
|---|---|---|
| E0 `verified-pin` | 4 hand-verified name-pattern pins, basis stated inline (the dam-crosswalk "verified-prefix" precedent): Mustang/Westlands (MSTANG↔MUSTANGS), Big Creek (SCE, BIGCRK*), Edwards Sanborn (EDWARD), Abengoa Mojave Solar (LCKHT1) | 19 plants |
| E1 `eia-lmp-node` | EIA-860 Generator sheet's own "RTO/ISO LMP Node Designation" (operator-reported pnode; exact pnode id, else token) | 132 |
| E2 `reviewed-crosswalk` | the two committed reviewed thermal resource→EIA crosswalks | 21 |
| E3 `resource-name` | DAM outage corpus resource names (CAISO's own, fleet-wide, 1,548 resources) ↔ EIA plant names (token containment, roman-numeral + plural normalization, numeric agreement), then resource token → substation | 274 |

Token matching is a four-rule ladder (exact > GEN/GN-strip > prefix ≥5 >
unit-designator base ≥4), first rule wins, all hit substations must agree.
**Two looser channels were built, audited against geography, and REMOVED**
(precision outranks recall: a wrong hub actively mis-allocates across the
cuts, an unmatched plant merely keeps today's estimate): the de-voweled
token rule (CONTROL/CENTRAL, SANDLOT, SYCAMORE collisions — ~2 GW moved on
false matches in the audit run) and the bare compact-plant-name prefix tier
(Edward C Hyatt→EDWARDS AFB 644 MW, Diablo Energy Storage @ Pittsburg →
DIABLO 200 MW, Sierra Pacific * → SIERRA). Three adjudicated
name-collision false positives are per-plant EXCLUDED with stated bases
(James B Black→BLACKWLL, Mill Creek 3→LOWGAP, High Sierra→SIERRA), and
three substations are barred as evidence (GEN_BUS placeholder, CENT403
generic-word trap, FLOWD3-6 — FloWind's ids conflate its Altamont and
Tehachapi fleets, direction-ambiguous by construction).

**Witness gates (§E pre-registered): ALL PASS.** DIABLO→TH_ZP26,
TOPAZ→TH_ZP26, ALTA→TH_SP15, CVSR→TH_ZP26, MUSTANG→TH_NP15, and the
GATES/MIDWAY boundary anchors TH_ZP26.

**The movers — 78 plants / 10,561 MW** (the crosswalk's payload; full table
committed in the JSON sidecar):

| direction | MW | anatomy |
|---|---:|---|
| NP15 → TH_ZP26 | 3,167 | Diablo Canyon 2,323 + Topaz 586 + CVSR 250 (the §E county-lift cohort) |
| ZP26 → TH_SP15 | 5,532 | the Tehachapi/Kern-desert band (Alta I–XI, Bellefield 1,000, Rexford 540, Edwards Sanborn, Windstar/Voyager, Ivanpah 393, Silver State, Coso) + the SCE southern-Sierra foothill cluster (VESTAL/RECTOR/SPRINGVL — Porterville/Visalia/Isabella: the SCE/PG&E territory line, not lat 35, is the true electrical divide there) |
| ZP26 → TH_NP15 | 1,141 | the Westlands/Kings counter-direction (Mustang 325, Slate 440, American Kings 128, Henrietta, Five Points/SCHLNDLR cluster — coherent with caiso-172's load-side finding that Fresno sub-LAP is 71:3 NP15) |
| NP15 → TH_SP15 | 621 | SCE Big Creek hydro (electrically SP15 at lat 37.2 — the estimate's largest single north-side error after Diablo) |
| SP15_rest → TH_ZP26 | 100 | Strauss Wind (Lompoc — coastal PG&E south of lat 35) + SEPV Cuyama |

**Coverage, honestly** (target was ≥90 %; realized 43.6 % of MW): nuclear
100 %, battery 56 %, solar 49 %, gas_cc 38 %, wind 40 %, hydro 37 %,
geothermal/pumped-storage ~0 %. The binding ceiling is the atlas itself:
`ATL_PNODE_MAP` is a NETWORK-node membership list (1,999 gen pnodes,
suffixes `_N###`/`_B#`), and many plants' resource substations
(HELMPG/Helms, GEYS*/Geysers, ORMOND, LAPLMA, COLUSA…) have no
token-resolvable entry — 17.3 GW of the unjoined MW has a KNOWN resource
whose substation the hub list simply doesn't carry. Unjoined mass
overwhelmingly sits where geography is already right (the deep NP15 north,
the LA basin); what the join had to reach — and did — is the boundary
cohorts. §F.1g pre-authorized exactly this: "even a low-coverage join
proceeds to Phase B; the S1-Diablo floor alone is material."

## §B — The realized S1′/S2′ table (the caiso-216 Ask-1 probe re-run)

`scripts/probes/_caiso217_realized_membership.py` re-runs the committed
caiso-216 instrument with the crosswalk ACTIVE (fresh recon cache; output to
`_caiso217_realized_membership.json` so the caiso-216 pre-state record is
preserved). Controls: recon demand row-match to the keeper sidecar **0.000
MW in all 7 zones × 3 years** (the crosswalk moved generation only — the
load split is the separate caiso-172 ATL_LDF derivation) and the model's
endogenous spill is byte-identical pre/post (480/1,176/852 GWh — an
input-side identity).

Realized cut-15 L2 (renewables potential + nuclear + injected − demand),
against FINDING-caiso216 §B/§E:

| year | metric | PRE (caiso-216) | **REALIZED (caiso-217)** | 216's S1 / S2 bounds | reality split h |
|---|---|---:|---:|---:|---:|
| 2023 | s-neg mean MW | +1,101 | **+3,132** | — | |
| 2023 | h > 5,400 path | 17 | **121** | 122 / 342 | 1,310 |
| 2024 | s-neg mean MW | +2,288 | **+4,108** | — | |
| 2024 | h > 5,400 path | 234 | **480** | 487 / 742 | 1,691 |
| 2025 | s-neg mean MW | +3,370 | **+5,245** | — | |
| 2025 | h > 5,400 path | 289 | **742** | 739 / 1,143 | 1,347 |

The realized geometry lands ON the caiso-216 S1 floor in 2023 (121 ≈ 122)
and between S1 and S2 in 2024/25 — reality's order, reality's year-ordering,
with 2023 4–6× below 2024/25: exactly the 2023-safe asymmetry the caiso-215
envelope requires. The south-of-Path-26 (cut26) net position also moves
+1.3/+1.4/+1.6 GW (−1,640→−368 / −1,102→+316 / −550→+1,080 s-neg mean MW):
the Path-26 S→N rating becomes testable in 2024/25 for the first time.

## §C — Phase B: the funded solve (Ask 2)

One invocation, years sequential (rule 12), through the sanctioned
recipe-replay channel: `run_calibration_full.py --replay-bundle
results/calibration/caiso200_h1_memberpanel --out-dir
results/calibration/caiso217_crosswalk` — the bundle's `meta.json` IS the
config (every kwarg via `replay_keeper.build_kwargs`), so the recipe is the
keeper's byte-for-byte; **the crosswalk is the ONLY delta and enters as
data**, nothing armed or changed, P1 scored. (First launch failed CLEANLY on
the strict input-completeness guard — the fresh container's derived
`data/clean/capacity-deliverability/CAISO` partition was absent; regenerated
via its own curate script and relaunched. The guard working as designed,
caiso-188/157 lineage.)

<!-- PHASE B/C RESULTS FILLED AFTER THE SOLVE -->

## §D — Gates (§G pre-registered; scored, not judged, first)

<!-- gate table with realized numbers -->

## §E — Determination and promotion decision

<!-- verdict + owner-standard evaluation -->

## §F — Records (rule 28b — CAISO shard only)

<!-- matrix stamps, log entry, filed items carry -->
