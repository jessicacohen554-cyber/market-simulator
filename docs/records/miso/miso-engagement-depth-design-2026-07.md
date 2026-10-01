# MISO engagement-depth lane — Midwest sub-regional reserve-holding family (frozen design)

**Date:** 2026-07-17. **Session:** `claude/miso-engagement-depth-phase-a-17mnb4`
(Fable, rule 27). **Parent contracts:**
`docs/handoffs/miso-f5-scarcity-depth-design-2026-07.md` §1e (the pre-named
engagement legs) + `docs/handoffs/miso-price-formation-design-2026-07.md`
(§2b re-read discipline, §7 non-relitigation) +
`docs/multi-iso/miso-scarcity-posture-design-2026-07.md` §B (the DATA-BLOCKED
Midwest family this lane un-blocks). **Run number: miso-71.** This document is
the Phase-A freeze: the mechanism, every parameter with its citation, the
leg-(b) adjudication, the composition plan, the pre-registered expected-delta
bands, and the refutation criteria are committed HERE, before any build or
solve. Nothing below is tuned to a residual; the one $ parameter is an
already-cited published value (`constants.MISO_RPE_DEMAND_VALUE`), and the
requirement series is the already-ledgered measured intake's Midwest leg.

## 0. State verified at session start (2026-07-17)

- MISO keeper = `2026-07-17-miso-70-tier-pricing` (PROMOTED by owner
  2026-07-17), NOT-YET, fail set {C1 CC_REGULAR-2023 −8.29 (±8.00),
  C3a-2025 −13.7%, C3c RT 1/30 · 6/37 · 1/88}; C3b PASS 0.079/0.124/0.184;
  DOF 24/2 (rubric v2.7) — matches the miso-71 charter exactly.
  `keepers.json["MISO"]` confirmed.
