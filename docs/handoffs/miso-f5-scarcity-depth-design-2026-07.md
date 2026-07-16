# MISO F5 scarcity-depth lane — declared-window ELMP emergency-tier pricing (frozen design)

**Date:** 2026-07-16. **Session:** `claude/busy-bell-k7jkhf` (Fable, rule 27).
**Parent contract:** `docs/handoffs/miso-price-formation-design-2026-07.md`
(§5/F5 — triggered 2026-07-16 by the miso-69 probe verdict) +
`docs/handoffs/miso-maxgen-registry-findings-2026-07.md` §5 (the measured
basis). **Run number:** miso-70. This document is the Phase-A freeze: the
mechanism, every parameter with its citation, the composition plan, the
pre-registered expected-delta bands, and the refutation criteria are all
committed HERE, before any build or solve. Nothing below is tuned to a
residual; the two $ parameters are verbatim tariff/SOM values and the windows,
levels and regions are the M-1 registry's rows (F4 — never reconstructed from
prices).

## 0. State verified at session start (2026-07-16)

- MISO keeper = `2026-07-16-miso-68-mothballs`, NOT-YET, fail set
  {C1 CC_REGULAR-2023 −8.28, C3a-2025 −14.3%, C3c RT 0/30 · 4/37 · 0/88};
  C3b PASS 0.081/0.124/0.193; DOF 21/2 — matches the F5 charter exactly.
- miso-69 (`2026-07-16-miso-69-maxgen` + `-base`) registered REJECTED PROBE;
  its branch merged to main (PR #2352); M-2 built/tested/default-off.
- RT actual tail (v2.7 gate basis): 30/37/88 hours > $200 for 2023/2024/2025;
  PASS bands [15,60] / [18.5,74] / [44,176] (0.5×–2×).
- Box: 15.1 GB MemAvailable → per-year + `--reuse-solved` orchestration is
  mandatory (parent design §8); years always sequential (rule 12).

## 1. The mechanism: `maxgen_emergency_tier_pricing` (ScenarioConfig bool, tier 3, default OFF)

### 1a. The measured physics (primary text, archived PDFs in `data/raw/MISO/`)

The 2023 SOM (Report Body p.10-11) defines the pricing/capacity effect of each
rung of MISO's emergency ladder:

> "Alert: allows 4-hour online resources to set price in ELMP. Warning: Tier 1
> emergency pricing in ELMP, curtail non-firm exports, call external capacity
> resources to import. Step 1: a) can commit emergency only units, b) activate
> emergency output ranges in the real-time dispatch (instantly available).
> Step 2: a) Tier 2 pricing and LMRs available, b) emergency DR, c) emergency
> energy purchases from neighbors. Steps 3-5: Raise priority of transaction
> curtailments, call reserves from reserve sharing group, shed firm load."
>
> "With the exception of the Alert, each of these emergency levels increases
> the supply-demand margin by increasing supply or decreasing demand."

The tier prices are footnoted identically in all three SOMs (2023 fn.21 = 2024
fn.17 = 2025 fn.17):

> "Emergency supply is priced by applying a $500/MWh offer price floor
> (Tier 1) to this supply in ELMP when MISO declares a Max Gen Warning and a
> $1000/MWh floor (Tier 2) in a Max Gen Event Step 2."

The 2024 SOM (p.15) gives the one measured within-window read: the
Aug-26-2024 Warning (13:00-20:00 EST) "trigger[ed] Tier 0 and Tier 1 emergency
pricing. Tier 0 and Tier 1 pricing allows 4-hour GTs and emergency MW to set
prices in ELMP, respectively. MISO's Tier 0 pricing increased prices by an
average of $60 per MWh during the Warning" — actual RT peaked ~$206 that
afternoon (bench hourly record), DA $169.

So MISO's declared-window prices are formed by a **bounded administrative
supply ladder priced at tier offer floors**, not by riding the reserve demand
curve into its deep steps: while a Warning's Tier-1 actions (emergency ranges,
external capacity, export curtailment) hold the margin, the marginal
emergency MW is priced at $500 — the $1,100/$3,300 zonal-ORDC steps and the
RBDC's deep ramp never become the price. That is exactly the two-sided miso-69
finding: with the measured 10.67 GW removed, the model — which has NO tier
supply — priced the 7-hour Aug-2024 Warning at the ~$2,000 slack cap
($1,840-1,985 for 6 straight hours vs actual $169 DA / $206 RT), while the
deep 2025 windows did nothing because the price-formation element that turns
declared-window stress into $200-450 prices is not depth alone.

