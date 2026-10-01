# PREREG miso-185 — the SOUTH FIRM-EXPORT EVIDENCE HUNT: the miso-182 §6b re-open ladder for `miso_south_firm_export_block` (`G`), with the source ladder, admissibility lines, kills and the conditional build/A-B frozen BEFORE any source is touched

**Session miso-185 (2026-08-25).** Charter: the miso-184 queue head
(`FINDING-miso184-export-ladder-tail-adjudication-2026-08-24.md` §5 road 1;
matrix §5.4 stamp miso-184) — execute the miso-182 §6b re-open ladder for
`miso_south_firm_export_block`, the ONLY named road left that directly targets
the established C3a-2025 scarce-export defect. The cell is **`G` on DATA, not
on form**: the Manitoba annual-flat form K-1 CLEARED 0/3 at miso-182 §3 (it
does not worsen any year), and miso-184 established that what the scarce tail
needs is exactly a **scarcity-coincident, price-INELASTIC export** — the
firm/scheduled-block class. The block is armed ONLY if driver data lands and
clears all three §6b questions; the MW comes from the CONTRACT series (term
and MW), never from the residual (rules 13 `[R-MEASURED]` / 23
`[R-FROZEN-DERIVE]`).

This document is committed and pushed **BEFORE the hunt begins** — before any
EQR record, OASIS query, GFA list, eLibrary result, tariff attachment, or any
other candidate-source content is retrieved, and before any adjudicating
quantity is computed. The miso-182/183/184 prereg discipline, carried in full.

## 0. The pre-registration boundary (what has been looked at, and what has not)

**Looked at (committed artifacts only):**

* The miso-174…184 findings and records, all committed — in particular
  miso-182 (`G` verdict, §6b re-open ladder, §8 non-exhausted-source
  disclosure), miso-183 (V-TRADE: the basis-free object), miso-184
  (V-DEFECT-COUPLING: the ladder class exhausted; PREREG-miso184 §6, whose
  A/B gates this document reuses verbatim).
* The in-repo implementation of the Manitoba firm-import block
  (`src/market_sim/model/interchange/spec.py:1535–1599` —
  `MISO_MANITOBA_FIRM_IMPORT_*`, `resolve_miso_manitoba_firm_import_mw`):
  annual-flat MW by year, price-insensitive (offer $8, floor frac 1.0),
  attached at a named zone. This is the K-1-cleared FORM the conditional
  build mirrors on the export side.
* The in-repo substrate for the seller-set construction (§2 E-0):
  `data/raw/eia-860/eia860_plant.parquet` / `eia860_owner.parquet` /
  `eia860_utility.parquet` exist with plant/owner/utility grain (schema
  glanced only to confirm the columns exist; no content enumerated).