- The miso-70 branch (`claude/busy-bell-k7jkhf`) is merged to main
  (PR #2367); this session's branch starts from the current main
  (`bce929d`). (The local shallow clone's stale `origin/main` ref was
  reconciled against the live GitHub head — no real divergence.)
- Keeper recipe re-verified from `results/calibration/miso70_tier_pricing/
  run_config.json`: `energy_reserve_coopt` + `miso_zonal_reserves` (South) +
  `miso_reserve_pergen` + `miso_measured_reserve_requirements` +
  `unit_outage_maxgen_events` + `maxgen_emergency_tier_pricing` +
  `miso_rdt_tcdc` + `miso_rpe_pricing` + `miso_south_seam_split` all ON.
- RT actual tail (v2.7 gate basis): 30/37/88 hours > $200 for 2023/2024/2025;
  PASS bands [15,60] / [18.5,74] / [44,176].
- Box: ~15 GB → per-year + `--reuse-solved` orchestration mandatory
  (parent §8); years always sequential (rule 12).

## 1. The diagnosis — what "the stack carries slack at the real tail hours" measures

All numbers recomputed this session from the committed intakes
(`data/raw/MISO-AS/asm_{rtmcp_zonal,rt_cleared_mw}_<year>.parquet`) and the
archived primary documents (`data/raw/MISO/`), or quoted from registered run
records. No solve was run.

### 1a. What the deep windows look like in the keeper

With the measured 7.41–10.67 GW event-window derates armed (M-2) and tier
pricing adopted, the deep 2025 declared windows still peak $142–197 in-model
vs actual RT tails of $327–1,202 (Jun-23 EEA1: model max $196.7 vs RT
$1,046.7; Jun-24 Warning: $84.1 vs $1,202.1; Jul-29 Warning: $142.3 vs
$367.3). **Zero tier slack was dispatched in all of 2025** — the $500 floor
caps declared-window formation but never engages, because the model's Midwest
stack clears every window hour below the floor.

### 1b. The measured reserve-price record (what reality did and did not do)

- **Per-reserve-zone separation NEVER occurred.** Across all 26,280 hours of
  2023–2025, the RT zonal reserve MCPs (`asm_rtmcp_zonal`, GENSPIN/GENSUPP,
  Zones 1–8) show ZERO zone-separated hours in 2023 and 2024 and two hours at
  a $0.01 spread in 2025 (max spread $0.01). The published per-zone Zonal
  ORDC (BPM-002 §5.2.1.2, $200/$1,100/$3,300) never bound anywhere in the
  scored window. Any Midwest mechanism priced at those per-zone steps would
  be structure the measured record refutes (rule 1: never reach the number
  through a mechanism that isn't real).
- **Market-wide RT reserve prices DID spike, market-uniform, in exactly two
  of the five windows:** max RT GENSPINMCP Jun-23/24-2025 **$302.2**;
  Jul-28/29-2025 **$1,097.2** (the 40-minute OR shortage averaged into its
  HE); Aug-26-2024 **$7.8** (a pure tier-pricing event — reserves never
  scarce, exactly the miso-70 adjudication); Jan-14-17-2024 **$3.1** (the
  winter tail is NOT a reserve event — leg (c)'s separation is measured);
  Aug-24-2023 $89.3.
- The miso-56 adjudication stands and BOUNDS this lane: measured DA reserve
  MCPs never reach the published RDC steps in 2023–24 (spin/supp max
  $25–27) and once in 2025 ($132); the IMM records **"no operating reserve
  shortages"** on Jun-23/24-2025 (ELMP ex-post emergency repricing, an
  RT-only construct, priced those days). **This lane must not make the
  reserve curves fire; it must not fabricate scarcity the measured market
  does not have.**

### 1c. The phantom-slack anatomy (leg (a)'s structural claim)

The 2025 SOM (p.14): on Jun-23-2025 "MISO declared an EEA1 in the Midwest to
access emergency capacity **because constraints trapped over 4 GW of
generation in the South**"; 565 MW of emergency energy was dispatched in the
Midwest. The real Midwest/South separation instrument is the RDT plus the
sub-regional reserve constructs over it: "MISO's 30-minute reserve product
(short-term reserves or 'STR') satisfies market-wide **and sub-regional**
requirements. MISO enforces the subregional STR requirements through reserve
procurement enhancement (RPE) constraints over the Regional Directional
Transfer (RDT) constraint. The RPE binds when headroom on the RDT plus
available STR in the importing subregion is limited" (2025 SOM p.8; same
construct 2024 SOM §II.E). When RDT and RPE bind/violate together, "prices
throughout the Midwest reflect the shadow prices of the RDT and RPE
constraints … up to $700 per MWh" (2025 SOM pp.8-9).

In the model, the market-wide RBDC family is **congestion-blind by
construction** (`zone_mask = all ones`): its measured hourly requirement can
be satisfied by reserve parked ANYWHERE — including the RDT-trapped South
surplus, which is exactly where a cost-minimizing LP parks it in a Midwest
event (South headroom is cheap precisely because it is trapped). The South
zonal family holds only the measured ~0.3–0.5 GW South reservation; **the
five Midwest zones carry no locational reserve requirement at all.** So at
the Jun-23-2025 peak the model can (i) park the market-wide requirement in
the South and (ii) convert every Midwest MW of headroom to energy — reality
could do neither, and held ~1.0–2.5 GW of OR in the Midwest through the
whole window (measured, §2b). The keeper's own DOF ledger already records
this one-sidedly: the RPE's STR-scarcity binding channel ("RPE Only" — binds
with NO RDT violation when importing-subregion reserve is limited) "is
unrepresented because the LP carries no STR product, so separation
under-shoots" (`miso_rpe_pricing` ledger entry). **Leg (a) closes exactly
that ledgered gap, with a measured quantity and a published demand value.**

The engagement mechanism is therefore ENERGY-SIDE, not curve-side: forcing
the measured Midwest reserve holding to sit IN the Midwest removes ~2 GW of
phantom peak supply in exactly the event hours (composing with M-2's
measured derates), so the Midwest energy balance can finally need the tier
supply the F5 lane built — and prints the documented $500/$1,000 formation.
The reserve-price footprint stays ≈ measured (near-zero scarcity) by
construction, because the requirement is the revealed holding itself
(feasible in reality, including its event-hour dips).

### 1d. What is out of representation (adjudicated honestly, per the charter)

- **Jul-28-2025 RT $3,100:** a 40-minute OR shortage caused by "significant
  load and renewable forecast errors" plus a 500 kV forced outage stranding
  1.8 GW in the South (2025 SOM p.15). Forecast-error + sub-hourly + a
  transmission contingency: three layers outside a deterministic
  perfect-foresight hourly LP. The Jul-28 window is Alert-only (no tier
  floor). This hour-family is OUT of admissible representation; no mechanism
  in this lane targets it, and C3c-2025 bands are set accordingly.
- **2023's 30 RT tail hours** (all isolated 1-hour transients, DA median
  $40) and ~95% of 2024's RT tail: sub-hourly/forecast-error, per the
  standing miso-39/scarcity-tail-diagnosis adjudication.
- **The perfect commitment posture** (the LP's free part-load/re-time relief
  that undercut the reserve curves in miso-38/39) remains unrepresented: §A
  of the scarcity-posture design was honesty-gate REJECTED (miso-43, holds
  3.7–4.2× measured online reserves) and is NOT re-opened here. Inside
  declared windows M-2's measured derates substitute for it; outside them
  this lane adds nothing.

