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

0. **Coal tranche-1 take-or-pay REPRICE — pre-registered, OWNER-BLOCKED, and now
   the best-identified coal lever.** `docs/PRECOMMIT-ercot136-coal-minload-reprice-2026-07-29.md`.
   ERCOT-136 read the SCED TPO instrument and settled the standing
   self-scheduled/withheld/telemetered-down fork: **none of the three** — the
   unoffered-in-DAM block is offered economically in RT at \$8–25/MWh, so the
   "a near-zero bid is faithful" escape is refuted and a coal offer-SHAPE
   correction is licensed for the first time. The lever is a **single existing
   registered scalar** (`coal_tranche_1_fuel_passthrough`, 0.00 → measured), it
   **retires a fitted value** rather than adding one, and it is rule-19-clean
   because the block is already floored twice (`ercot_coal_min_config_floor` +
   `coal_mustrun_per_plant`). **Blocked on the same ERCOT-116 adoption ruling**
   (rule 14: an offer-curve change cannot move a pinned block). Do NOT re-derive
   the identification — it is measured and committed
   (`results/calibration/ercot136_coal_headroom_conduct.json`). It **supersedes**
   the ERCOT-135 width arm (wrong instrument, wrong level by ~\$4–5).
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

### 5.3 PJM — **NO failing criterion** (keeper `2026-07-29-pjm-137-ctheatrate`, CALIBRATED)

C1 CC_REGULAR-2023 and C3a-2025 closed at pjm-135; **C3c-24/25 closed at
pjm-136** and is UNCHANGED by pjm-137. The queue below is not gate-driven — it
is ranked by *structural* defect, per rule 1 `[R-STRUCT]`.

**CLOSED AT pjm-137, binding on successors — do not re-open:**

- **The zonal-congestion route to the Dominion CT leg.** PJM's own day-ahead
  binding-constraint record (new intake `data/raw/pjm-binding-constraints/`,
  228,795 constraint-hours) puts only **6.34 / 3.06 / 6.19 %** of its congestion
  rent on a named zonal-scale interface and **80.0–87.8 %** on monitored
  facilities rated ≤ 230 kV; **`AEP-DOM` carries 0.041 / 0.071 / 0.236 %**. The
  constraints that dominate the DOM-separation hours are PLEASNTV TX3 500 kV,
  GOOSECRE TX1 500 kV, PLEASNTV-ASHBURN 230 kV, ASHBURN-GOOSECRE 230 kV and
  BRAMBLET-EVRGREEN — every one `zone = DOM` in PJM's own pnode registry, i.e.
  **both ends inside `PJM_Dominion`**. PJM's 500 kV EHV nodes (new intake
  `data/raw/pjm-ehv-lmp/`) measure **more** dispersion inside Dominion
  ($6.18/$8.68/$16.78) than across the whole DOM–AEP boundary
  ($4.76/$6.13/$14.42). This is the ERCOT/MISO `internal_congestion_split`
  refusal class. **No successor may propose another zonal congestion mechanism
  for this defect.**
- **`measured_ct_heat_rates` → K** (pjm-137 keeper). Adjudicated on PJM's own
  artifact; see the matrix cell.

**The queue:**

1. **The system-energy-price half of the Dominion CT deficit — the successor's
   target.** In the hours Dominion's real turbines run, the model's zonal price
   is **$17.72 / $26.69 / $54.61 /MWh** short; netting the measured congestion
   component out leaves **$8.63 / $14.37 / $26.88** (49 / 54 / 49 %) that a
   zonal model *could* produce. Measured DOM **MEC** alone runs at a p50 of
   $35.94 / $41.35 / **$58.86** in those hours against the model's whole
   Dominion dual at $32.07 / $32.28 / **$42.72**. This is an ISO-wide
   marginal-unit question and it joins item 5 below.
