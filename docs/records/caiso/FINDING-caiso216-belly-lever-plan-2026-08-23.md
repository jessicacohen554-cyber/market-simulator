# FINDING — caiso-216: the deferred Phase-0 measurement ANSWERS the lever class — the model's south-of-Path-15 **does** have a belly surplus (positive in 72–85 % of reality's south-negative hours, growing +1.1 → +2.3 → +3.4 GW mean 2023→25) but it is **under-allocated and invisibly absorbed**: the armed S→N directional ratings never bind (17/234/289 h over path vs reality's 1,310–1,691 split hours) because the lat-cut/county-lift zone estimate holds GW-scale zero-MC supply on the wrong side of both cuts — **CAISO's own ATL_PNODE_MAP puts DIABLO in TH_ZP26 (model: NP15), ALTA/WINDHUB Tehachapi in TH_SP15 (model: ZP26), TOPAZ in TH_ZP26 (model: NP15), MUSTANG in TH_NP15 (model: ZP26)** — and with the membership-measured re-allocation (input arithmetic, no LP) the bound-hour count reaches **742 h (2024) / 1,143 h (2025) vs 342 h (2023)**: reality's order, in reality's year-ordering, with 2023 3× smaller — the 2023-safe geometry the caiso-215 envelope requires. THE RANKED ASK: fund (1) the **measured generator-hub-membership crosswalk intake** (the caiso-172 program completed on the generation side; zero free parameters) and (2) **one 3-year solve** carrying it, under the pre-registered gate table. NO LP, NO SOLVE, NOTHING ARMED — committed bytes + the licensed fleet-only input assembly (2026-08-23)

**Keeper `2026-08-17-caiso-200-h1-memberpanel` UNCHANGED. No mechanism armed, no
`ScenarioConfig` field added or changed, no LP built, no solver called, nothing
registered, NO matrix cell verdict moved.** This session executes the owner's
2026-08-23 order ("I really really need you to address the 2025 overprice") as
the PLANNING continuation of the caiso-214 charter: caiso-215 answered WHERE
(the southern solar belly, split at Path 15); caiso-216 answers WHICH LEVER
CLASS and delivers the rule-13-vetted design packet with the explicit funding
ask. The lane's rested state (caiso-201 Q1) is undisturbed — this order is the
standing authority for planning only, and the in-model lever queue remains
EMPTY (exhausted at caiso-200): every candidate below is off-queue under this
charter, from new Phase-0 measurement, not a re-test of any adjudicated cell.

## THE ONE-SCREEN OWNER SUMMARY

* **Which lever class — allocation or price formation?** **Allocation first,
  and with it the price formation is already built.** The Phase-0 charter
  question ("does the model's south even have a belly surplus?") splits by
  cut: at **Path 26** the model's south3 (LA_BASIN+SDGE+SP15_rest) is NOT in
  surplus — its zero-MC+must-run stack sits 0.5–1.9 GW *short* through
  reality's south-negative hours in every year (§B) — so at that cut there is
  literally nothing to price. At **Path 15** (the cut caiso-215 measured
  reality splitting at, ZP26 pricing south) the surplus EXISTS — positive in
  493/688, 934/1,230, 821/964 of reality's south-negative hours (2023/24/25),
  mean +1.1/+2.3/+3.4 GW — but it exceeds the armed 5,400 MW S→N rating in
  only 17/234/289 h, so the LP exports it north unpriced and absorbs the rest
  in a storage fleet that never comes within 10 % of its power cap (§C). The
  binding defect upstream of both: the **zonal allocation estimate**. The
  lat-cut and county-lift place ≈2.1 GW of nuclear (Diablo), ≈1.3 GW of
  central-coast solar (Topaz + CVSR cohort), and the ≈3.0 GW Tehachapi wind +
  ≈1.0 GW ridge solar band on the NORTH side of cuts where CAISO's own
  generator-hub membership (`data/raw/caiso-atlas/ATL_PNODE_MAP.csv`,
  committed) prices them SOUTH — and the error is two-directional (MUSTANG in
  the Westlands band reads TH_NP15 where the lat-cut says ZP26), which is
  exactly why the fix is the measured membership crosswalk, not a boundary
  tweak (§E).