**NOT looked at (the hunt's subject matter — untouched at commit time):**

* No FERC EQR record of any kind (contract or transaction, any seller, any
  quarter).
* No MISO OASIS reservation record; no GFA inventory or tariff attachment
  content; no Entergy unit-power-sale filing; no pseudo-tie or
  dynamic-schedule inventory; no eLibrary informational filing; no TVA
  disclosure document.
* No quantity that could adjudicate any gate below has been computed.

## 1. The object (committed values, restated; nothing re-measured here)

* **Basis-free (miso-183):** in the 2025 scarce set (47 h) the measured
  MISO-South boundary complex moved **−2.441 GW OUT** (annual −1.166) while
  the keeper moves ≈ **+0.35 GW INTO** the South (interval mid); the
  conservative interval end puts the shortfall at **≥ 0.93 GW**. The measured
  RDT bound **S→N in 32/47** scarce hours (≥1 5-min row; 9/47 majority) and
  **N→S in 0/47** (0/72 across 2023–25); the keeper binds N→S in 9/47.
  The retired pool-basis "+1.19 GW" is NOT quoted as the object's size.
* **Mechanism class (miso-184):** the measured South export is
  price-inelastic (Spearman |r| ≤ 0.19 vs every admissible basis) and
  DEEPENS under scarcity (2025: c_k > d_k at all 8 bands); the
  willingness-to-pay ladder class cannot carry it
  (`miso_south_export_ladder_rt_tail` `R` — adjudicated, not re-testable).
* **The candidate form (miso-182 §3, K-1 CLEARED):** an annual-flat,
  price-insensitive block B_y. The Manitoba-identification sizes reached
  29 % / 54 % / 24 % of the scarce gaps — cleared by being too small to harm.
* **Declared against the hunt's own hopes (miso-183 §4):** the consistency
  arithmetic `N_S ≈ S→N wheel (−2.3) + genuine external (≈ −0.14)` already
  suggests the South's genuine third-party trade is SMALL (~0.14 GW). A
  qualifying block, if found, is expected to be modest; a small positive must
  not be oversold, and a negative or immaterial close is the base case. This
  is stated now so no post-hoc narrative can inflate either outcome.

## 2. The source ladder (frozen order; scope bounds; verdict vocabulary per rung)

Per-rung verdicts: `DRIVER` (yields a qualifying obligation series per §3),
`CORROB` (level/path corroboration only — can never size B_y),
`NEGATIVE` (probed, nothing qualifying), `UNREACHABLE` (no admissible access
route from this environment), `NOT-EXHAUSTED` (disclosed coverage gap).

* **E-0 — the seller set (method frozen; runs first, from in-repo data
  only).** MISO-South jurisdictional seller candidates = the union of
  (a) the named incumbents: the Entergy operating companies (Entergy
  Arkansas, Entergy Louisiana, Entergy Mississippi, Entergy Texas, Entergy
  New Orleans, System Energy Resources), Cleco (Power + Cajun), and
  (b) owners/operators of plants in the MISO-South footprint enumerated from
  `eia860_plant.parquet` (Balancing Authority Code = MISO ∧ State ∈ {AR, LA,
  MS, TX}) joined to `eia860_owner.parquet` / `eia860_utility.parquet`,
  ranked by owned capacity. **Declared coverage bound:** pure marketers with
  no South plant are OUT of the scope-by-seller query; any negative close
  must carry this bound explicitly (EQR covers jurisdictional marketers, but
  a seller-scoped retrieval cannot see them).
* **E-1 — FERC EQR, the primary rung (miso-182 §6b(ii)).** Filtered
  retrieval ONLY — by seller and quarter, 2023Q1–2025Q4 — via the EQR
  report-viewer/API filtered-download routes. Both record classes:
  **contracts** (counterparty, product, class, term begin/end, delivery
  point, stated MW/quantity) and **transactions** (classification + level
  corroboration). Customers of interest: {TVA, Southern Co. opcos, AECI,
  LG&E/KU, PowerSouth}; **TVA-weighted** (79–86 % of the pool's gross
  export, miso-182 §2). The key property, per miso-182: MISO's own internal
  Midwest↔South RDT transfer is NOT a sale and files no EQR transaction, so
  an EQR firm sale is clean of the wheel confound **by construction**.
  **NEVER a bulk ~100 GB mirror** (Q-C bounds retrieval).
* **E-2 — MISO OASIS long-term firm point-to-point reservations** at the
  southern seam (sinks TVA/SOCO/AECI/LGEE), archive depth per miso-182 §8.
  A reservation is transmission, not a sale: **CORROB-class alone** (it
  proves path and firmness, not an energy obligation). E-2 + a matching E-1
  contract = DRIVER; E-2 alone never sizes B_y.
* **E-3 — Grandfathered agreements (GFAs)** carried into MISO at the 2013
  Entergy integration (MISO tariff GFA inventories/attachments). A GFA with
  a named external counterparty in the pool, stated MW and stated term is
  DRIVER-class.
* **E-4 — Legacy Entergy unit-power-sale / system agreements** persisting
  into 2023–25 (FERC eLibrary rate schedules). Same DRIVER test as E-3.
* **E-5 — Pseudo-tie / dynamic-schedule inventories** at the southern seam
  (a MISO-South resource pseudo-tied or dynamically scheduled to serve
  TVA/SOCO/LGEE load is exactly a scarcity-coincident, price-inelastic
  export). DRIVER-class only if the MW and the arrangement's term are
  published; **placement additionally requires establishing its EIA-930
  booking treatment** (whether the flow is inside or outside the measured
  DIBA interchange the object is scored against) — unresolved booking =
  fails Q-A for that entry, disclosed.
* **E-6 — FERC eLibrary informational/compliance filings** and the TVA-side
  disclosure class (TVA annual report/10-K purchased-power tables; TVA is
  non-jurisdictional as a seller). **Monthly/annual grain = CORROB only,
  never the driver** (charter line, carried).

The hunt terminates when every rung carries a verdict. A rung whose access
adjudication is already standing in this repo (e.g. MISO Data Exchange
key-gated) is cited, not re-probed.

## 3. The admissibility lines (miso-182 §6b (1)–(3), operationalized and frozen)

A found obligation series is **QUALIFYING** iff it clears all three:

* **Q-A — crosswalk (no invented apportionment).** Each obligation places at
  the model's South seam boundary: (i) seller side — the source
  resource/point-of-receipt is in MISO-South (E-0 footprint), and (ii)
  counterparty/point-of-delivery — a named member of the seam DIBA pool
  {TVA, SOCO, AECI, LGEE} or an entity inside one of those BAs (PowerSouth
  → SOCO BA). Placement is to the **seam aggregate** (the model's single
  external-South complex), NOT per-counterparty — the model carries one
  boundary, so no counterparty apportionment is ever needed; what Q-A
  forbids is an entry that exists only as an aggregate that cannot be
  separated from the RDT wheel (the miso-182 criterion-2 refusal, which a
  named-counterparty contract clears by construction).
* **Q-B — rule-13 forward-regenerability (the likely binding one, miso-182
  §6b question 2).** Qualifying = a contract/obligation with (i) a stated
  term (begin AND end dates) overlapping [2023-01-01, 2025-12-31], (ii)
  term length **≥ 1 year**, (iii) a firm physical power product — frozen
  product classes: capacity, firm energy, unit power, requirements service
  (physical delivery; booked-out, financial/swap, and non-firm/recallable
  classes are OUT), and (iv) a stated or arithmetically-derivable MW
  quantity (a stated MW, or a stated MWh/period convertible to flat MW by
  division; never a fitted shape). **A pile of short-term (< 1 yr) or spot
  transactions NEVER enters B_y** — that is a measured outcome with no
  forward analogue. Ambiguous records are EXCLUDED from B_y (fail-closed)
  and reported as ambiguous.
* **Q-C — cost.** Filtered per-seller/per-quarter retrieval only; total
  retrieval budget declared at ≤ ~2 GB; no full-corpus mirror; quarterly
  files only for quarters in 2023Q1–2025Q4 (holdout: no out-of-train market
  outcomes are retrieved; contract METADATA whose stated term extends
  outside the window is metadata, not an out-of-train market outcome, and
  is admissible). If no filtered route is reachable through this
  environment's egress, the rung is UNREACHABLE — a distinct close from a
  merits negative.

**B_y (frozen formula).** For each year y ∈ {2023, 2024, 2025}:
B_y = Σ over qualifying obligations active in y of (stated MW, prorated by
the fraction of year y the term covers; if a contract states an explicit
seasonal/on-peak schedule, the STATED schedule is used verbatim — stated,
never fitted). Corroboration-class evidence (E-2 alone, E-6, transactions)
never enters the sum. No scaling, no coincidence factor, no residual-derived
adjustment of any kind may be applied after the data lands.

**Materiality line (frozen, and derived from the A/B's own gate).**
The conditional build is licensed iff **B_2025 ≥ 0.1 GW** — exactly the
S-3 outflow-movement threshold (PREREG-miso184 §6): an annual-flat block
below 0.1 GW cannot move the scarce-mean South net inflow by ≥ 0.1 GW even
in the limit where every block-MW is incremental outflow, so arming it
spends six solve-years on a gate it fails by construction.

## 4. Verdict mapping (frozen)

* **V-LANDS:** ≥ 1 qualifying series clears Q-A + Q-B + Q-C and
  B_2025 ≥ 0.1 GW → execute §5 (build + A/B). The cell's final status is
  the A/B's verdict (K/R/I per the gates), stamped in-session.
* **V-NEG-ABSENT:** every rung probed to a verdict; no qualifying
  obligation found → the finding closes negative; **the cell STAYS `G`**
  with its re-open clause NARROWED by what is now excluded; the finding
  hands the owner the **D-4 posture question with the ~1.3 GW scarce-export
  model-class concession as the honest residual** (miso-184 §5 road 4).
* **V-NEG-SPOT:** an external-sale record is found and is affirmatively
  short-term/spot (fails Q-B(ii)) → the V-NEG-ABSENT close PLUS the
  affirmative statement that the measured external leg is not
  contract-shaped — evidence FOR the model-class concession. The cell stays
  `G` (the E-0 marketer bound and the non-jurisdictional-seller bound
  prevent an `R`: absence-of-firm cannot be proven from a seller-scoped
  jurisdictional record).
* **V-NEG-IMMATERIAL:** qualifying obligations exist but B_2025 < 0.1 GW →
  no build; the found B_y is recorded as the honest measured bound on the
  firm leg (it sharpens the miso-183 ≈ 0.14 GW consistency arithmetic);
  cell stays `G` with the bound in its evidence line.
* **V-UNREACHABLE:** E-1 UNREACHABLE and no other rung yields a qualifying
  series → cell stays `G` verbatim; the finding records the access
  adjudication (the miso-77/174 Data-Exchange pattern) so no successor
  mistakes it for a merits negative.

Mixed states resolve mechanically: B_y sums across all qualifying
obligations from all DRIVER-class rungs; the mapping is evaluated on the
total. Every rung's verdict is reported regardless of which fires first.

## 5. The conditional build + A/B (only under V-LANDS; declared now, built then)

* **Field:** `miso_south_firm_export_block: bool = False` (ScenarioConfig,
  MISO-only, default off). **Constants:** `MISO_SOUTH_FIRM_EXPORT_BLOCK_MW_BY_YEAR:
  dict[int, float]` = {2023: B_2023, 2024: B_2024, 2025: B_2025}, each value
  citation-commented to the specific contracts (rule 5 `[R-NO-MAGIC]`);
  backcast years only (the forecast-year story regenerates from the same
  contracts' stated terms — rule 13's test, stated in the code comment).
* **Form:** the export-side mirror of the Manitoba firm-import block
  (`spec.py:1535` family): annual-flat MW, price-insensitive, attached at
  the South boundary complex (`MISO_external_South`), leaving the seam
  ladder and RDT machinery untouched (rule 19 `[R-ONE-MECH]`: the block
  represents the CONTRACT leg only; the ladder keeps the price-responsive
  leg). If a qualifying contract states a schedule, the stated schedule
  replaces flat for that contract's MW.
* **Matrix duty 26(c):** the `miso_south_firm_export_block` base row already
  exists (minted at miso-182 with MISO `G`, others `·`); the build updates
  MISO's cell only, in MISO's shard, same push; `check_mechanism_matrix.py`
  before pushing.
* **DOF ledger:** one entry — B_y, identification source = the named
  contracts (term × MW), zero fitted parameters.
* **Runs:** control `miso185_firm_A` / arm `miso185_firm_B`, each
  `scripts/replay_keeper.py results/calibration/miso177_rho_B` at HEAD,
  `--year 2023 2024 2025` in ONE invocation each, run SEQUENTIALLY (rule 12
  `[R-PARALLEL]`; miso-169 memory recipe: 8 GB swapfile,
  `MARKET_SIM_HIGHS_THREADS=4`, ~13 GB peak on a 15 GB container).
  Registration ids `2026-08-25-miso-185-control` /
  `2026-08-25-miso-185-firmblock` — **BOTH registered whatever the outcome**
  (rule 15 `[R-DASHBOARD]`, full span rule 16 `[R-ALLYEARS]`).
* **Gates: PREREG-miso184 §6 VERBATIM**, with `miso184_tail_*` →
  `miso185_firm_*` and the arm flag → `miso_south_firm_export_block=true`:
  * **S-0 CONTROL INERTNESS (ABANDON):** every scored control sidecar
    value-identical to the committed keeper's; anything else = HEAD drift —
    STOP, report, no arm conclusion.
  * **S-1 EXACTNESS (KILL):** the arm's `run_config.json` records the field
    true (control false/absent); the armed block MW equal the frozen B_y
    tuples; every non-block mc row byte-identical between legs.
  * **S-2 DIRECTION (structural gate):** on the frozen scarce mask, the
    arm's 2025 scarce-hour N→S binding count under the miso-183 spread
    classifier (spread = P1 price(MISO-South) − price(MISO-East); N→S ≡
    spread > $1 outside the RPE ±$1 band) must FALL below the control's
    (committed keeper: 9/47). Reported alongside, never gated: the S→N
    count (measured 32/47 any / 9/47 majority) and the full classifier
    composition, all years.
  * **S-3 OUTFLOW (structural gate):** the arm's 2025 scarce-mean model
    South boundary-complex net inflow `N_S^m` — computed EXACTLY from each
    leg's full solve outputs (link flows into MISO-South + the seam-band
    net at `MISO_external_South`), balance-verified (residual < 1 MW) —
    must move from the control's value toward the measured −2.441 GW by
    **≥ 0.1 GW**.
  * **THE CHARTER KILL:** an arm that improves C3a-2025 while BOTH S-2 and
    S-3 fail is a level adder wearing a repair's name → REJECTED regardless
    of every other number.
  * **S-4 CONDUCT (KILL):** zero D-4 conduct failures on the arm's
    regenerated `legitimacy_diagnostics.json`, zero NEW vs control; C8 PASS
    all years.
  * **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill):** the
    complete verdict scorer on both legs; every regression at full
    magnitude; movements outside the commercial band (±10 %) in 2023/2024
    or any criterion PASS→FAIL flip fire the OWNER-ESCALATION path (posture
    directive: "if structural integrity improves but gates regress that may
    still be a keeper" — escalate, never silently revert; the ercot-231
    precedent), never an auto-reject and never an auto-keeper.
  * **LOYO within 2023–2025 before any promotion** (rules 20/22); a
    promotion re-stamps `keepers/MISO.json` and fires the
    calibration-keeper-auditor.