2. **The defect is ~1.9× smaller than every prior note said.** The Dominion
   `CT_PEAKER` actual is **3.066 / 4.048 / 5.218 TWh** on the benchmark's own
   unit-split per-plant record — not the 7.38 / 8.68 / 9.64 carried forward,
   which is the nine roster plants' *whole-plant* energy and counts Doswell's
   combined-cycle blocks as peaker output. After pjm-137 the gap is
   **−2.345 / −2.600 / −2.056 TWh**, i.e. the model is at **24 / 36 / 61 %** of
   actual. Take a zonal class actual from
   `frontend/data/backcast/bench/<ISO>/<year>.json.gz` (which carries
   `split: "unit_hourly"` at mixed sites), never by summing CAMPD over a plant
   roster.
3. **A `PJM_Dominion` NoVA/Loudoun split** is the structurally correct fix and
   is **blocked on one measured input**: PJM's metered-load feed stops at the
   transmission zone, so a sub-zonal load share would be a fitted scalar
   (rules 5/24). Refused until a measured sub-zonal load basis exists.
4. **C8 `CT_PEAKER` forced share** rose to 16.3 / 16.9 / 17.1 % at pjm-137 (all
   GROUNDED — D-4 clear, profile r 0.923–0.973, CV ratio 0.703–1.083) on a class
   whose ISO-wide volume fell 2.6–2.9 TWh. A clean pass under rule 20, but worth
   watching.
5. **G-20b guard false-negative lead — now PRICED, and the price is material.**
   pjm-138 §4.2 sized what
   `FINDING-guard-falseneg-audit-2026-07-27` §7 said no instrument could:
   removing the guard's own 2.8–5.0 GW from the tightest decile's offer stack
   moves the clearing price **+$4–23/MWh** on the mean (3 GW: +$3.97 / +$8.02 /
   +$14.95; 5 GW: +$7.45 / +$12.46 / +$23.36), i.e. **28–59 %** of that decile's
   system-energy gap, as a LOWER bound. The **verdict is unchanged** — that
   audit's D2 population test is clean 3/3 for PJM and its D3 exceedance is
   mostly a window-LENGTH effect — so this is a change of stakes, not of
   evidence. Route stays its §7.2: a within-window tight-hour treatment memo,
   owner sign-off, its own charter, LOYO within 2023–2025. **Do not arm anything
   on the price alone.**
6. **C3c margin** — still passes by **1 h** (2024) and **2.5 h** (2025) against a
   0.5× floor, untouched by pjm-137 and by pjm-138 (which solved nothing). Any
   delta must report its C3c effect explicitly.
7. **`pjm_dam_availability`** (**U**) — intaken but untested. pjm-137 measured
   that Dominion's real turbines are synchronised in 68.3 / 54.4 / 62.4 % of all
   hours, so the CT leg is **not** an availability defect; this lever now stands
   on the outage-envelope story alone. Note the ERCOT precedent before
   chartering it: the measured envelope there is *measured-correct* and was
   rejected twice on level (ERCOT-116/134).
8. **`st_gas_mustrun_p25_level`** (**U**, MISO form) — re-ground the six
   overnight ST_GAS floor limbs on measured operating levels (D-2 ST_GAS
   42–55 % forced). **Newly motivated by pjm-138**: the model runs
   **$1.6–7.3/MWh too DEAR at h01–h04**, worst in 2023, and that over-pricing is
   the one part of the dispersion defect the reserve credit does not touch.
9. **`gas_daily_shape`** (**U**) — measured, mean-preserving HH daily shape,
   never probed on PJM. **pjm-138 makes this the best-identified remaining
   lever**: the largest single cell in its whole measurement is the *winter
   morning ramp* (CT-weighted DJF 2025 **+$46.05/MWh**, h06–h07 the worst hours
   of the day), which is exactly the phenomenon
   `DIAGNOSIS-pjm-dof-scarcity-tail` §B.4.1 named it for — a January merit order
   priced on a flat monthly gas level cannot express the measured intra-month
   cold-snap spike.
10. **TETCO-M3 winter daily citygate** (`winter_citygate_daily` form, **U**) —
    own hub derivation. Same winter-ramp target as item 9; derive PJM's own hub.

**CLOSED AT pjm-138, binding on successors — do not re-open (no LP solved;
`FINDING-pjm138-system-energy-is-reserve-opportunity-cost-2026-07-29.md`):**