* **What is admissible?** The **fleet-wide measured hub-membership
  crosswalk** (candidate C1, §F.1): rule 13 PASS (a published physical/market
  registry, reproducible forward — a new plant's membership regenerates from
  its interconnection geography; zero free parameters, nothing tuned to any
  residual), rule 14 driven (replaces the documented lat/county ESTIMATE with
  CAISO's own data — the same `ATL_PNODE_MAP` authority the caiso-172 keeper
  already uses for the LOAD side, cell `path15_load_split` K). The caiso-215
  §F H2 mean-zero kill does NOT apply: the crosswalk moves physical supply
  across the cuts and changes the binding set — it is not a mean-preserving
  re-badging of a fixed price surface (§F.1c). What is NOT admissible, named:
  capping model flows at realized flows (outcome pin), the delivered-solar
  cap (`caiso_solar_cap_at_delivered`, self-labelled forbidden), any
  local-curtailment-share derate (wrong direction AND outcome-adjacent).
* **What funding is asked?** (i) **The crosswalk intake session** — build the
  EIA-860/eGRID-plant → pnode → trading-hub join over the committed atlas
  (name-fragment feasibility verified on every witness tried, §E), land it as
  a reference CSV + a zone-assignment seam with coverage reporting (the
  ERCOT `custom-bin-assignments.csv` pattern); no solve. (ii) **One 3-year
  solve** of the keeper recipe + crosswalk under §G's pre-registered gate
  table. (iii) Two contingencies, pre-fenced and NOT asked now: the
  internal-path published-operating-limit intake, and the measured export
  sink — each conditional on the funded solve's own gate evidence (§F.3).
  If the owner funds nothing, NOT-YET stands and the residual attribution
  tightens from caiso-215's "south surplus-pricing regime (model-class)" to:
  **south surplus mis-allocated by an estimate CAISO's own data can replace**.

Instruments (committed, no LP, no solve):

* `scripts/probes/_caiso216_belly_surplus.py` — §A–§E (stdout sections
  B0–B6). The only reconstruction is the licensed caiso-105/131
  `run_year(fleet_only=True)` input assembly (the committed caiso-202
  pattern) rebuilt from the keeper bundle's own `meta.json`; imports the
  committed caiso-215 probe for the hub actuals and the committed hour clock.
* `results/calibration/_caiso216_belly_surplus.json` — every number below,
  committed (deterministic: sorted keys, rounded floats, no timestamps).
* Controls (§A): the reconstructed per-zone demand matches the keeper
  sidecar's per-zone demand to **0.0 MW** in all 7 zones × 3 years (the
  meta-kwargs mapping carries the keeper's full override dict — the probe
  documents the `coal_prb_sigmoid_overrides → prb_overrides` rename a naive
  kwargs filter drops, which reproduces a ~5 % demand error if missed).

Reproduction: `pip install numpy pandas pyarrow pydantic pyyaml scipy highspy
openpyxl tzdata` then `PYTHONPATH=.:src python3
scripts/probes/_caiso216_belly_surplus.py` (first run rebuilds the fleet-only
assembly per year, minutes each; cached thereafter).

---

## §A — Instrument and controls

Inputs: the keeper's `hourly/` sidecars (per-zone demand/price/dump, ISO
class MW, storage charge); the fleet-only assembly (per-zone wind/solar
bounds = cf×cap as the LP receives them, nuclear pmax×availability, hydro
min-gen floors, per-zone storage power, the armed negative-offer floors);
the raw trading-hub RTM CSVs via the caiso-215 loader; CAISO's published
production-and-curtailments workbooks (5-min, Local/System reason); the
EIA-930 CISO region parquet (D/NG/TI); `ATL_PNODE_MAP.csv`; the EIA-860
operable parquets + the eGRID location lookup through the model's own
`build_zone_lookup("CAISO")` membership filter.

Controls: (i) demand row-match 0.0 MW (above); (ii) the model's endogenous
spill (ISO potential − sidecar wind+solar dispatch) = **480 / 1,176 / 852
GWh** (2023/24/25), 84–91 % of it in hod 10–15 — the model does curtail,
just 5.5× / 2.9× / 4.4× less than reality's reported record (§D), and only
pooled (§C); (iii) the armed offer floors read back at **wind −$26 / solar
−$20** — the exact prices the B3 spill-hour λ floors print, confirming the
per-zone λ series and the offer assembly agree.