## 2. Leg (a) — the frozen mechanism: `miso_midwest_subregional_reserves` (ScenarioConfig bool, tier 3, default OFF)

### 2a. Design decisions with their evidence (design questions 1 and 3 of the charter)

| question | decision | grounds |
|---|---|---|
| published basis | **sub-regional (Midwest/South) reserve construct**, NOT per-Reserve-Zone | the per-zone Zonal ORDC never separated in 26,280 measured hours (§1b); Reserve Zones are redrawn quarterly (BPM-002 §3.3) with no stable crosswalk to 5 model zones; the ASM cleared report's own grain is the three operating regions (North/Central/South); the SOM's separation narrative (trapped-South, RPE) is sub-regional |
| zone crosswalk | Midwest = the 5 physical Midwest model zones (`MISO-West`, `MISO-Plains`, `MISO-Illinois`, `MISO-Indiana`, `MISO-East`); ASM regions North+Central = Midwest, South = South | the RDT is the only represented (and the only measured-binding) internal reserve-deliverability boundary; external seam buses are excluded by construction (the F5 external-bus amendment precedent) |
| §5.2.1.2 curve per-zone or per-region? | **per-zone — and therefore NOT used here.** The Midwest family prices shortfall at a single step = `MISO_RPE_DEMAND_VALUE` ($200/MWh, 2024 SOM §III.B — the published demand value of the sub-regional reserve-deliverability constraint) | applying the per-zone ORDC steps to a region would put deep steps ($1,100/$3,300) on a construct whose measured zonal expression never fired (§1b); the RPE $200 is the published price of exactly the sub-regional construct being represented; conservative single-step under-shoots deep shortage — the repo's standing convention (RDT 92% default derate, RPE conservatism notes) |
| requirement basis | **measured hourly Midwest revealed OR holding** = cleared reg+spin+supp summed over regions {North, Central} (`asm_rt_cleared_mw_<year>.parquet`) — the Midwest leg of the SAME miso-56 measured-cleared construction the keeper already applies market-wide and South | rule 14 (measured preferred); identical provenance, clock, and admissibility as the two ledgered series; scarcity-posture §B's data-block is thereby lifted by data that landed AFTER the block was written (miso-56, 2026-07-11) — §B was never re-visited |
| fallback / forward story | flag off or forecast mode: within-region MSSC (`largest_single_contingency_mw` masked to the 5 Midwest zones) — the same static basis the South family falls back to | forward-reproducible, fleet-responsive (rule 13); the mechanism is NOT backcast-only |
| nesting | `reserve_class = 0` (shared with the market-wide and South families): a Midwest reserve MW counts toward Midwest AND market-wide — the NYISO East ⊂ NYCA nested template; Midwest and South masks are disjoint | BPM-002 zonal minimums nest inside the market-wide requirement; note: measured Midwest + measured South = measured market by construction, so the market family becomes implied-slack when both sub-families hold — recorded, not a defect (the market family stays, costless) |
| fitted scalars | **zero** | the $200 is an existing cited constant; the series is measured; the zone list is topology |

### 2b. The measured quantity (recomputed this session; the loader table Phase B must reproduce)

Annual mean cleared OR (reg+spin+supp), MW:

| region | 2023 | 2024 | 2025 |
|---|---|---|---|
| Midwest (N+C) | 2,126 | 2,190 | 2,165 |
| South | 321 | 366 | 477 |

Event-window Midwest series (mean / min / max, MW): Jun-23/24-2025
**1,862 / 957 / 2,467**; Jul-28/29-2025 **1,941 / 851 / 2,485**; Aug-26-2024
2,077 / 1,525 / 2,429; Jan-14-17-2024 2,060 / 1,711 / 2,633; Aug-24-2023
2,253 / 2,004 / 2,416. The deep-window dips (957/851 vs ~2,165 mean) are the
leg-(b) limitation, quantified — see §3.

### 2c. What the mechanism deliberately does NOT do

- **It does not make reserve curves fire.** Expected reserve-price footprint:
  family dual ≈ re-dispatch opportunity cost (≤ ~$25, the measured DA
  scarcity bound) in almost every hour; genuine shortfalls (dual = $200)
  only where the model fleet, thinned by the measured M-2 derates, cannot
  hold the measured requirement — rare by construction since the requirement
  is the revealed (feasible) holding. This honors the miso-56 adjudication
  verbatim.
- No RBDC/zonal-ORDC curve edit, no VOLL/ORDC constant change pre-9/30/2025,
  no post-solve overlay, no new congestion mechanism (separation is earned
  through the EXISTING RDT/TCDC/RPE machinery when reserve holding adds S→N
  pull), no STR product build, no per-zone families, no window scoping (the
  family fires whenever requirement + deliverability bind — its driver is a
  standing market construct, not a declared-window overlay; the D-4-style
  off-driver watch is band R2/R3 below).