### 1b. The in-LP representation (rule 19: reconciled with the RDC, nothing stacked)

**In backcast mode, for every model zone-hour inside a registry window whose
declared level is Maximum Generation Warning or higher, the energy-balance
load-slack cost is `min(iso_config.voll, tier_floor(level))`.** Everywhere
else it stays `iso_config.voll` (MISO: the $2,000 FERC Order 831 bid cap) —
bytes unchanged.

Semantics: the LP's load slack IS its administrative supply of last resort.
The SOM says declared emergency levels *increase supply* and that this
emergency supply is *priced in ELMP at the tier's offer floor*. Repricing the
slack from the bid cap to the declared tier's floor inside the declared
window is precisely that statement in LP form: an (unbounded) emergency
supply tranche at the tier floor, entering the energy balance of the declared
region's zones, marginal only in hours whose counterfactual marginal cost
exceeds the floor. LMP in a clamped hour prints the tier floor — the
documented formation — instead of the $1,841-1,985 slack-cap ride.

Why this reconciles with (and does not stack on) the in-LP RDC family:

- **No reserve-family constant, step, width, or requirement is touched.** The
  market-wide RBDC ($3,500 Schedule 28 anchor) and the South zonal ORDC
  ($200/$1,100/$3,300, BPM-002 §5.2.1.2) remain THE scarcity mechanism, and
  §2c of the parent design (no VOLL/ORDC constant change pre-9/30/2025)
  is untouched — the tier treatment only *lowers* the effective in-window
  energy-side cap; it never edits the published curves.
- **One supply, no dual stacking.** Emergency MW in the real market serves
  energy and thereby frees real units for reserve. A slack-side tranche does
  the same by displacement: with supply available at $500, the energy dual is
  bounded at ~$500 and the LP frees real headroom toward the reserve
  requirement, so nested reserve families cannot stack their clamped duals
  into the LMP (which a per-family ORDC-step clamp WOULD have done — two
  families clamped at $500 each could still stack $1,000 into the energy
  dual; that representation is considered and rejected for exactly this
  reason).
- **Post-solve overlays stay off** (parent §7: MISO scarcity is in-LP only).
  This is not an overlay: it is inside the LP, changes the optimum, and the
  duals ARE the prices (rule 4).

### 1c. Level keying (all cited; the registry's `level` column is the key)

| declared level (registry vocabulary) | pricing effect in-LP | citation |
|---|---|---|
| `capacity_advisory` | none | 2023 SOM p.10-11 ladder: advisory/alert add no margin |
| `maxgen_alert` | none | "Alert: allows 4-hour online resources to set price in ELMP" — a price-FORMATION relaxation with no margin change. A pure LP has no commitment integralities: every online resource's offer already sets the dual, so the Alert/Tier-0 treatment is LP-native and building it would double-count. The measured +$60 Tier-0 effect (2024 SOM p.15) is deliberately NOT an adder (a fitted adder is forbidden, rule 1). |
| `maxgen_warning` | slack cost = min(voll, **$500**) | Tier 1 floor, SOM fn (2023 fn.21/2024+2025 fn.17) |
| `maxgen_event_step1` | slack cost = min(voll, **$500**) | Step 1 "commits emergency only units / activates emergency output ranges" — more Tier-1 MW, no new pricing tier; Tier 2 arrives only at Step 2 (2023 SOM p.10 ladder) |
| `maxgen_event_step2`..`step5` | slack cost = min(voll, **$1,000**) | Tier 2 floor, same footnote. Steps 3-5 add non-pricing actions (curtailment priority, reserve sharing, firm load shed); the emergency-supply offer floor stays Tier 2 while firm load shed itself remains priced at the ISO cap — no step3+ row exists in the registry, so this clause is vocabulary-complete but currently unreachable. |

Overlapping active Warning+ rows on the same zone-hour take the MINIMUM floor
(the cheapest active emergency tier is the marginal one). No such overlap
exists in the current registry — deterministic tie rule, not a live branch.