- **The RESERVE/SCARCITY route to the Dominion CT leg, and to PJM price
  formation generally.** PJM's own published day-ahead reserve market prices
  synchronized reserve **above zero in 84.2 / 96.7 / 47.6 %** of all hours
  (Primary 45.1 / 64.0 / 30.8 %) at a cover ratio of **1.00–1.11**; the model's
  reserve dual is above zero in **0 / 2 / 28** hours of 8,760. That dormancy
  correlates with the model's system-energy price gap at **r = +0.79 / +0.60 /
  +0.66** and accounts for **82 / 52 / 57 %** of it in the Dominion CT-running
  hours. **It is not a missing mechanism**: the requirement is PJM's own
  measured series, the demand curve is PJM's published two-step ORDC
  (`pjm_ordc_curve.csv`, m11 §4.3.3), and the in-LP per-generator joint-headroom
  co-optimization that is *designed* to price the opportunity cost is armed and
  is its sole owner under rule 19. It clears at $0 because the model's reserve
  supply is 5–10× the requirement — the **LP-vs-MIP boundary** pjm-82 named,
  which the no-MIP mandate makes a **disclosure, not a defect**. The lane was
  owner-closed 2026-07-11 and this measurement confirms that closure on PJM's
  own numbers. **Requirement-side dynamic reserves (the old queue item 9) is
  adjudicated INERT by measurement** and the matrix cell moves `.` → `K`.
- **The size of what is left.** Of the CT-hour price deficit
  (**$17.97 / $26.44 / $54.06**, restated on the corrected hour key), pjm-137
  closed **54.6 / 51.8 / 54.2 %** as intra-zonal congestion and pjm-138
  attributes **37.3 / 25.2 / 26.2 %** to the reserve opportunity cost. **Only
  8.1 / 23.1 / 22.1 % is reachable by any energy-stack mechanism**, and on an
  annual load-weighted basis the model already reproduces PJM's own system
  energy price to **+$0.47 / +$2.62 / +$8.48** — so the residual is a
  *dispersion* defect, not a level one, and any successor lever must raise tight
  hours **without** raising slack ones (the gradient test the measured offer
  surface failed at pjm-123).
- **Keeper root cause (6) — "fitted coal rungs own the $40–150 region the
  measured corpus assigns to the CC top belt and `CT_FAST`" — is CLOSED.** On
  the current keeper's own fleet (no LP), `COAL` is **12.7–18.2 %** of the
  marginal set across all hours and **11.1–17.6 %** in that band, against
  pjm-122's **44–79 %** on the `pjm-121` bundle; `CC_REGULAR` + `CT_PEAKER` hold
  **68.4 / 72.6 / 75.5 %** of it and `CT_PEAKER` alone is **60.7 / 65.9 /
  67.1 %** of the tightest net-load decile. The intervening keeper line (CC
  mid-curve belt, net-position cut, loss surface, measured CT heat rates) is the
  plausible cause. It should be retired from `keepers/PJM.json` — a
  promotion-lane edit pjm-138 reports rather than performs.
- **An hour-key correction to pjm-137's shape statistics.** Its measured-side
  loader indexes on Eastern *Prevailing* time against a model and a CAMPD record
  that are both Eastern *Standard*. Levels move ≤ $0.38/MWh and every pjm-137
  conclusion stands, but **no diurnal statistic may be quoted from
  `_pjm137_dominion_ct_congestion.py`** — use `_pjm138_mec_gap_shape.py`'s
  UTC-keyed loader.

**Representation limits, measured at pjm-137 and ISO-wide (not EMAAC-only):**
intra-zone EHV dispersion in 2025 runs **West_APS $18.58, Dominion $16.78,
Central_PA $12.38, AEP_Ohio $9.40, SWMAAC $7.35** against an inter-zonal
DOM–AEP spread of $14.42 — six of seven measurable model zones carry as much
separation inside them as the model is chartered to reproduce between them.
ComEd ($1.93) is the exception, which is why pjm-136 §3's hub-based test read
clean: PJM publishes multiple hubs only inside its two most internally-uniform
zones. The external star node remains lossless while internal wheeling pays a
loss.

### 5.4 MISO — targets C7 COAL_PRB (non-ledgerable), C3b spread compression (instrument-blocked), C3a-2024