## §B — THE DECIDING TABLE: the south's zero-MC net position, by cut and layer

Layer L2 (renewables potential + nuclear + the biomass/OTHER demand-share
injection − zone demand; hydro's min-flow floor adds < 0.12 GW and is
reported as L3 in the JSON). "s-neg hours" = reality's TH_SP15 RT < $0 hours
(688 / 1,230 / 964); "split hours" = reality's NP15−SP15 > $15 hours
(1,310 / 1,691 / 1,347). Absorption bounds: the ARMED directional S→N caps
(Path 26 3,000 MW / Path 15 5,400 MW; `measured_interface_limits`, keeper-on)
and the in-cut storage charge power (a deliberately GENEROUS absorption
bound: end-state power, no SOC/energy limit).

| year | cut | belly mean MW | s-neg hours pos | s-neg mean MW | h > path | h > path+stor | pos TWh |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | cut26 (south3) | −4,566 | 118/688 | **−1,640** | 3 | 0 | 0.29 |
| 2023 | cut15 (south4) | −2,370 | 493/688 | **+1,101** | 17 | 0 | 1.44 |
| 2024 | cut26 | −3,706 | 448/1,230 | **−1,102** | 59 | 0 | 1.10 |
| 2024 | cut15 | −800 | 934/1,230 | **+2,288** | 234 | 0 | 3.95 |
| 2025 | cut26 | −2,786 | 444/964 | **−550** | 73 | 0 | 1.13 |
| 2025 | cut15 | +703 | 821/964 | **+3,370** | 289 | 0 | 5.72 |

Readings: (1) **south3 has no surplus** — at the Path 26 cut the charter's
"allocation" branch fires cleanly: no price-formation change can create a
surplus regime out of a −0.5 to −1.9 GW net-short region. (2) **south4's
surplus is real and year-growing** — the charter's binary resolves as a
HYBRID with a measured split: the surplus exists at the cut reality actually
splits at, but at 17/234/289 h over the armed 5,400 MW rating the S→N
constraint is effectively never tested, and the caiso-215 measurement (model
split hours: 0/0/0) follows: the surplus pools north and into storage at
charge-parity prices. (3) The pos-TWh column against reality's stranded
volume (§D: 2.66/3.42 TWh curtailed + belly exports) says the model's south4
surplus is also **under-sized ~2×** even where it exists.

## §C — The model's absorption/price state in those hours (why nothing prices)

* **The floor only ever engages pooled.** Hours with λ ≤ $0: NP15 = ZP26 =
  LA_BASIN = SP15_rest exactly (314 / 604 / 507) — the four non-pocket zone
  λ series hit ≤ 0 only simultaneously, at the −$20 solar offer floor (belly
  p05 = −$20 in every zone-year). The model reproduces a *system* oversupply
  regime but has never once priced a *southern* one (caiso-215: 0 h of
  NP15−SP15 > $15).
* **The one exception proves the machinery works**: SDGE-only λ ≤ 0 hours
  (SDGE ≤ 0 while SP15_rest > 0) = **206 / 194 / 432** — the LCT one-way
  import cap into the SDGE pocket is the model's ONLY armed limit that can
  strand southern supply, and behind it zonal separation forms exactly as
  designed (rule 1 structural witness: give the topology a binding limit and
  the price formation follows; nothing else needs inventing).
* **Storage never saturates on power**: belly charge p95 = 4.7 / 7.2 / 9.1 GW
  against 9.6 / 13.2 / 17.5 GW fleet power — 0 hours at ≥ 90 % of power in
  any year. The belly λ is the charge-parity dual (caiso-202 §C.2), and the
  ≥ 4 GW standing power headroom is what a marginal GW of southern surplus
  meets — it pools, it never strands. Dump: 0 hours.
* Belly λ p50 is flat across zones at $41–42 / $30–31 / $31–33 — the pooled
  CC/charge band caiso-215 measured against reality's south-3×-lower
  sub-$20 hour counts.