Region scoping = the M-2 deriver's crosswalk (`_zone_in_region`) restricted
to the **physical** zones: `footprint` → all 6 MISO zones; `midwest` → all
except MISO-South; `south` → MISO-South. *(Amended during implementation,
2026-07-16, before any scored read: the LP's zone list also carries the
external seam buses — `MISO_external` / `MISO_external_South` — which the
first launch's footprint rows swept in, 8 zones repriced. Load slack at an
external bus is phantom import supply through the border links, so a tier
floor there would fabricate unmeasured emergency imports and bypass the
measured seam ladders; in a backcast the Tier-1 "call external capacity
resources" leg is already inside the measured interchange. External buses
are therefore outside every declared region by construction — the partial
first launch was killed and re-run with the fix; no probe verdict was read
from the 8-zone arm.)* Hour masks = `outages.outage_hour_mask` — the SAME
half-open, no-leap (8760) model-clock convention the M-2 derates use, EST
(Etc/GMT+5) year-round per MISO Tariff Module A, so the tier windows and the
M-2 derate windows are hour-exact aligned by construction.

Active rows for the 2023-2025 window (from `data/raw/maxgen-events/miso/miso.csv`):

| row | level | region | tier floor |
|---|---|---|---|
| 2023-08-24 12:00→24:00 EST | maxgen_event_step2 | footprint | $1,000 |
| 2024-08-26 13:00→20:00 EST | maxgen_warning | footprint | $500 |
| 2025-06-23 00:00→24:00 EST | maxgen_event_step1 | midwest | $500 |
| 2025-06-24 00:00→24:00 EST | maxgen_warning | midwest | $500 |
| 2025-07-29 00:00→24:00 EST | maxgen_warning | footprint | $500 |

(The four advisory/alert rows — Aug-22-24-2023 alert, Jul-24-2025 advisory,
Jul-28/29-2025 advisory, Jul-28-2025 alert — carry NO pricing effect. In
particular the model's one 2025 tail hour, Jul-28 19:00 EST at $247.7, sits
under Alert+Advisory only and is untouched by this mechanism.)

### 1d. Parameters and DOF

Two $ constants, both verbatim primary values, to live in
`config/reserve_config.py` beside the ORDC constants with the SOM citation:
`MISO_EMERGENCY_TIER1_OFFER_FLOOR = 500.0`,
`MISO_EMERGENCY_TIER2_OFFER_FLOOR = 1000.0`. Zero MW parameters: the tranche
is depth-unbounded within the declared window. Identification for the
unbounded depth is the ladder's own revelation discipline — "MISO should only
declare each level of declaration when the additional MWs available in that
level of emergency will be needed to avoid an operating reserve shortage"
(2023 SOM p.11): a Warning that never escalated to Step 1/2 reveals Tier-1
margin sufficed at $500; a Step-2 declaration reveals Tier-1 exhausted and
prices the margin at $1,000. The declared level IS the measured depth
indicator, so no per-window MW bound is fitted (none exists to intake — the
SOMs report event-level emergency energy only sporadically, e.g. 565 MW
Jun-23-2025).

DOF ledger: **+1 measured-physical entry** on the miso-69 stack (the
tier-floor schedule; the registry windows/levels are already ledgered by the
M-1/M-2 entries) → expected main 24/2, base 21/2.

Rule-12 triple: *driver* = MISO's declared emergency instruments (the same
per-row provenance as M-2) + the SOM-documented tier pricing they trigger;
*window* = exactly the registry windows at Warning+ level (off-window binding
is structurally impossible — the slack cost equals voll outside them by
construction); *forward story* = backcast/calibration overlay (D-5
`backcast_only`), same admissibility family as the CAMPD/M-2 windows: the
registry regenerates from each new declaration vintage; a forecast year
carries no declared windows, and the post-9/30/2025 ER25-579 regime
($10,000 VOLL + LOLP ORDC + $3,500 EDR cap) remains the forecast lane's own
charter (parent §2c) — deliberately not half-built here.

### 1e. What this mechanism deliberately does NOT do

