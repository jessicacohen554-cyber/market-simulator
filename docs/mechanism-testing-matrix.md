> Status: ACTIVE — the cross-ISO mechanism testing matrix (rule 28 `[R-MECH-MATRIX]`).

# Cross-ISO mechanism testing matrix — methodology, lever queues, glossary

**The canonical data lives in ONE place:**
`docs/codebase-site/data/mechanism-matrix.js` (rendered at
`docs/codebase-site/mechanism-matrix.html`, nav → Backcast → Mechanism Matrix).
This doc is the methodology and the *actionable* layer on top of it: how the
matrix is maintained, how similar the six ISO configs actually are, and the
per-ISO **lever queues** — ranked untested candidates tied to each ISO's
currently-failing calibration gates. The glossary is on the HTML page (and
summarized in §6).

Built 2026-07-27 from a five-way audit: the full `ScenarioConfig` inventory
(634 fields), all six keeper `run_config.json`s, the per-ISO calibration logs
(`docs/calibration-log/<iso>.md` + archive), the forecast program board
(`docs/forecast-development-plan-2026-07.md`, FF-2C/2D/3E), and the site
conventions. Keeper snapshot at build: ercot115 / caiso-130 / pjm-133 /
miso-88 / nyiso-89 / neiso-61.

---

## 1. What the matrix is for, and the update protocol (binding)

The matrix answers three questions no single doc answered before:

1. **Usage** — which mechanisms are armed in each ISO's backcast keeper and in
   its forecast default (they are NOT the same set — see §3.3).
2. **Testing** — for each mechanism × ISO, has it been tested *in that ISO*,
   and with what verdict (`K` keeper / `R` rejected / `I` inert / `G`
   governance-refused / `O` open / `U` untested / `·` n/a).
3. **Transfer** — which mechanisms proven in one ISO are plausible, untested
   candidates in another (the `U` cells), so lanes stop rediscovering each
   other's work — and stop re-testing each other's already-adjudicated dead
   ends.

**Duties (normative text is CLAUDE.md rule 28; this is the working recipe):**

- **(a) Handoff prompts cite the matrix.** Any prompt that opens a calibration
  or forecast session for an ISO includes: a pointer to this doc + the matrix,
  and the target ISO's lever queue (§5). The session picks its lever from the
  queue or states why it is going off-queue. It never re-tests a cell already
  marked `R`/`I`/`G` without new evidence (the DO-NOT-REDO discipline —
  e.g. caiso-129's explicit list, ERCOT-122…126's exhausted coal enumeration).
- **(b) Test ⇒ update the cell, same session.** Probe, candidate, or keeper —
  the session that produces a verdict edits the mechanism's row in
  `mechanism-matrix.js` (cell char + `ev` citation + note if the story
  changed), in the same commit series as its rule-15 dashboard registration.
  Rejected probes update the matrix too; a rejection that isn't recorded will
  be re-run by someone else.
- **(c) New mechanism ⇒ new row, same PR.** A PR that adds a solve-affecting
  `ScenarioConfig` field/flag adds its matrix row (all six cells — mostly `U`
  and `·` at birth). A mechanism absent from the matrix is an off-registry
  tuning channel in spirit (rule 24).
- **(d) Verdicts are per-ISO** (rule 25). `K` in PJM says *nothing* about
  MISO. Transfers enter the target ISO as `U`, and the target session derives
  its own parameters from its own fleet/market data — never imports the source
  ISO's fitted values.
- **(e) Keeper swaps re-stamp the header.** When a keeper changes, refresh the
  `keepers`/`gates` header block and re-check that ISO's column (a promotion
  usually flips 1–2 cells).