1. **Coal minimum-take tonnage data ask**
   (`miso-coal-contract-tonnage-data-ask-2026-07.md`) — **the LP constraint is
   NOT the lever any more; the RHS is.** The constraint itself (contract-period
   tonnage priced by its dual, the named miso-96 successor) stays the only
   identified route to C7 COAL_PRB that doesn't break C1/C5a, but miso-103
   adjudicated its only forward-regenerable RHS candidate — receipts-derived
   tonnage in any window/lag/smoothing — inadmissible (log R² 0.87–0.94 vs
   same-year burn), and miso-104's sourcing pass found **no** ex-ante
   contractual series at plant grain across the 39-plant target set for
   2023–2025. Do NOT charter the constraint until a source clears that ask's
   §4; do NOT re-test any receipts variant. Bounded next step is the ask's §8
   Form 580 count, not a solve.
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
at ~4–5 h/yr and the queue stays offer/DA-side.

**THE C3c QUEUE IS NOW EMPTY (2026-07-29, nyiso-96/97).** Every candidate is
adjudicated: items 1/1b closed ex-ante on identification (nyiso-94/95), item 2
characterised and item 3 tested by nyiso-96 (verdict commitment/obligation, not
start economics; the amortization arm adjudicated R on rule 1, then
owner-promoted to keeper 2026-07-29 for its C1 PASS with the CT_PEAKER trade on
the record), and the last surviving candidate — **SCUC load-pocket security
commitment + BPCG (NYC/LI sub-zonal)** — closed **ex-ante, no solve** by
nyiso-97: the owner authorized sub-zonal scoping data-first, and identification
failed on *content*, not only access (the as-enforced AORR is MyNYISO-walled;
the public 2008-vintage Appendix B carries no derivable NYC parameter — every
Con Ed in-city commitment row is condition-triggered on TO contingency analysis
with parameters in unpublished SO procedures). **NYISO C3c is recorded as a
DIAGNOSED, UNCLOSED structural limitation of the five-zone representation**
(`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`, re-open
conditions §5). Remaining live NYISO work is the dispatch-matching lane (items
7–10) and the D-2 hygiene item 6; item 4 stays blocked on its joint-lever
condition.

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
1b. ~~**TSA (Thunderstorm Alert) downstate transfer derate.**~~ **CLOSED
   2026-07-28 (nyiso-95): REFUSED ex-ante, no solve.** The event set was never
   the problem — and two premises in the original queue entry were wrong, both
   in the model's favour. (i) A TSA history **does** exist in-repo: MIS **P-35
   Real-Time Events**, intaken 2026-07-10 under owner authorization, clean
   datatype `nyiso-operating-events` (`event_type=thunderstorm_alert`);
   reconstructed windows 32/30/18 spans = 187/272/477 h, h13–21 share 61/55/42 %,
   May–Sep 75/90/97 % — independently corroborating the IMM's stated window.
   (ii) The model **already** represents TSA's one published, quantified
   consequence: the LRR `tsa_reduced_to_zero` rule feeds
   `derive_nyiso_reserve_requirements_hourly.py::build_tsa_windows` →
   `nyiso_dynamic_reserve_requirements`, **armed on the nyiso-92 keeper**.
   What is unidentifiable is the **magnitude**. (a) It is **not in the published
   limits**: a declaration-instant event study on MIS P-32 across all 18
   interfaces (83 pooled starts) gives **exactly +0.0 MW** on SPR/DUN-SOUTH and
   TOTAL EAST (0 % of events |Δ|>100 MW) and **−23.9 MW** on UPNY CONED (median
   exactly 0.0 every year) — against a feed that resolves 835–1,565 MW
   hour-over-hour steps, so the null is well-powered. (b) The SOM's "1–2 GW" is
   defined *"relative to day-ahead scheduled levels"* — a range, not a rating;
   selecting a point inside it and scoring it on C3c **is** the fitted scalar
   (rules 21/5). (c) It sits **off our boundary** — the constraint carrying 71 %
   of July-2025 TSA uplift is the **Lovett-Buchanan 345 kV** line under
   multi-contingency **CE40**, which the IMM explicitly distinguishes from the
   UPNY-Con Ed interface; it is one of six parallel paths our five-zone network
   collapses into one link (rule 14's named misalignment clause), and
   reconciling it needs ratings/OTDFs NYISO does not publish. (d) Even the IMM
   has **no magnitude model** — Appendix III.J predicts *P(occurrence)* only.
   The one real measured signal (DiD flow response at onset: UPNY CONED
   −57/−412/−326 MW, SPR/DUN-SOUTH −36/−330/−279 MW, CENTRAL EAST placebo n.s.)
   is a **validation target, never an input** (rule 13) — and at ~280–410 MW it
   is ~¼ of the IMM's low end, confirming the 1–2 GW is mostly the **DA-vs-RT
   schedule gap**, which has no analogue in a formulation with no DA/RT split.
   Evidence: `docs/FINDING-nyiso95-tsa-derate-not-identifiable-2026-07-28.md`.
2. ~~**CT start-frequency lane** (nyiso-89 successor).~~ **CLOSED 2026-07-29
   (nyiso-96 characterisation + nyiso-97 identification).** The
   characterisation chose the commitment/obligation family over start
   economics (below-SRMC energy spread FLAT; 82–88 % of missing online-hours
   priced below the plant's own SRMC; run lengths already right — start COUNT
   is the defect), every commitment-side candidate is adjudicated
   (nyiso-83/84/90/91), and the surviving load-pocket candidate died on
   identification (nyiso-97). The defect is carried on the nyiso-96 keeper
   attestation as an owner-accepted misrepresentation (`_open_items (0)`).
3. ~~**`tranche_startup_amortization`**~~ **TESTED 2026-07-29 (nyiso-96,
   registered A/B): adjudicated R on rule 1 (C1 flips to PASS but CT_PEAKER
   degrades 27–39 % and C3c is bit-unchanged), then OWNER-PROMOTED to keeper
   the same day for the C1 PASS with the trade on the record (cell K;
   keeper `2026-07-29-nyiso-96-ctamort`). Do not re-test; do not read the
   cell K as a structural endorsement — the finding's §5 adjudication
   stands.**
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

7. ~~**`nuclear_unit_availability`** (NYISO derivation).~~ **TESTED 2026-07-29
   (nyiso-98, registered A/B): all gates PASS — cell K, OWNER-PROMOTED to
   keeper `2026-07-29-nyiso-98-nucavail` the same day.**
   **The queue entry's own premise was wrong.** "r_day drops 0.84 → 0.50/0.51
   in 2024–25" is scored against EIA-930 `NYIS` `NG: NUC`, which posts exactly
   0.0 MW in contiguous blocks (1,179 h 2023 / 380 h 2024 / 117 h 2025 — zeros
   in the source parquet, not NaN). Falsified against NRC on **all 81 gap days,
   zero survivors**: every one has ≥1 NY reactor at 100 % licensed thermal
   power. Gap-masked the ordering **inverts** — 0.446/0.833/0.534, so **2023 is
   the worst year** and the "2024–25 drop" does not exist as described. (Same
   artifact: nyiso-92's 2023 nuclear level reads +14.5 % over-produced; clean
   it is −2.1 %.) Target re-based onto gap-clean r_day in the pre-registration
   **before** the arm was built. The PJM failure mode does **not** repeat, for
   the pre-registered reason: PJM's target was the *level at near-full pool
   days* (what the 923 anchor moves), NYISO's is *within-month timing* (what it
   preserves). Build-time gates: G1 raw-NRC lift **+0.304** (≥ +0.10), G2
   reconciled retention **104 %** (≥ 70 %; PJM's was negative), G3 max annual
   |ΔTWh| **0.14 %** (< 0.5 %). In-solve: gap-clean r_day **0.446/0.833/0.534 →
   0.885/0.960/0.917**, r_hr 0.418/0.819/0.502 → 0.834/0.941/0.836, every
   criterion verdict identical to the same-HEAD zero-delta control. Reported
   adverse (rule 14, not patched): 2023 `CC_REGULAR` −2.76 → −2.79 of ±2.94,
   in band. Zero fitted scalars.
   `docs/FINDING-nyiso98-nuclear-availability-2026-07-29.md`.
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