## §D — Reality's stranded-surplus record (the target regime, quantified)

From CAISO's published workbooks (5-min, MW-per-interval — established
against the published annual total: 2024 sum/12 = 3.423 TWh). Coverage
note: the corpus README's "discontinued as of 2025-06-01" line does NOT
truncate the 2025 workbook — it carries all 12 months (3.766 TWh; span
measured from the rows, `record_span` in the JSON; README annotated this
session so the ambiguity isn't re-inferred as a data gap):

| year | curtailment TWh (wind+solar) | **Local share** | belly (hod 10–15) share | top months | model spill / record |
|---|---:|---:|---:|---|---:|
| 2023 | 2.66 | **78 %** | 76 % | Apr, Mar, May | 18 % |
| 2024 | 3.42 | **92 %** | 70 % | Apr, Mar, May | 34 % |
| 2025 | 3.77 | **83 %** | 72 % | Mar, Apr, Feb | 23 % |

* The record's dominant class is **Local** — sub-zonal congestion no 5-zone
  pool can strand by construction. This is the honest bound on what ANY
  zonal repair (C1 included) can reproduce, and the measured evidence base
  for the residual's structural home (§F.3a).
* **The belly export witness** (EIA-930 CISO TI, + = export): reality's belly
  TI swings to net export in **900 / 676 / 601** h (p95 +3.2/+3.1/+2.4 GW)
  while the model's belly import class runs p50 **3.0 / 3.4 / 3.4 GW** and
  can never export (the P1 build wires no export column; `EXPORT_TRANCHES`
  exists un-called on the solve path; `caiso_p1_export_sink_seam` R,
  default-off). In the belly the model's boundary sits 3–6 GW long relative
  to reality's — a second, import-side reason its *pooled* λ still clears at
  the charge band. Not proposed as a lever (caiso-142's kill is
  mechanism-level and stands); recorded because post-C1 it becomes the
  C3b-side contingency (§F.3c).

## §E — The allocation evidence: the estimate vs CAISO's own geography

The model's CAISO zone assignment is a documented estimate: latitude cuts at
36.5° (Path 15) / 35.0° (Path 26) plus county rules
(`data/zone_assignment.py::_caiso_zone`). The committed
`ATL_PNODE_MAP.csv` (13,484 rows; TH_NP15/ZP26/SP15 generator membership —
the SAME authority the caiso-172 keeper derivation used for the load split)
disagrees at every boundary witness tried:

| witness (pnodes) | model zone (rule) | CAISO's own hub | movable mass |
|---|---|---|---|
| DIABLO (12) | NP15 (county lift) | **TH_ZP26** | 2,077 MW-mean nuclear (2024 recon) |
| TOPAZ (13) | NP15 (county lift) | **TH_ZP26** | cc-lift solar cohort 1,285 MW |
| ALTA Tehachapi (43) | ZP26 (lat ≥ 35.0) | **TH_SP15** | band26 wind cohort 2,955 MW |
| WINDHUB TRTP (24) | ZP26 (lat) | **TH_SP15** | (in the band26 cohort) |
| MUSTANG Westlands (12) | ZP26 (lat < 36.5) | **TH_NP15** | counter-directional |
| GATES / MIDWAY (27/14) | — | TH_ZP26 | boundary anchors consistent |

Straddle mass (EIA-860 operable through the model's own membership filter):
solar 20,304 MW total, of which 4,810 MW sits within ±0.25° of the Path 26
cut and 1,204 MW within ±0.25° of Path 15; wind 6,263 MW with 3,296 MW on
the Path 26 cut. Currently-north movable cohorts: ZP26-band26 969 MW solar +
2,955 MW wind; NP15-band15 913 MW solar; NP15 central-coast lift 1,285 MW
solar. MUSTANG proves the correction is two-directional — a membership
crosswalk, not a lat re-tune (which rule 23 would also forbid: the cuts are
frozen derive parameters; the crosswalk replaces the estimate with source
data, the one sanctioned route).

**The what-if arithmetic (input-side, no LP; upper bounds pending the real
join).** S1 = L2 + Diablo to the south4 side; S2 = S1 + the movable cohorts
shaped by their source zone's own CF profile:

| year | variant | s-neg hours pos | s-neg mean MW | **h > 5,400 path** | reality split h | pos TWh |
|---|---|---:|---:|---:|---:|---:|
| 2023 | S1 | 627/688 | +3,149 | 122 | 1,310 | 3.95 |
| 2023 | S2 | 665/688 | +4,559 | **342** | 1,310 | 6.49 |
| 2024 | S1 | 1,090/1,230 | +4,129 | 487 | 1,691 | 6.93 |
| 2024 | S2 | 1,127/1,230 | +5,302 | **742** | 1,691 | 9.56 |
| 2025 | S1 | 882/964 | +5,251 | 739 | 1,347 | 9.70 |
| 2025 | S2 | 904/964 | +6,568 | **1,143** | 1,347 | 13.07 |

With the measured re-allocation the S→N binding count reaches **the same
order as reality's split-hour count, in reality's year-ordering, with 2023
3× below 2024/25** — the geometry the caiso-215 envelope needs (2024 −$0.97
/ 2025 −$1.96 required, 2023 headroom −$7.4). In a bound hour λ_south
decouples DOWN from λ_north by the constraint dual: the south (61 % of load)
leaves the pooled $30–42 band for its own marginal — charge parity first,
the −$20 floor when storage energy exhausts — while NP15 prices its own
stack. Direction: C3a-2024/25 down, 2023 little (3× fewer bound hours),
NP15's standing under-price (−6.6/−0.8 %) RISES toward truth. The magnitude
is the funded solve's question and is deliberately not estimated here beyond
the hour-count match (the LP re-equilibrates storage, imports, and gas).

## §F — Candidate adjudication (kill-before-propose)

### F.1 — C1, the measured generator-hub-membership crosswalk. PROPOSED — the packet's load-bearing item.

Fleet-wide re-assignment of CAISO plant→zone from `ATL_PNODE_MAP` membership
(EIA-860/eGRID plant → pnode join), all techs (renewables, nuclear, thermal,
storage — one crosswalk, applied to every year identically per the rule-22
consistency clause), effective-dated rows honored, unmatched plants falling
back to the current geographic rule with coverage reported.

* **(a) Rule 13.** PASS. A published registry of CAISO's own settlement
  geography; a *quantity*-side input (where capacity sits), not a price or
  outcome; zero free parameters; forward analogue — membership is published
  continuously and a forecast-year plant resolves exactly as today (location
  → zone), only against measured geography rather than a latitude proxy. It
  cannot be tuned to a residual because it contains nothing tunable.
* **(b) Rule 14.** This is the rule-14 canonical move: the lat-cut is
  self-documented as an estimate; the accurate data exists in-repo, and the
  caiso-172 keeper already crossed this bridge for LOAD (cell
  `path15_load_split` K: ATL_LDF × ATL_PNODE_MAP membership, "CAISO's own
  Path-15 geography"). C1 completes the same program on the generation side.
  If the solve's fit worsens, rule 14's discipline applies: keep the
  accurate input, root-cause the newly visible error.
* **(c) Why the caiso-215 H2 kill does NOT apply.** H2 killed *mean-zero
  zonal redistribution* — re-labelling a fixed price surface nets to ±$0.15
  by construction. C1 moves *physical supply* across constraints and changes
  the LP's binding set: bound hours split the system marginal itself. The
  scored mean moves through the 61 %-weighted southern λ in 342–1,143 new
  bound hours, not through re-weighting. (The §D.1 netting identity holds
  only when the zonal λ vector is unchanged — here it is the thing changing.)
* **(d) Rule 19 ownership.** The owning surface is the zone-assignment layer
  itself (`data/zone_assignment.py`), which no ScenarioConfig mechanism
  duplicates; no floor/bridge overlaps it. The armed mechanisms it composes
  with (`measured_interface_limits` directional caps, `zonal_loss_surface`,
  `negative_renewable_offers`, storage) are exactly the machinery that
  produces the priced outcome — nothing new is armed.
* **(e) Size vs envelope & 2023 safety.** §E table: bound-hour counts land
  in reality's order with the 2023/2024–25 asymmetry the envelope requires;
  full-size 2023 exposure is bounded by its 342 h (S2 upper bound) against
  −$7.4 headroom (and the up-side risk — NP15 rising — is bounded by 2023's
  own +5.9 pp up-headroom and is truth-ward per §A of caiso-215: NP15-2023
  reads −5.3 %).
* **(f) Risks, honestly.** (i) The upper-bound cohorts may shrink at the
  real join (S1, the Diablo-only floor, already yields 487/739 bound hours
  in 2024/25 — material on its own); (ii) C3b: new low-price southern mass
  deepens the duration curve's left tail — reality has that mass (south
  sub-$20 hours ~3× NP15's, caiso-215 §B), but the −$20 floor vs reality's
  ~−$15..−$18 south-negative means the gate table's C3b MUST-NOT-REGRESS
  (0.098/0.179/0.182, 2025 margin 0.018) is the live tripwire; (iii) fuel /
  basis side effects of re-zoning thermal plants are second-order (CAISO
  fuel pricing is plant-resolved, not zone-resolved, in the keeper's
  monthly-actuals path); (iv) the crosswalk moves the loss-surface zone
  populations — re-derive per rule 23 only via its own source-data pathway
  (the surface is zone-defined, so a re-zoned fleet is a source-data change
  for it, not a residual re-fit).
* **(g) Intake spec** (the funded work, sized): join EIA-860/eGRID CAISO
  plants (≈300–600 with capacity weight; membership filter already in-repo)
  to pnode prefixes (name-fragment feasibility: every witness tried resolved
  uniquely, §E; the caiso-172 substation-name join is the working
  precedent); land `data/raw/reference/caiso-plant-hub-membership.csv`
  (plant_code, pnode, hub, eff dates, join method) + a curated seam + the
  `_caiso_zone` first-check (the ERCOT `custom-bin-assignments.csv`
  pattern); report joined-capacity coverage per tech (target ≥ 90 % of MW;
  unmatched → current rule). No new ScenarioConfig field is expected (a data
  crosswalk, not a mechanism); if implementation lands one anyway (e.g. a
  gate for A/B control), it enters the matrix per rule 28c in that PR.

### F.2 — The two standing owner objects, re-scored against the SOUTH-BELLY target (charter obligation; committed artifacts only)

* **(a) PS water-state hourly intake** (declined 3×; CA-wide most-favourable
  bound **62.1 % / 10.4 %** of the required 2024/25 C3a move, caiso-186).
  The object is defined on **NP15 pumped storage** (caiso-200 §4: "reshape
  NP15 pumped-storage dispatch"). Against the south-belly target its reach
  is **≈ 0**: (i) it acts north of the cut that carries the error — in any
  S→N-bound hour NP15-side action cannot touch southern λ at all (the
  constraint decouples them); (ii) in unbound belly hours its pumping is
  absorption (raises the pooled λ — adverse sign for an overprice) and its
  generation shifts supply *toward* the belly the model already over-prices.
  **Re-score: DOWN — not a south-belly object; its 62.1/10.4 % remains a
  CA-wide tail-formation bound, now known to address the half of the C3a
  anatomy (NP15/tail) that is NOT where the 2024/25 gap lives.** The wall
  (ruling 4) is untouched; nothing here re-opens the intake.
* **(b) Import spot-capacity derivation** (declined; direct λ share < 5 %,
  caiso-202 §C; witness localized NORTH at caiso-215 §C — model WECC_PNW
  $8–11 below measured MALIN). Against the south-belly target: **≈ 0
  direct** — WECC_DSW tracks PALOVRDE (−$4.3/+$0.0/+$2.2), so the southern
  corridor is already priced about right; the object's action raises
  NP15-side costs, i.e. the MEAN moves up (C3a-adverse in sign, bounded
  < 5 %). **Re-score: DOWN as a C3a lever — unchanged verdict — but
  RE-FRAMED post-C1: in S→N-bound hours λ_north is set by the northern
  stack, and the cheap PNW node then UNDER-prices the north side of the
  split; the derivation becomes a split-magnitude completion item worth
  bundling into the C1 solve's diagnosis, not a standalone ask.**

### F.3 — The strandedness residual (what C1 cannot reach) and its fenced contingencies. NOT ASKED NOW.

* **(a) Sub-zonal (Local) curtailment — the structural home of the residual.**
  78–92 % of reality's record is Local-class: stranded behind collector /
  local constraints INSIDE the southern zones. After a perfect C1, a 5-zone
  pool still cannot strand it (the SDGE witness shows what it takes: a real
  limit in the topology). The faithful representation is a gen-pocket split
  (Kern/Tehachapi collector zone behind a measured export limit) — rule 1
  structure, heavy intake (the LCT reports publish LOAD-pocket import
  limits, not gen-pocket export limits; a citable source for the collector
  limit must be found first). DEFERRED until the C1 solve measures what
  residual is left.
* **(b) Internal-path published operating limits.** If the C1 solve's bound
  hours under-produce reality's 1.3–1.7 kh, the next measured tightening is
  the real-time OPERATING limit on Path 15/26 (derates, nomograms) vs the
  catalog rating. Rule-13 fence, pre-stated: published limits/ATC are
  admissible; **realized flows as caps are not** (a flow cap fitted to
  observed flows is the outcome pin wearing a limit costume). No committed
  source today — an OASIS intake question. NOT asked now.
* **(c) The measured export sink (post-C1 C3b tripwire contingency).**
  caiso-142's R (an absorption column can only RAISE λ) was measured on a
  model that was never long; if C1 lands and the southern floor over-deepens
  (C3b regression at the gate — the −$20 floor vs reality's WEIM-exported
  ~−$5..−$18), the mechanism-reality picture inverts exactly as §F H4's
  fence requires for a re-open: reality's belly export (601–900 h, §D) is
  then the missing ABSORPTION that lifts the model's too-deep floor toward
  truth. Contingent new-evidence standing only — the `EXPORT_TRANCHES`
  CAISO sinks are still G-26-flagged static-fitted and would need their own
  measured derivation first. NOT asked now; recorded so a C3b trip at the
  gate has its named diagnosis.
* **(d) Killed restatements** (no re-litigation): `caiso_solar_cap_at_
  delivered` — the self-labelled forbidden pin; local-curtailment-share
  derates — remove supply (λ up: wrong direction) AND outcome-adjacent;
  per-zone/per-year offer objects — caiso-202 §F stands; mean-zero zonal
  instruments — caiso-215 H2 stands (and C1 is not one, §F.1c).

## §G — The packet (ranked, gated, priced)

**Ask 1 — fund the C1 crosswalk intake** (one session, no solve): §F.1g
spec. Deliverables: the membership reference CSV + curated seam + assignment
first-check + coverage report + this probe re-run showing the realized
(non-upper-bound) S1′/S2′ surplus table. **Decision value: even a null
result is decisive** — if the real join moves materially less mass than S2,
the allocation lever shrinks toward the S1 (Diablo) floor and the residual
attribution shifts to §F.3's strandedness with measured weight.

**Ask 2 — fund one 3-year solve** (keeper recipe + crosswalk; years
sequential per rule 12) under this pre-registered gate table:

| gate | requirement |
|---|---|
| C3a | scored all three years; 2024/2025 toward band, **2023 stays in band** (down-headroom −$7.4, up-headroom +$5.9) |
| C3b | **MUST-NOT-REGRESS vs 0.098 / 0.179 / 0.182** (2025 margin 0.018 — the composition watch is THE tripwire; a C3b trip reads as §F.3c's diagnosis, not a C1 refutation) |
| C8 / D-1..D-4 | forced-energy budgets and windows unchanged — C1 adds no floor, no forcing |
| C6 | attestation regenerated at promotion (also discharges filed item 2) |
| DOF | 10/7 unchanged + one **measured-input** identification row (the crosswalk source + join method); zero new tunables |
| LOYO | not applicable as parameter identification (nothing is fitted); the mechanism-change flip rule (rule 20) applies unchanged if any verdict flips |
| split witness | re-run `_caiso215_c3a_zonal_decomp.py`: model NP15−SP15 > $15 hours 0 → reported; the per-zone C3a table re-printed |

**Partial-close pre-registration** (carried from caiso-215 §G, unchanged): a
2024-only pass is NOT a determination flip; NOT-YET stands unless 2025
clears with 2023 in band. **Cost note:** one 3-year plant-level CAISO solve
(rule 12 concurrency cap applies if run alongside another ISO).

**Ask 3 — nothing else.** The contingencies (§F.3a/b/c) are named,
rule-13-fenced, and deliberately unfunded until Ask 2's gate evidence picks
among them. "Still nothing admissible" is no longer the state: C1 is
admissible today on committed data.

## §H — Record changes (rule 28b — CAISO shard only; NO verdict moves)

* Matrix §5.2: caiso-216 block added above caiso-215's. Shard `gates` stamp
  prepended (2026-08-23, session caiso-216); `updated` bumped. Evidence
  strings APPENDED (no cell/fc moves) on: `measured_interface_limits` (the
  armed directional caps never bind for want of southern surplus — 17/234/289
  h over path at L2; 342/742/1,143 at the S2 membership bound),
  `path15_load_split` (the gen-side witnesses: DIABLO→TH_ZP26,
  ALTA/WINDHUB→TH_SP15, TOPAZ→TH_ZP26, MUSTANG→TH_NP15 — the load-side
  crosswalk's authority extends to generation), `solar_deliverability`
  (reality's record measured 78/92/83 % Local-class — the sub-zonal
  strandedness bound), `negative_renewable_offers` (the floor engages only
  pooled: all-zone simultaneous −$20 in 314/604/507 h; SDGE-only 206/194/432
  h is the lone zonal separation), `import_hub_pricing` (belly boundary:
  model import p50 3.0–3.4 GW vs reality TI swinging to export 601–900 h).
* `docs/calibration-log/caiso.md`: caiso-216 entry.
* Probe + JSON committed under `scripts/probes/` / `results/calibration/`.
* **Filed items — SEVEN** (six carried from caiso-215 §H + one new):
  (1) stale `offer_curve_by_group` DOF text; (2) keeper
  `legitimacy_diagnostics.json` regeneration (chp_steam D-4 vintage drift) —
  discharged by-product of Ask 2 if funded; (3) caiso-205 pair site
  retention; (4) promoting sessions re-measure the whole scorecard; (5)
  three CAISO bench parts unstamped (HARD STALE); (6) the unsupported
  `zonal_gas_basis: K` shard cell (re-adjudicate caiso-203-style);
  **(7, NEW)** the `solar_deliverability` K cell describes the pre-LP derate
  that `caiso_solar_endogenous_spill` (armed) SKIPS by design — the cell
  text should say the K rides the endogenous-spill leg on this keeper; fold
  into the next promotion's shard pass (no verdict move implied).
* Open cross-lane items (NOT CAISO's): THREE carried unchanged —
  `check_bench_freshness` D1+D2; five-ISO bench regeneration + CI gate;
  cccc911 forecast-sidecar citations.

## §I — DO-NOT-REDO (new, binding; caiso-202 §I and caiso-215 §I carry whole)

* **Re-measuring the south net-position stack, the sensitivity table, the
  pooled-floor/SDGE witnesses, the curtailment Local/System split, or the
  belly TI comparison** — `_caiso216_belly_surplus.py` reproduces all of it
  from committed bytes (fleet-only assembly cached per year); the JSON
  carries every number.
* **Re-arguing the south3/Path-26 branch as a price-formation question** —
  §B: south3 is net-short in every year; there is nothing to price at that
  cut until allocation moves.
* **Proposing lat-cut re-tuning as the allocation fix** — §E MUSTANG: the
  error is two-directional; rule 23 freezes the cuts; the membership
  crosswalk is the one sanctioned route.
* **Treating C1 as barred by the caiso-215 H2 mean-zero kill** — §F.1c: C1
  changes the binding set; H2's identity is conditional on an unchanged
  zonal λ vector.
* **Re-opening caiso-142 (export sink) without the §F.3c tripwire firing** —
  the contingency is pre-fenced on a C3b regression at the funded solve's
  gate, nothing less.

Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, the
§5.2 header (beyond the caiso-216 block addition), every bench part, and
every source file other than the additions listed in §H: UNCHANGED. Next
number: caiso-217.