**Mechanical enforcement.** `scripts/check_mechanism_matrix.py` (stdlib-only)
runs as the `mechanism-matrix-guard` CI job on every PR: it validates matrix
integrity (unique ids, well-formed 6-char cells), **fails** a PR that adds a
new `ScenarioConfig` field not mentioned anywhere in the matrix (duty c —
mention-anywhere is the escape hatch for sub-scalars that belong on an
existing family's row), and **warns** when a new backcast registry sidecar or
calibration CLI flag lands without a matrix touch (duty b — advisory, since
re-runs of recorded recipes legitimately change no cell). In-session, the
`.claude/hooks/mechanism-matrix-reminder.sh` SessionStart hook injects the
duties and pointers at the start of every session, local and web.

## 2. How similar are the six ISO configs? (the up-front answer)

Quantitatively, from the keeper `run_config.json`s (true non-default counts,
excluding JSON round-trip artifacts): **ERCOT 73, PJM 80, CAISO 77, MISO 69,
NYISO 60, NEISO 50** non-default fields.

**Three layers:**

1. **A shared backbone all six run (~30 mechanisms).** One ISO-agnostic LP;
   CAMPD per-plant binning; P0→P1 two-pass pricing; `reliability_floor`
   engine; per-plant coal/CC must-run + CHP steam-following;
   `offer_curve_by_group`; measured annual HH pin + per-plant monthly coal
   pricing; CAMPD outage windows; v2 emission rates; and — the flagship —
   **`gas_offer_net_revenue_margin`, the only calibrated mechanism adopted in
   all six keepers** (per-ISO measured anchors 2.25→4.80 $/MMBtu; precedent
   chain NEISO→CAISO→ERCOT→NYISO→PJM→MISO).
2. **A five-ISO plant-level standard with ERCOT as the deliberate holdout.**
   `plant_level_fleet`, `gas_offer_curve` tranches, `gas_monthly_actuals`,
   `gas_plant_monthly_fuel_pricing` + fallbacks, `gas_daily_shape`,
   `cc_peaking_per_plant`. ERCOT instead runs its own CAMPD-bin + 60-Day
   disclosure stack (DAM availability at plant grain, cleared-share offer
   ladder, GTC limits, storage-AS credits). Whether any of the five-ISO fuel
   mechanisms would move ERCOT's 2023 residual is **untested** (§5.1).
3. **Large ISO-exclusive families encoding each market's real design**
   (armed flag counts: ERCOT 24 `ercot_*`, CAISO 21, MISO 16, NYISO 14,
   PJM 10, NEISO 4). These are *structural*, not drift: RA must-offer exists
   only in CAISO; ORDC/ASDC co-optimization only in ERCOT; RDT/TCDC only in
   MISO; LCR/TSL localities only in NYISO; winter fuel security only in
   NEISO; DA virtual depth + star-node congestion only in PJM. Rule 25 makes
   the fitted *values* non-transferable — but the *mechanism shapes* transfer,
   and that is what the `U` cells track.

**Where the six genuinely disagree on the same phenomenon** (each a deliberate,
logged choice, not an accident): coal offer economics (sigmoid passthrough
everywhere coal matters *except* MISO, which refuted the SOM deep-discount
premise and runs near-cost + take-or-pay committed bands); scarcity price
formation (in-LP co-opt: 5 of 6; CAISO alone runs a post-solve overlay and has
**never tested the in-LP co-opt** — its pergen builder is incomplete);
commitment scaffolding (three per-ISO bridges off one shared detector vs
floor-limb registries vs NEISO's legacy-P2 exception); interchange (priced
node CAISO/PJM/MISO/NYISO vs fixed tranches NEISO vs n/a ERCOT); outage
re-basis (ERCOT measured-DAM keeper; NEISO/MISO tested-and-rejected theirs;
PJM's is intaken-but-untested); `wefor_multiplier` 0.7 five ISOs vs 1.0 MISO.

**Forecast-lane similarity is much higher than backcast** — by design the
forecast reference config is bare `ScenarioConfig` defaults + `mode`, so the
six differ only through registries: capacity-curve clearing (PJM/MISO/CAISO/
NEISO on; NYISO deliberately excluded pending re-calibration; ERCOT
energy-only), the reserve-margin backstop (off for ERCOT), the ERCOT-only
correlated-outage curve, and per-ISO PRM/ELCC/net-CONE tables.
**Keeper-only mechanisms whose global default is False never reach the
forecast lane** (verified for `coal_econ_marginal_hr_bound`,
`measured_ct_heat_rates`, `hydro_budget_nameplate_aware`,
`carry_operating_mothballs`, and CAISO's `capacity_deliverability_limits`
part (a)) — a structural inheritance gap the matrix's `fc` fields track; the
G4 mode-aware seam (forward analogues like `ercot_reserve_supply_forward`,
`caiso_corridor_atc_forward`, `--hydro-forecast-budget`) is the sanctioned
closure path, mechanism by mechanism.

## 3. Reading the matrix

- **Categories** (14) follow production-cost-modeling practice: market
  structure; price formation & scarcity; reserves/AS co-optimization;
  commitment & floors; offer curves; fuel; outages/availability;
  renewables & hydro; storage; network/seams; demand; capacity evolution & RA
  (forecast); policy; emissions.
- **`mode`** tags the lane: `B` backcast-only overlay (measured artifact, no
  forward analogue), `F` forecast-only, `BF` both. Rule 13's admissibility
  test decides `B` vs `BF`.
- **`fc`** appears where the forecast-lane posture differs from the backcast
  cells (capacity rows; `correlated_forced_outage`;
  `capacity_deliverability`).
- **Row-level notes carry the adjudication one-liners** with calibration-log
  ids — the log entry remains the evidence of record.

## 4. Cross-ISO patterns the matrix makes visible

1. **Reserve/scarcity dormancy is one problem, not four.** Reserve duals sit
   at ~$0 in NEISO (all 26,280 h), PJM (max $211), MISO (0/6/2 h); CAISO
   models zero C3c hours. Shared root cause: LP-vs-MIP under the no-MIP
   mandate. ERCOT is the exception (its measured envelopes bite — and
   over-fire when placed in-LP). Any C3c lever queue below inherits this
   ceiling; PJM/NYISO/NEISO adjudications say the *reserve-tier* route is
   closed and the live candidates are *offer/DA-depth-side*.
2. **`hydro_budget_nameplate_aware` is the template transfer** (CAISO →
   PJM, promoted in both; MISO/NYISO/NEISO cells `U`), and it surfaced the
   **PS-inclusive hydro pin defect** — audit every hydro ISO whose BA omits
   `NG: PS` from EIA-930 `NG: WAT`.
3. **`pjm_da_virtual_bids` is the highest-value untested transfer**: it moved
   PJM's 2025 C3c 0→17 h — and C3c is exactly the sole/ledgered blocker for
   NYISO and NEISO and failing in CAISO/MISO/ERCOT.
4. **The CAMPD economic-layup defect is upstream of everything** (all six
   extracts; holdout frozen; MISO/PJM/NYISO re-tune required; downstream
   derived artifacts not yet re-derived post-guard — an open cross-ISO audit).
5. **Topology splits are dead at both tested ends** (ERCOT-117, MISO-79):
   missing congestion is sub-zonal; the path forward is data intake (nodal/
   station crosswalks), not invented interfaces.
6. **Registry hygiene items the audit surfaced** (file separately, not levers):
   `--ramp-limits` is a dangling CLI flag (no `ScenarioConfig` field — should
   `TypeError` if passed); `historic_outage_overlay` defaults True but has
   been inert since 2026-07-17; `correlated_forced_outage` defaults True with
   an ERCOT-only curve registry (silently inert ×5);
   `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` is empty; every
   `thermal_tranches_<ISO>.csv` is provenance-orphaned (miso-95); the forecast
   board's gate-(a) keeper names are stale vs HEAD.

## 5. Per-ISO lever queues (untested candidates → failing gates)

Ranked; each entry names the gate it targets and the identification that must
be derived **from that ISO's own data** before any solve (rules 23/25). Queue
order is a prior, not a mandate — a session with a better-identified lever
goes off-queue and says so. Entries already adjudicated elsewhere are *not*
repeated here; the matrix `R`/`G`/`I` cells are the DO-NOT-REDO list.

### 5.1 ERCOT — targets C3a/C3b-2023, C3c (attributed), C7 lignite, coal seasonal split

The lane is heavily enumerated; the honest top of the queue is closure work,
not a new sweep:

1. **C6 governance attestation of the C3c tail** as an attributed
   measured-input limitation (ERCOT-101/107/108 adjudication) — the named
   closure route; blocked only by the 8 residual-identified DOF entries.
2. **Coal dispatch-band mechanism** (ERCOT-117 §5.3 named successor): real
   fleet works 0.54–0.72 of its range, model rides ceilings (43–50% of energy
   within 0.5% of plant-month max vs 3.6–6.9% actual) → C7 COAL_LIGNITE-2023
   + the ±1.5 GW coal seasonal split. Needs a measured band identification
   (CAMPD loading distributions), not a floor.
3. **Five-ISO fuel stack on ERCOT** (`gas_daily_shape`,
   `gas_monthly_actuals`, `gas_plant_monthly_fuel_pricing`) — consistency
   audit + candidate for 2023 winter-volatility C3b; cheap A/B, zero new DOF.
4. **`tranche_startup_amortization`** (PJM/MISO/NEISO form) vs ERCOT's
   season-spread ST startup — mid-merit/trough price formation candidate.
5. **`measured_ct_heat_rates`** (NYISO form) on ERCOT's CT fleet — audit-grade.
6. **WP-B nodal curtailment layer** — *data-intake first* (station→area
   crosswalk does not exist in-repo), then the under-curtailment gap
   (ERCOT-121).

### 5.2 CAISO — targets C5a (all years), C3c-23/24, C3a-2025

1. **`energy_reserve_coopt` + completing `caiso_reserve_coopt`** (add
   storage/hydro/RegUp-Down to the pergen builder first — documented gaps) —
   the only ISO that has never tested the in-LP co-opt, and its C3c is 0
   modeled hours. Expect LP-dormancy (pattern §4.1); the test is still owed
   before any further overlay work (rule 19: pick one owner for scarcity).
2. **Corridor/export-path congestion family** — the *selected* open family for
   C5a (59–101% of the belly wedge is DSW→CA congestion, caiso-120/121);
   surplus-regime import pricing is the specific defect.
3. **S2: DA/RT two-settlement separation charter** for the evening/overnight
   storage spread (caiso-129's only surviving candidate; a real charter, not a
   shaped floor — the S1 family is DO-NOT-REDO).
4. **`tranche_startup_amortization`** — untested; evening-ramp start economics.
5. **`unit_outage_short_windows` / `unit_partial_outage_windows`** — derive
   for CAISO (currently MISO/PJM-only artifacts); cheap availability-grain
   test.
6. **`measured_ct_heat_rates`** — CT priced-out finding (caiso-119) and the
   CHP miscosting (caiso-128) both point at offer-cost inputs; measured loaded
   HRs are the audit-grade first step.

### 5.3 PJM — targets C1 CC_REGULAR-2023, C3a-2025, C3c-24/25

1. **`pjm_dam_availability`** — the intaken-but-untested measured availability
   re-basis (2018–2026 data landed 2026-07-24, ships default-off). Directly
   at C1 CC_REGULAR volume and the outage-envelope story.
2. **Dominion CT/CC zonal inversion** (pjm-134 ask): first lever =
   **`measured_ct_heat_rates`** on PJM's CT fleet (the measured-offer-surface
   family provably cannot reach it — pjm-132 gives Dominion identical values).
3. **G-20b guard false-negative lead** (~2.8–5.0 GW returned capacity per
   tight hour) — the SUSPECT-grade reserve-supply tightness lead; audit before
   any new mechanism.
4. **`st_gas_mustrun_p25_level`** (MISO form) — re-ground the six overnight
   ST_GAS floor limbs on measured operating levels (D-2 ST_GAS 44–55% forced).
5. **Requirement-side dynamic reserves** (NYISO form, measured as-enforced
   hourly requirement) — the supply side is adjudicated; the requirement side
   is not.
6. **TETCO-M3 winter daily citygate** (MISO `winter_citygate_daily` form) —
   winter C3a shape candidate, own hub derivation.

### 5.4 MISO — targets C7 COAL_PRB (non-ledgerable), C3b spread compression (instrument-blocked), C3a-2024

1. **Coal minimum-take LP constraint** (the named miso-96 successor lane; NOT
   built): contract-period tonnage constraint priced by its dual, replacing
   the take-or-pay discount's cycling side-effect. Multi-session; the only
   identified route to C7 COAL_PRB that doesn't break C1/C5a.
2. **Outage-grain data ask** (`miso-outage-grain-data-ask-2026-07.md`) — the
   C3b driver (~10 GW 2025 summer under-derate) is instrument-blocked; the
   lever is data intake at unit/fuel grain, not a model change.
3. **DA virtual depth** (`pjm_da_virtual_bids` form, own derivation) — the
   diurnal-spread compression (model reproduces 29–47% of observed
   peak-minus-night spread) is a DA-formation signature; untested.
4. **`measured_ct_heat_rates`** — audit-grade.
5. **`dual_fuel_switching`** — winter-event pricing candidate (Elliott-class),
   untested in MISO.
6. **`hydro_budget_nameplate_aware`** + the `NG: PS` pin audit — small fleet,
   cheap, closes a flagged cross-ISO exposure.

### 5.5 NYISO — target: C3c (sole blocker, roof-blocked)

The J/K-commitment and reserve-tier routes are closed IN FULL (nyiso-83/84);
the tail is blocked by an SRMC roof (~$258 mainland). nyiso-92 dated the
actual RT tail: it is **summer** (2025 Jun 23–25 alone = 18 of 42 h; the
Jan-2024 storm produced zero >$300 hours), so the winter-fuel lane caps out
at ~4–5 h/yr and the queue stays offer/DA-side:

1. ~~**DA virtual depth / DA demand formation** (`pjm_da_virtual_bids` form,
   NYISO derivation).~~ **CLOSED 2026-07-28 (nyiso-94): REFUSED ex-ante, no
   solve.** PJM's lever is admissible because `hrl_da_incs_decs` is the
   **submitted** curve; NYISO publishes no submitted-curve equivalent. Four
   independent blockers: (a) P-59 `zonalBidLoad` carries **no price axis** — one
   MW per zone-hour, so `net(λ)` needs an assumed price distribution = a fitted
   scalar (rule 21); (b) those columns are **cleared, not submitted** — they
   reproduce the IMM's published cleared MW/h to within 1–2 MW (rule 13), and
   the priced P-27 masked archive cannot separate virtual from physical
   price-capped load; (c) the **premise is false here** — net virtual is
   *negative* in the mean hour (−230/−186/−277 MW) and only +580/+293/+917 MW
   in the measured tail vs PJM's +7–11 GW, with NYISO's whole DA book ~0.85 GW
   *below* RT load (IMM: DA net scheduled load ≈96 % of actual peak load);
   (d) **roof-blocked** — all five mainland zones share one max dual
   (149.9/194.5/255.1), 0 h >$258, zero load-shed slack, and every model >$300
   hour is Long Island. **Successor lever identified — see item 1b.**
   Evidence: `docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md`.
1b. **TSA (Thunderstorm Alert) downstate transfer derate** — *the recommended
   new queue head, data-intake first.* NYSRC rules make NYISO pre-secure the
   ConEd system as if the first contingency occurred, cutting upstate→downstate
   transfer capability **1–2 GW, real-time only, never in the DA market**
   (2025 SOM §D). It fires in **hours 13–21, May–September** — exactly where
   nyiso-92 dated the tail — and on >26 GW peak-load days costs **$300–500/MWh**,
   with 50 of 1,377 hours carrying 99 % of the cost. The model has no TSA
   representation and prices `Lower_Hudson − Upstate_West` at **$0.0** in the
   measured tail hours, i.e. no downstate congestion at all where NYISO says it
   is most expensive. A weather-driven interface derate is rule-13 admissible
   (physical availability event, forward-reproducible — the IMM built its own
   forecast from public weather data). Caveats: needs a TSA-history intake that
   does not exist in-repo, and must be argued on the **RT** side.
2. **CT start-frequency lane** (nyiso-89 successor): model starts the CT fleet
   2–5× less often than measured; 50–68% of measured CT energy clears below
   its own SRMC — candidates are start-economics (see 3) and DA-award
   commitment, NOT heat rates (eliminated).
3. **`tranche_startup_amortization`** — start-cost amortization changes
   marginal start economics directly at the start-frequency gap; untested.
4. **`nyiso_iroquois_winter_spread` re-arm** — decisive winter fix, but ONLY
   jointly with a summer scarcity lever (its construction conserves the annual
   spread; re-arming alone just moves the miss to summer — adjudicated).
5. ~~**`unit_outage_short_windows`** — derive for NYISO; cheap grain test.~~
   **CLOSED 2026-07-28 (nyiso-93): INERT ex-ante, no solve.** The detector is
   coal-only and NYISO has no coal — 0 coal unit-years in NY+NJ CAMPD 2023-25
   (last NY coal MWh: Somerset/Kintigh 2020), 0.0 MW COAL `plant_group` in the
   model fleet; both extracts derive to 0 rows and both overlays return empty
   dicts. A gas-CC scope extension is the only path to a binding window here
   and needs its own charter (layup confound).
   `docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md`.
6. **`st_gas_mustrun_p25_level`** — re-ground the in-city ST_GAS persistent
   bases on measured levels (D-2 ST_GAS 31% forced in 2024).

Dispatch-matching lane (hourly r, opened by the nyiso-92 charter; the hydro
capability envelope/floor pair is now the keeper — cells K above):

7. **`nuclear_unit_availability`** (NYISO derivation) — nuclear r_day drops
   0.84 → 0.50/0.51 in 2024–25 (refuel/outage timing) on 26–28 TWh; the
   ISO-generic engine exists (ERCOT keeper). Mind the PJM NRC-overlay
   provenance-gate failure before choosing the source.
8. **`hydro_ror_split` NYISO classifier review** — blocked on answering the
   Robert Moses Niagara hybrid label (Run-of-river/Peaking, 52% of fleet MW)
   from the treaty scenic-flow schedule; never arm on the CAISO-reviewed rule
   alone.
9. **Import hourly shape** (nyiso-86 §3): r_hr 0.45–0.61 after nyiso-92's
   side-effect improvement; still the third-largest mistracking component.
10. **Keeper-lineage cleanup:** drop `dual_fuel_oil_reattribution` from the
    NYISO recipe metas (CLI already pins it NEISO-only; zero dispatch delta,
    removes a known recording-basis artifact from the sidecars).

### 5.6 NEISO — target: C3c (ledgered; FRONTIER DECLARED — charter required first)

Frontier discipline: every named admissible mechanism in the winter/summer
scarcity family is already on record. Anything below needs its **own new
charter with a new measured identification** before a solve:

1. **DA-bid offer formation / DA depth charter** (`pjm_da_virtual_bids` form)
   — the named "new identification" class in the frontier note (oil-parity /
   import / DA-bid); NEISO publishes DA cleared/bid data to derive from.
2. **Import-side scarcity identification** (HQ/NB tie behavior in tight
   hours) — second named class.
3. **`measured_ct_heat_rates`** — audit-grade, no charter needed (input
   accuracy, not a scarcity mechanism).
4. **`hydro_budget_nameplate_aware`** + `NG: PS` pin audit — cheap, flagged.
5. **STEP 3 seam disposition** (owner decision pending): carry the
   layup-vs-outage seam explicitly (recommendation (b) on record).

### 5.7 Cross-cutting audits (not ISO levers)

- Post-guard re-derivation sweep of outage-derived artifacts, all six ISOs
  (flagged in governance.md 2026-07-26, unaudited).
- `NG: PS` hydro-pin audit (PJM disclosed; every hydro BA to check).
- `thermal_tranches_<ISO>.csv` provenance re-derivation (blocked at HEAD,
  miso-95).
- Registry hygiene fixes from §4.6 (dangling `--ramp-limits`, inert-default
  flags).
- Forecast-lane inheritance review: for each keeper-only `BF` mechanism,
  decide arm-in-forecast vs G4 forward-analogue vs backcast-only, and record
  it in the row's `fc` field (start: CAISO `capacity_deliverability_limits`
  part (a)).

## 6. Glossary

The full grouped glossary (≈80 terms: LP/duals, gates C1–C8 and
D-diagnostics, ORDC/RCPF/ASDC, commitment bridges and floor limbs, offer
tranches and passthrough sigmoids, EFOR/WEFOR, TTC/GTC/seams, ELCC/PRM/
net-CONE/VRR, RPS/REC/ACP, CAMPD/CEMS/eGRID/EIA-923/930/860, …) is rendered
with search on the matrix page: `docs/codebase-site/mechanism-matrix.html#glossary`.
It is maintained there (single source); this doc deliberately does not
duplicate it.

---

*Maintenance: this doc changes when the protocol or queues change; the matrix
data file changes every time a verdict lands. If they disagree, the data file
(+ the calibration log it cites) wins — fix this doc.*