## 6. Anti-sweep (binding)

* The firm-product classes, the ≥ 1 yr term line, the 0.1 GW materiality
  line, the seam pool set, the E-0 seller-set method, and the B_y formula
  are frozen in this document. **No statistic, classification rule, or
  threshold may be added, removed, or reinterpreted after any source
  content is seen.**
* Ambiguous records fail closed (excluded from B_y, disclosed).
* Corroboration-class evidence never sizes B_y; monthly/annual grain is
  level corroboration only.
* If the hunt surfaces a series suggesting a DIFFERENT mechanism-in-kind
  (e.g. a state-conditioned schedule), it is REPORTED for an owner charter
  (miso-184 §5 road 3), never built here.
* A negative is a result: the finding is written with the same care either
  way, and the D-4 posture handoff (miso-184 §5 road 4) is the declared
  deliverable of a negative close.

## 7. DO-NOT-REDO and governance

**DO-NOT-REDO** (miso-184 §7 carried in full, plus the charter's additions):
`miso_south_export_ladder_rt_tail` `R` (the rebasis is adjudicated — no
variant, no composite basis); `miso_seam_coincident_envelope` `R`;
`measured_interface_limits` `R`; `m2m_seam_entitlement_cap` `G`;
`import_shape_lever` `G`; `internal_congestion_split` `G`;
`zonal_loss_surface` `R`; within-unit `measured_offer_surface` `R`;
`gas_hub_basis_overlay` `R`; `ramp_envelopes` `I`; `dam_availability_rebasis`
`R`; the ordc/reserve and dispersion families (offer family exhausted,
miso-179/180); the `miso_offer_spread_anchored` unspent re-open clause
(untouched; this session may not be cited as graft evidence). The miso-183
basis question is CLOSED (V-TRADE) — the object is quoted ONLY as the
basis-free ≥ 0.93 GW floor / −2.441 GW scarce outflow, never the retired
pool-basis +1.19. `ba_code="SOCO"` stays a forecast-lane rule-14 item. The
import-side ladder tail (miso-184 §4, ~+0.96 GW DA-driven scarce import) is
NAMED, not this session's lever — report only.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only; the holdout
spend freeze ACTIVE; MISO holds neither marker (fail-closed); any fetch
refuses out-of-train market dates (Q-C's quarter bound). Rule 26: §5.4 queue
stamp + `docs/calibration-log/miso.md` entry in-session, negative outcomes
included; cell verdicts ONLY in `docs/codebase-site/data/mechanism-matrix/MISO.js`;
`scripts/check_mechanism_matrix.py` before pushing matrix edits. Rule 27
`[R-PUSH]`: exact on-disk bytes; every pushed blob ≥ 300 lines verified. No
new `.github/workflows`; each commit pushed immediately (HTTP 408/500 →
`git config http.version HTTP/1.1`, retry with backoff). The owner merges;
no PR unless asked.

**Instrument (declared):** `scripts/probes/_miso185_firm_export_hunt.py` —
written AFTER this prereg commits, executing E-0 and the E-1 classification
mechanically per §3, emitting
`results/calibration/_miso185_firm_export_hunt.json`. Source-access probes
(HTTP status, route viability) are recorded in the finding; no adjudicating
quantity exists outside the probe's output.