- It does not create engagement. It is a cap on declared-window price
  formation, never a floor: a window hour whose counterfactual price is below
  the tier floor is untouched (the $500 supply is dominated). The deep-2025
  under-engagement (model $196-248 vs actual $327-1,202 RT peaks inside
  declared windows) is a *depth* question owned by the availability truth
  (M-2) and the engagement-side lanes (the Midwest carries no zonal reserve
  family; the market-wide requirement is the measured *cleared* series;
  winter fuel security is its own chartered lane) — each needs its own
  charter and NONE is armed here (rule 19, one mechanism per phenomenon).
- No Tier-0 adder, no ORDC step edit, no VOLL constant change, no post-solve
  overlay, no new congestion mechanism, no Jan/Sep/Dec residual mechanism
  (parent §7 in full).

## 2. Composition plan (design question 2 — pre-declared)

**The deciding probe is the COMPOSITION: miso-68 keeper recipe + M-2
(`unit_outage_maxgen_events=True`) + tier (`maxgen_emergency_tier_pricing=
True`), against a same-box unchanged-recipe base replica.** One new mechanism
is added relative to the already-adjudicated miso-69 pair — the F2
one-mechanism-at-a-time discipline is satisfied by adjudicating the tier-alone
arm analytically:

- **Tier-alone on the keeper stack is provably dispatch-inert — no solve is
  spent on it.** Proof from the committed keeper payload
  (`runs/2026-07-16-miso-68-mothballs.js`, `ordc.hoursGt200` + `lmpDeltaHr`
  reconstruction against the bench RT series, recomputed this session): the
  keeper prints ZERO hours with max zonal dual > $200 in all of 2023 and all
  of 2025, so every Warning+ window hour in those years clears below $200 <
  $500 in every zone, and a $500-priced supply is dominated (the LP optimum
  is unchanged; a tie would need a marginal cost of exactly $500.00 —
  measure-zero). In 2024 the keeper's Aug-26 window hours print $44-50
  ISO-demand-weighted; for any zone to reach $500 with the South's 27% weight
  the weighted mean would exceed $160, so all zones sit far below the floor
  there too (the keeper's 4 tail hours are elsewhere in 2024 and outside any
  Warning+ window — the only 2024 window is those 7 Aug-26 hours). Slack at
  $500/$1,000 never becomes marginal → byte-identical dispatch.
- M-2-alone is already adjudicated (miso-69, REJECTED on the C3b-2024 breach;
  its registered pair stays the M-2-only record).
- The composition is therefore the structural claim under test: *measured
  event-window availability truth (M-2) + documented tier price formation
  (this mechanism) = MISO's declared-window prices*. Both halves are
  measured; neither is fitted.

Cross-run isolation read (pre-registered): if miso-70-base reproduces the
registered keeper exactly on every gated criterion (as miso-69-base did —
zero box drift), then miso-70-main − miso-69-main isolates the tier's
within-composition footprint. Expected: exactly the 6 Aug-2024 window hours
move (~$1.9k → the $500 floor), plus at most re-solve wiggle elsewhere.

## 3. Pre-registered expected-delta bands (design question 4 — committed BEFORE the probe)

All mechanism-only reads are miso-70-main − miso-70-base (same box), never
probe − registered. The C3b-2024 projection below is arithmetic on the
committed miso-69 payload/bench (scorer replicated exactly: main 0.203, base
0.124; the 6 window hours clamped to $500 move the August demand-weighted
monthly mean −11.1 to −14.4 $/MWh depending on within-month demand
weighting), stated as the expectation, not tuned to it.