- No touch to the South family or the market-wide family (rule 19: one new
  mechanism; the existing families keep their adjudicated bases).

### 2d. Rule-12 triple and DOF

*Driver* = MISO's published sub-regional reserve-deliverability construct
(STR/RPE over the RDT — 2025 SOM p.8, 2024 SOM §II.E/III.B) + the measured
revealed Midwest OR holding (the miso-56 intake's North+Central leg).
*Window* = none needed (standing constraint); the fabricated-scarcity
refutation R2 and the Jan-2024 red flag R3 are the off-driver guards.
*Forward story* = within-region MSSC basis regenerates for any forecast
fleet; the measured series regenerates from each new ASM vintage (rule 23).
DOF: **+1 measured-physical entry** (the Midwest sub-regional family:
measured N+C series + published $200 demand value; zero new scalars) →
expected main 25/2, base 24/2.

## 3. Leg (b) — adjudicated: NO admissible requirement-side series exists; ledgered caveat (the NYISO B1 precedent)

Facts established this session:

1. **MISO publishes no historical reserve-requirement series** at any grain.
   Verified three ways: the module-docstring record (miso-56) stands;
   candidate market-report names probed on `docs.misoenergy.org` all 404
   (`*_or_req`, `*_str_req`, `*_asm_requirements`, …); BPM-002 describes
   daily zonal-requirement determination with no historical posting. The
   scarcity-posture §B data ask (2026-07-06) remains unfilled on the
   requirement side.
2. **The raised-STR instruments are real but inadmissible as a requirement
   basis:** +900 MW STR Aug 21-25-2023 (2023 SOM), raised DA/RT STR for
   Winter Storm Enzo Jan-2025 (2025 SOM p.iii), dynamic STR adjustment since
   2024 (2025 SOM p.8). STR is a 30-minute product the LP does not carry and
   the OR construct deliberately excludes (`OR_PRODUCTS`); no hourly series
   of the raised values is published; grafting event-scoped +MW onto the OR
   requirement would be a hand-sized, one-window patch of a different
   product's requirement (rules 1/13 — refused).
3. **Cleared < requirement in exactly the tail hours, now quantified:** the
   Midwest cleared series dips to 957 MW (Jun-23/24-2025) and 851 MW
   (Jul-28/29-2025) against a ~2,165 MW mean. Any construction that undoes
   the dip (trailing-max smoothing, window-scoped floors, "requirement =
   cleared except in events") is residual-fitting around a shortage and is
   refused by name.
4. **New recorded fact (basis family, not a requirement):** MISO DOES
   publish a DA cleared-offers report (`YYYYMMDD_asm_da_co.zip`, per-unit
   hourly RegMW/SpinMW/SuppMW/STRMW + MCPs by region, EST) — the
   miso-56 module docstring's caveat 2 ("the day-ahead scheduled-reserve
   series is not published at hourly grain") is stale. A DA-basis intake is
   a possible future refinement OF THE SAME cleared-basis family; switching
   the adopted RT basis is out of this lane's scope (it would re-litigate
   miso-56 and change all three families at once).

**Adjudication:** the engagement results of the Midwest family are LOWER
BOUNDS — in genuine-shortage intervals the requirement input understates
reality (point 3), for the market-wide and South families exactly as for the
new Midwest one. This is recorded as a ledgered measured-input caveat in the
run's attestation and the DOF ledger entry (the NYISO B1 precedent), not
"fixed" by any construction. Nothing is built for leg (b).

## 4. Composition & sequencing (one mechanism; the F2 lesson)

**The deciding probe is ONE new mechanism on the promoted keeper recipe:**
miso-70 keeper stack (M-2 + tier + measured requirements + South family +
pergen, all already armed) + `miso_midwest_subregional_reserves=True`,
against a same-box unchanged-keeper-recipe base replica. Probe script
`scripts/probes/_miso71_midwest_reserves.py` on the `_miso70_tier_pricing.py`
pattern (strict miso-70 `meta.json` replay via `replay_keeper.build_kwargs`;
the flag through `prb_overrides`; per-year + `--reuse-solved`; years
sequential; main and base back to back). **The base sanity checks are
updated to REQUIRE `unit_outage_maxgen_events` and
`maxgen_emergency_tier_pricing` in the base recipe** (they are keeper
structure now — the miso-70 pattern's checks rejected them).

Pre-reads, in order, BEFORE any verdict is read:

1. **Loader table:** the Midwest series' annual means and the five window
   rows printed and compared to §2b (byte-level intake check).
2. **Phantom-parking read (base run, solved first):** the base's regional
   reserve allocation in the Jun-23/24-2025 and Jul-29-2025 window hours —
   the share of the market-wide requirement held in MISO-South. EXPECTED:
   material South parking (this is the mechanism's premise). **Pre-declared
   inertness exit:** if the base already holds ≥ the measured Midwest
   requirement in the Midwest zones in EVERY deep-window hour, the family is
   provably inert on its target set — the main arm is NOT solved, the base
   registers (rule 15) as the record with an inertness log entry
   (ERCOT-64/75 no-build precedent), and the lane closes per R4.
3. In-window LMP ceiling check (inherited invariant): every Warning+/Step
   window-hour zonal LMP ≤ its tier floor + $1, both arms.

## 5. Pre-registered expected-delta bands (committed BEFORE the probe)

All mechanism-only reads are miso-71-main − miso-71-base (same box). C3b is
the monthly load-weighted NRMSE, so band arithmetic is monthly-mean-based:
the deep-2025 windows sit in months the model undershoots by $16.6/$18.1
(Jun/Jul), so RIGHT-SHAPED engagement (up to ~2 dozen $500-capped hours per
month, in the actual event windows) IMPROVES C3b-2025; the risks are
overshoot breadth and off-window prints.

| read | band | notes |
|---|---|---|
| C3b-2025 | **≤ 0.20 ABSOLUTE (standing veto; keeper 0.184, headroom 0.016)**; expected [0.160, 0.195] | the decisive risk read; in-window June/July engagement is toward-actual by monthly arithmetic |
| C3b-2024 | ≤ 0.20; expected [0.118, 0.135] (keeper 0.124) | family adds at most ~1 more $500-capped hour inside the 7-hour Aug-26 window; Jan-2024 MUST be untouched (R3) |
| C3b-2023 | expected [0.077, 0.105] (keeper 0.079) | upside risk = Aug-24 Step-2A prints at the $1,000 floor vs actual ~$205-219 peak; a few such hours move August-2023 wrong-shaped — watch, veto-protected |
| C3c-2025 (RT actual 88h, PASS [44,176]) | honesty band **[1, 26]** | gains confined to declared-window hours + measured-RT-scarce hours; the PASS band is NOT claimed — the Jul-28 40-min transient family and the isolated RT singles are out of representation (§1d); landing in-band is NOT tail skill (R5) |
| C3c-2024 (37h, [18.5,74]) | [4, 12] | keeper 6; window-confined; any Jan-14-17 gain triggers R3 scrutiny, not credit |
| C3c-2023 (30h, [15,60]) | [1, 6] | keeper 1 |
| C3a-2025 | [−14.5%, −10.0%], direction UP from −13.7% | Jun/Jul monthly gaps close partially; PASS (±10) NOT claimed from this leg alone |
| C3a-2024 | [−8.5%, −5.0%], PASS both arms (keeper −6.9%) | |
| C3a-2023 | −0.9% ± 1.0 watch | |
| C1 CC_REGULAR-2023 | −8.3 ± 0.15 (unchanged watch) | not this lane's lever |
| C2 / C4 / C5a | PASS both arms; C5a within ±7 | reserve holding displaces energy within-region; class energy moves ≤ 0.5 TWh watch |
| C7 / C8 | PASS, same ST_GAS grounded-above-budget notes; NO new floors | the family carries no floor-mechanism id (a reserve requirement, not a min_gen) |
| reserve-price fidelity (the miso-56-honoring read) | family dual ≤ $25 in ≥ 99% of hours; dual ≥ $200 in ≤ 20 h/yr, ALL inside declared windows or measured-RT-scarce hours (≈4/11/19 h) | breach = R2 (fabricated scarcity) |
| RDT S→N | binding hours ≥ base (added separation through existing machinery); flows may differ any hour (a standing constraint, not a window overlay) | |
| in-window LMP ceiling | ≤ tier floor + $1, both arms | implementation invariant |
| DOF | main 25/2, base 24/2 | +1 measured-physical (§2d) |

## 6. Refutation criteria (what kills what, pre-declared)

1. **R1 — C3b any year > 0.20 composed** → REFUTED (the family's engagement
   is wrong-shaped or too broad). Register as REJECTED PROBE; lane pauses
   for the owner. No guard/width/step retuning against the shape residual.
2. **R2 — fabricated scarcity:** family dual ≥ $200 in > 20 h/yr outside
   (declared windows ∪ measured-RT-scarce hours) → REFUTED per the miso-56
   adjudication, whatever it does to C3c. Register as rejected probe.
3. **R3 — wrong-driver engagement:** family dual > $50 in any Jan-14-17-2024
   tail hour (measured reserve MCPs there: ~$3) → those hours are excluded
   from any claimed gain and the finding escalates to the winter-2024
   fuel-security lane; if Jan engagement is material (> 5 h), the run is a
   rejected probe (the family is binding where its own driver evidence says
   the phenomenon was fuel/congestion, rule 12's off-window analogue).
4. **R4 — inertness at current depth:** the §4.2 pre-read shows the base
   already holds the measured Midwest requirement through the deep windows,
   OR main − base is byte-comparable with family duals ≈ 0 everywhere → the
   reserve-parking hypothesis is refuted AT CURRENT DEPTH; the remaining
   C3c-2025 gap is ledgered as out-of-representation (sub-hourly transients
   + the rejected §A commitment posture), and **nothing further is armed in
   this lane** — closing honestly is the deliverable (the F5 lesson).
5. **R5 — honesty:** C3c-2025 landing inside [1,26] must not be quoted as
   tail skill; the [44,176] RT PASS band was never claimed. Equally, the
   miso-70 precedent applies: bands here are honesty bands.
6. **Keeper candidacy** is separate from design survival: if R1–R3 hold and
   no gated criterion regresses PASS→FAIL, the composed stack is
   structurally superior (a ledgered under-shoot closed with measured +
   published inputs at zero fitted scalars) and a rule-1 keeper
   recommendation goes to the owner whatever the MAE does. Swap owner-only.

## 7. Implementation freeze (files, seams, tests — Phase B executes verbatim)

1. `src/market_sim/config/reserve_config.py`: `MISO_MIDWEST_ZONES:
   tuple[str, ...] = ("MISO-West", "MISO-Plains", "MISO-Illinois",
   "MISO-Indiana", "MISO-East")` (physical zones only — external seam buses
   excluded by construction, F5 precedent) with the §2a citation block; a
   `_miso_design` branch gated on
   `getattr(config, "miso_midwest_subregional_reserves", False)`: zone_mask
   over the 5 names (error on a missing name), requirement =
   `measured_req["MISO-Midwest"]` when the measured flag is on, else the
   within-region MSSC (same `largest_single_contingency_mw`, masked to the
   region), single shortfall step `[(1.0, MISO_RPE_DEMAND_VALUE)]`
   width-anchored at `max(requirement)` (South-family feasibility
   convention), `reserve_class=0`, family name
   `"miso_subregional_or_midwest"`. Import `MISO_RPE_DEMAND_VALUE` from
   `config.constants` — no new constant, no inlined number.
2. `src/market_sim/data/miso_reserve_requirements.py`: emit a
   `"MISO-Midwest"` key = cleared sum over regions {North, Central}
   (constant `MIDWEST_REGIONS = ("North", "Central")`); docstring updated:
   the Midwest leg, the quantified dip caveat (§3.3), and the corrected DA
   caveat (§3.4 — `asm_da_co.zip` exists; RT basis retained as adopted).
3. `src/market_sim/config/scenarios.py`:
   `miso_midwest_subregional_reserves: bool = False` beside
   `miso_zonal_reserves` with the full driver/window/forward-story comment;
   tier-3 entry in the gated-fields registry.
4. `scripts/run_calibration.py`: CLI flag
   `--miso-midwest-subregional-reserves` wired exactly like
   `--miso-zonal-reserves` (config override only; the co-opt chain already
   routes `_miso_design`).
5. Tests (trivial case first, rule "1 gen, 1 zone, 24 h"):
   `tests/test_reserve_config.py::TestMisoMidwestDesign` — family present
   iff flag on; mask = exactly the 5 zones (external buses and South
   excluded); measured basis consumes the loader key; fallback MSSC when
   measured off; single $200 step, width = series max; `reserve_class` 0.
   `tests/test_reserve_coopt.py::TestMisoMidwestReserveLP` — a Midwest-short
   / South-surplus toy LP prices the Midwest family at $200 while the
   market-wide family stays cleared (nesting: a Midwest MW counts toward
   both); off-state byte identity of the LP matrices.
   `tests/test_miso_reserve_requirements.py`: the Midwest key sums N+C and
   aligns to the existing clock conventions.
6. `scripts/probes/_miso71_midwest_reserves.py` per §4 (miso-70 meta strict
   replay; base sanity REQUIRES the two maxgen flags; rule-22 year guard
   2023/2024/2025 only; the pre-reads of §4 printed before any verdict).
7. Legitimacy/registration: no new floor-mechanism id (verify D-2/D-4 regen
   carries no new rows); DOF ledger +1 entry per §2d with the leg-(b)
   caveat text; attestation via the `gen_miso70_attestation.py` pattern.
   Labels ≤ 4 non-stopword words: **"miso 71 midwest"** (main) /
   **"miso 71 midwest base"** (base). Registration chain per parent §6.7
   for BOTH runs whatever the verdict (rule 15), keeper recommendation to
   the owner, no `keepers.json` edit.

## 8. Non-relitigation (inherited + this session)

Parent §7 in full; the miso-70 adjudications (tier mechanism ADOPTED with
its scoping settled; tier-alone inertness proven; miso-69's M-2 rejection
superseded by the composed adoption; C3b-2024 CLOSED at 0.124; the 1/6/1 vs
[0,3]/[4,10]/[1,8] results are honesty-band hits, not tail skill; the
D-4/D-5 price-side registry pattern settled). Plus, adjudicated THIS session
from the measured record:

- **miso-56's "0 binding DA RDC hours is CORRECT" stands** — this lane's
  family is scoped so its expected reserve-price footprint matches the
  measured near-zero scarcity (R2 enforces it). No mechanism that works by
  making the published curves fire may be proposed on this lane's residual.
- **Per-Reserve-Zone families are measured-refuted** for 2023–2025 (the
  26,280-hour zonal-MCP uniformity check, §1b) — do not re-open per-zone
  grain, including for the existing South family.
- **The Jul-28-2025 $3,100 forty-minute transient is out of admissible
  representation** (forecast error + sub-hourly + a 500 kV contingency,
  2025 SOM p.15); it is measured context, never a target.
- **§A commitment posture stays rejected** (miso-43 honesty gate); this lane
  does not substitute for it outside declared windows and must not be
  extended toward it on a residual.
- **The winter-2024 tail is measured NOT-a-reserve-event** (reserve MCPs
  ~$3, §1b) — leg (c) stays its own chartered lane (fuel security /
  `gas_daily_shape` / seam family, rule-19-reconciled there, not here).
- **G-23 imports stay LAST** (adds supply, pulls C3a-2025 the wrong way).
- **No basis switch for the existing families** (RT cleared stays the
  adopted basis; the `asm_da_co` discovery is a recorded future-intake
  option, not an invitation).

## 9. Environmental constraints (verified this session)

- Box ~15 GB: per-year + `--reuse-solved`, one fresh python process per
  year, years ALWAYS sequential (rule 12); main and base back to back. The
  new family adds one constraint row-family (T rows) — negligible against
  the ~15.9 GB co-opt peak; keep `MALLOC_ARENA_MAX=1
  MARKET_SIM_HIGHS_THREADS=1`.
- Push: `git push -u origin <branch>` through the session git gateway worked
  this session; verify every push by fetch-back SHA compare (rule 27).
  Never commit the per-year accumulator dirs (`_<run>_acc/`, gitignored).
- `misoenergy.org` is proxy-403 from this box; `docs.misoenergy.org`
  (market reports) is reachable — the loader-side data is already on disk,
  so Phase B needs no new fetch.

---

## Phase-B handoff prompt (copy-paste for the build session)

```
MODEL: Opus or Fable (CLAUDE.md rule 27 — this lane writes core infrastructure;
never Sonnet). PHASE B of the MISO engagement-depth lane — execute the FROZEN
contract in docs/handoffs/miso-engagement-depth-design-2026-07.md (Fable
Phase A, 2026-07-17) VERBATIM. That doc pre-declares the mechanism
(miso_midwest_subregional_reserves — the Midwest sub-regional reserve-holding
family: measured N+C cleared OR requirement, published $200 RPE demand value,
5 physical Midwest zones, reserve_class 0 nested), every parameter with its
citation, the pre-reads, the expected-delta bands, and the refutation criteria
R1-R6 — do not redesign, do not add mechanisms, do not tune any value against
a residual (rules 1/11/13). Run number: miso-71. Deliverable = registered runs
on the backcast dashboard + a keeper recommendation (rule 15; keeper swap
owner-only).

# Verify first (STOP and reconcile with docs/calibration-log.md on any mismatch)
- git fetch origin main; read CLAUDE.md end-to-end; read the design doc
  end-to-end plus its parents (miso-f5-scarcity-depth-design-2026-07.md,
  miso-price-formation-design-2026-07.md, miso-scarcity-posture-design §B,
  miso-scarcity-tail-diagnosis.md).
- PYTHONPATH=.:src .venv/bin/python scripts/calibration_verdict.py \
    2026-07-17-miso-70-tier-pricing
  Expect: NOT-YET; FAIL {C1 CC_REGULAR-2023 −8.29, C3a-2025 −13.7%, C3c RT
  1/30 · 6/37 · 1/88}; C3b PASS 0.079/0.124/0.184; DOF 24/2. Confirm
  keepers.json["MISO"] = 2026-07-17-miso-70-tier-pricing. If the keeper moved,
  STOP and reconcile before executing anything.
- RAM: read MemAvailable. ≤~16 GB → per-year + reuse orchestration
  (scripts/probes/_miso70_tier_pricing.py pattern incl. prb_overrides), years
  ALWAYS sequential, main/base back to back. Never offload a solve to CI.
- Push: git push -u origin <branch> worked 2026-07-17; verify every push by
  fetch-back SHA compare (rule 27). Never commit _<run>_acc/ dirs.

# Guardrails (absolute)
- Rule 22: MISO has NO calibration-complete marker — solve 2023/2024/2025
  ONLY, all three in ONE bundle (rule 16); never a single-year keeper.
- C3b ≤ 0.20 absolute is the standing shape veto (2025 headroom 0.016).
- The design's R1-R6 are the ONLY fallbacks; never invent one after reading a
  probe. R2 (fabricated scarcity) and R3 (Jan-2024 wrong-driver) are read
  from the solved reserve duals BEFORE celebrating any C3c gain.
- No RBDC/zonal-ORDC curve edit; no VOLL/ORDC constant change pre-9/30/2025;
  no post-solve MISO scarcity overlay; no new congestion mechanism; no STR
  product; no per-zone reserve families; no basis switch for existing
  families; no G-23 import work; design doc §8 non-relitigation in full.

# Ordered execution
1. Implement design §7 items 1-5 (reserve_config Midwest branch + constant
   tuple; loader "MISO-Midwest" key; ScenarioConfig tier-3 bool; CLI flag;
   unit tests trivial-case-first). Run the new tests + existing reserve
   config/coopt/requirement test files.
2. Analytical pre-checks (no solve): loader table vs design §2b (annual
   means 2,126/2,190/2,165 Midwest; window rows incl. the 957/851 dips).
3. Probe scripts/probes/_miso71_midwest_reserves.py on the _miso70 pattern
   (strict miso-70 meta.json replay; main adds
   miso_midwest_subregional_reserves=True via prb_overrides; base adds
   nothing; base sanity checks REQUIRE unit_outage_maxgen_events AND
   maxgen_emergency_tier_pricing in the base recipe). Solve BASE first,
   per-year + --reuse-solved, years sequential. Run the §4.2 phantom-parking
   pre-read on the base: if the base already holds ≥ the measured Midwest
   requirement in the Midwest zones in EVERY deep-window hour, the main arm
   is provably inert — do NOT solve it; register the base with an inertness
   log entry and close the lane per R4.
4. Otherwise solve MAIN; reads in design §5's order: C3b-2025 (veto) →
   reserve-price fidelity (R2) + Jan-2024 duals (R3) → in-window LMP ceiling
   → C3c per year → C3a → C1/C2/C4/C5a watches → C7/C8 + D-1/D-2/D-4 regen →
   RDT anchors → DOF (25/2, 24/2).
5. Registration chain per the parent §6.7 for BOTH runs whatever the verdict
   (rule 15): dashboard_add_run (labels "miso 71 midwest" / "miso 71 midwest
   base" — ≤4 non-stopword words, the miso-70 slug-collision lesson) →
   attestation/DOF ledger (gen_miso70_attestation.py pattern; the leg-(b)
   ledgered caveat text from design §3) → legitimacy regen → calibration_
   verdict --write-metrics → parity → build_manifest → calibration-log entry
   (lead with the dashboard result) → push with fetch-back verification.
   Keeper recommendation per R6; no keepers.json edit. Honour
   top-15-per-ISO retention.
6. /sync-docs at end of session (miso-reserve-coopt.md gains the Midwest
   family section; scarcity-posture §B marked un-blocked/executed).

# Pre-registered bands (the probe decides; a miss triggers the matching
# refutation criterion, never a retune) — design §5 verbatim:
- C3b: 2025 ≤ 0.20 ABSOLUTE, expect [0.160,0.195]; 2024 [0.118,0.135];
  2023 [0.077,0.105].
- C3c RT-basis: 2025 [1,26] (PASS [44,176] NOT claimed); 2024 [4,12];
  2023 [1,6]. In-window/measured-scarce hours only (R2/R3 police this).
- C3a-2025 [−14.5,−10.0] direction up; C3a-2024 [−8.5,−5.0] PASS.
- C1 CC_REGULAR-2023 −8.3±0.15 watch; C2/C4/C5a PASS both arms (C5a ±7);
  class energy ≤0.5 TWh; C7/C8 PASS, no new floors.
- Reserve fidelity: family dual ≤$25 in ≥99% of hours; ≥$200 in ≤20 h/yr,
  all inside declared windows or measured-RT-scarce hours.
- In-window LMP ≤ tier floor + $1 both arms. DOF 25/2 main, 24/2 base.
```