| read | band | notes |
|---|---|---|
| C3b-2024 (the miso-69 breach) | **[0.124, 0.16]**, projection 0.127-0.138 | MUST be ≤ 0.20 (standing veto). This is the design's decisive read. |
| C3b-2023 | 0.078-0.082; mechanism-only ≤ +0.005 | tier inert in 2023 (window hour $207 < $1,000 Step-2 floor) |
| C3b-2025 | 0.18-0.195; mechanism-only ≤ +0.005 | M-2's own −0.009 improvement carries; tier adds ~0 |
| C3c-2023 (RT 30h) | [0, 3] | M-2's 1h at $207 survives (< $1,000) |
| C3c-2024 (RT 37h) | [4, 10] | the 6 clamped hours print the $500 floor > $200 and stay counted |
| C3c-2025 (RT 88h) | **[1, 8]** | honest: the tier caps, never engages; the $247.7 Jul-28 hour is Alert-only and untouched. The [44,176] RT PASS band is NOT expected to be reached — see §4 on what that does and does not refute. |
| C3a-2024 | −4.5..−6.5% (from main's wrong-shaped −2.0%, mostly reverting toward base −8.0%) | the clamp removes ~0.9-1.2 $/MWh of phantom annual mean |
| C3a-2025 | −13..−14.5% | M-2's −13.7 carries; tier adds ~0 |
| C1 CC_REGULAR-2023 | −8.3 ± 0.1 (unchanged watch) | not this lane's lever |
| C2 / C4 / C5a | PASS both arms; C5a within ±7 | slack energy in clamped hours displaces ≤ ~0.05 TWh of class energy |
| class energy moves | ≤ 0.5 TWh watch (expect ≤ 0.15) | |
| C7 / C8 | PASS, same ST_GAS grounded-above-budget notes; NO new floors | the tier channel carries no floor-mechanism id |
| RDT S→N flows | byte-identical outside Warning+ windows; ≤ 31 window hours may differ | slack changes in-window flows |
| in-window LMP ceiling | every Warning+/Step window-hour zonal LMP ≤ its tier floor + $1 | numerical implementation check |
| DOF | main 24/2, base 21/2 | +1 measured-physical (tier-floor schedule) |

## 4. Refutation criteria (what kills the design, pre-declared)

1. **C3b-2024 composed > 0.20** → REFUTED: the tier floor is not the binding
   declared-window formation element (or the mechanism failed to bound the
   overshoot). The run registers as a REJECTED PROBE and the lane pauses for
   the owner.
2. **C3b mechanism-only (main − base) > +0.005 in 2023 or 2025** → REFUTED as
   window-scoped: the mechanism has a footprint outside its declared windows,
   which is structurally impossible if implemented correctly — treat first as
   an implementation stop-the-line, and as a design refutation only if the
   footprint is real and in-window-caused.
3. **Any Warning+/Step window-hour zonal LMP above its tier floor + $1** →
   implementation defect (stop-the-line, fix before any verdict is read).
4. **C3c-2024 falling BELOW 4** (the clamp erasing tail hours it should keep
   at $500) → implementation defect (the floor prices > $200 by construction).
5. **C3c-2025 remaining ~1h does NOT refute this design** — pre-declared: the
   tier treatment never claimed engagement; it claims correct price formation
   GIVEN engagement. What it leaves open is the pre-named engagement-depth
   question (§1e), which stays un-armed and un-fitted in this lane. Equally,
   C3c-2025 landing in [1,8] must NOT be quoted as tail skill.
6. The composed run's keeper-candidacy is a separate question from the
   design's survival: if every band above holds, the composed stack is
   structurally superior to the keeper (measured derates + documented tier
   pricing, C3b restored inside the veto, C3c-2024 6/37 vs 4/37, C3c-2023
   1/30 vs 0/30) with C3a-2024 expected a few points worse than base but
   PASS — a rule-1 keeper recommendation is made to the owner either way the
   MAE moves, provided no gated criterion regresses from PASS to FAIL.
   Keeper swap is owner-only.

## 5. Implementation freeze (files, seams, tests)

1. `src/market_sim/config/reserve_config.py`: the two cited floor constants
   (§1d) beside `MISO_ZONAL_ORDC_STEPS`, citation comment quoting the SOM
   footnote verbatim.
2. NEW `src/market_sim/data/maxgen_events.py`: the registry loader for
   dispatch-time consumers —
   `emergency_tier_slack_cost(iso, year, zone_names, voll, hours)` →
   `(n_zones, T)` float array or `None` when no Warning+ row overlaps the
   year (key omitted → byte-identical LP). Reads the curated `maxgen-events`
   partition through the frozen `clean_io` seam (auto-curating from raw when
   `data/clean` is absent, the deriver's pattern), converts UTC → naive EST
   (Etc/GMT+5, MISO Tariff Module A), floors starts / ceils ends to the hour
   (a declared 23:59 end-of-day becomes next midnight), maps hours through
   `outages.outage_hour_mask` (no-leap 8760 model clock — hour-exact with
   M-2), levels through the §1c table, regions through the deriver's
   crosswalk, overlaps through min(). Every constant imported, none inlined.
3. `src/market_sim/model/dispatch.py`: `build_cost_vector(...,
   slack_cost=None)` — `None` keeps the flat `voll` broadcast (byte-identical
   path); an `(n_zones, T)` array replaces it per zone-hour.
   `DispatchModel.__init__(..., slack_cost=None)` validates shape and passes
   through. No layout change, no new columns.
4. `src/market_sim/config/scenarios.py`: `maxgen_emergency_tier_pricing:
   bool = False` beside `unit_outage_maxgen_events` with the full driver/
   window/forward-story comment; tier-3 entry in the gated-fields registry.
5. `scripts/run_calibration.py` (the backcast orchestrator only — forecast
   never arms overlays): after `build_base_dispatch_kwargs`, gated
   `dispatch_kwargs.update(slack_cost=...)` when the flag is on and the
   loader returns an array (the `storage_soc_min` precedent). Applies to P0
   and P1 identically (same LP kwargs; P0's trough hours never touch slack).
6. `scripts/legitimacy_diagnostics.py`: D-5 registry entry
   (`maxgen_emergency_tier_pricing`, backcast_only) + the D4_WINDOWS note
   extended — like M-2, the channel carries no floor-mechanism id (it is a
   price-side slack repricing that can never raise `min_gen`); its rule-12
   window declaration is the registry Warning+ window set itself.
7. Tests, NEW `tests/test_maxgen_tier_pricing.py`, trivial case first
   (rule "1 gen, 1 zone, 24 h"): (a) an LP with demand > capacity prices
   slack hours at the tier floor inside a window and at voll outside; (b)
   off-state (`slack_cost=None` / flag off) byte-identity of the cost vector
   and of the loader path; (c) level keying (warning/step1 → 500, step2 →
   1000, advisory/alert → no rows); (d) region scoping (midwest excludes
   MISO-South); (e) min(voll, floor) never raises the cost (a voll below the
   floor is kept); (f) overlap → min floor; (g) no-window year → None; (h)
   the EST no-leap clock places the Aug-26-2024 13:00-20:00 window at model
   hours 5701-5707.

## 6. Execution order (after this freeze)

1. Implement §5, run the new tests + the existing maxgen/dispatch test files.
2. Analytical pre-probe checks (no solve): loader row table printed and
   compared to §1c's five active rows; keeper-payload inertness numbers
   (§2) re-stated in the probe log.
3. Probe `scripts/probes/_miso70_tier_pricing.py` on the `_miso69` pattern
   (strict miso-68 meta replay via `replay_keeper.build_kwargs`; main adds
   `unit_outage_maxgen_events=True` + `maxgen_emergency_tier_pricing=True`
   through `prb_overrides`; base adds nothing), per-year + `--reuse-solved`,
   years sequential, main and base back to back (15 GB box). Rule 22 year
   guard (2023/2024/2025 only) in the script.
4. Reads in §3's order — C3b-2024 first (the decisive read), then the
   window-hour LMP ceiling check, then the rest. Fallbacks/refutations §4
   only; no new fallback invented after reading.
5. Registration chain per parent §6.7 for BOTH runs whatever the verdict
   (rule 15): `dashboard_add_run` → attestation/DOF ledger → legitimacy
   regen (D-5 entry live) → `calibration_verdict --write-metrics` → parity →
   `build_manifest` → calibration-log entry (lead with the dashboard
   result) → push with fetch-back verification (rule 27). Keeper
   recommendation to the owner; no keepers.json edit.

## 7. Non-relitigation (inherited, restated)

Parent §7 in full, plus: miso-69's rejection stands; the M-2 guards are
frozen; the [$120,$200] certificate caveats are recorded facts; no VOLL/ORDC
constant change pre-9/30/2025 (this design touches neither — the slack floor
only lowers the in-window energy cap); no window reconstruction from prices;
no G-23 import work; the Jan-2024 winter tail (0/24 declared-window hours)
stays the winter fuel-security lane's; the D-4 adjudication for
availability-derate channels is settled and this channel adopts the same
no-row-by-construction pattern.
