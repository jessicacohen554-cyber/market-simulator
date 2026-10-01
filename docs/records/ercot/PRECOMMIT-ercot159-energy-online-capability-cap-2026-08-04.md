# PRECOMMIT — ERCOT-159: `ercot_energy_online_capability_cap` (queue item 9, the ERCOT-155 named successor) — the measured online-capability ceiling on the slow-start energy stack, chartered and gated BEFORE any solve

Owner authorization: the ercot-159 session prompt (2026-08-04) authorizes
chartering and executing §5.1 queue item 9, matrix row
`energy_online_capability_cap` (ERCOT `U`). This document is pushed before any
LP is solved; the A/B scorer is pushed before results exist (the ERCOT-158
pattern). Phase-0 census (no LP): `scripts/probes/ercot159_capability_phase0.py`
→ `results/calibration/_ercot159_capability_phase0.json`.

## 0. Scope fence (DO-NOT-REDO, rule 28(a))

This session does NOT re-open, and the mechanism below is none of:

* **The refused offer-dispersion arm** (ERCOT-155, rules 1/13/20): no offer is
  re-priced, no dispersion/slope parameter exists here. The lever is a
  QUANTITY bound.
* **The closed `ercot41/43/106/108` envelope family**
  (`online_capacity_envelope`, cells `R`, adjudicated BISTABLE). Four explicit
  distinctions, each addressed to that family's recorded failure mode:
  1. **Identification.** The envelope reconstructed capability as
     class-share-of-installed tables × a FITTED deliverability coefficient
     (season×decile medians; the ercot43 finding that the pooled median
     collapses the extreme tail). This mechanism carries **zero fitted
     scalars**: the ceiling is the measured conditional ENVELOPE (per-cell
     max) of ERCOT's own telemetered online HSL, from the full-year 60-Day
     SCED corpus, cell-indexed on forward drivers.
  2. **Scope.** The envelope capped the ALL-responsive tier — quick-start CTs
     inside the P-sum and NonSpin inside the R-sum — so binding forced the
     ~10.7 GW ORDC total-reserve span into shortage inside a ceiling sized to
     real dispatch + real headroom (ercot41/43 §7.4: arithmetically guaranteed
     to over-fire; 963/181 tail hours, the whole year repriced). This
     mechanism caps the **FAST tier only**: LHS = P(slow-start fossil +
     nuclear) + R(RegUp/RRS/ECRS). Quick-start CT energy is NOT capped (its
     offline increment is PRICED by the keeper's fast-start pool, ERCOT-158
     cell `K`), and NonSpin is NOT capped (the ORDC total family is all-class,
     so its coverage can shift to NonSpin on quick/offline headroom — the
     escape valve the envelope lacked).
  3. **Ex-ante bistability census.** The envelope's over-fire was discovered
     in-LP. Here the binding arithmetic was measured BEFORE chartering, on the
     keeper's own committed sidecars (§5): the chosen construction binds 667
     hours in 2023 (523 ordinary at shallow p50 1.10 GW depth, 66 of the 91
     missed tail hours at ~2× that depth) — nothing resembling the 3,838-hour
     raw-series bind or the envelope's 963-tail-hour repricing.
  4. **The ERCOT-89 §3(ii) "no-cap" line is consciously superseded** for this
     one mechanism by the item-9 owner authorization (matrix row opened at
     ERCOT-155 naming "an energy-side measured online-capability ceiling";
     the session prompt authorizes it as "a structural LP change"). That line
     bound the shoulder-span design round; it was itself derived from the
     envelope family's failure, whose mechanics are addressed point-by-point
     above.
* **The rejected-as-armed `ercot_shoulder_online_span`** (ERCOT-89): that was
  an offer-GEOMETRY re-anchor (ladder stretched over the conditional online
  span, 2024/2025-scoped). No ladder geometry is touched here.
* **The closed West/Panhandle topology split**, the ercot41/43 §6.1 evaluation
  rule ("degrading the current-design years is a rejection") carries over
  through the gates in §6.

## 1. The two runs (rule 16 full-span; rule 12 memory caveat)

Both runs replay the ercot158 keeper recipe from
`results/calibration/ercot158_poolarm_B` (keeper
`2026-08-03-ercot158-pool-arm`), full-span `--years 2023 2024 2025`, years
sequential within each invocation, and the two invocations SEQUENTIAL (this
box measured ~10 GB RSS per ERCOT plant-level solve at ERCOT-158; rule 12's
cap-2 binds at 1 here).

* **Run A (control):** `scripts/replay_keeper.py results/calibration/ercot158_poolarm_B
  --out-dir results/calibration/ercot159_control_A` — config UNCHANGED, fresh
  out-dir, same HEAD (the ercot150 K2 drift lesson: never score against the
  committed bundle directly; the ercot98 honest-inputs pattern).
* **Run B (arm):** same, plus the single delta
  `--set ercot_energy_online_capability_cap=true
  --out-dir results/calibration/ercot159_cap_B`.

Registration: BOTH runs go on the backcast dashboard this session, whatever
the outcome (rule 15), with attestation + legitimacy diagnostics before
registration.

## 2. Mechanism statement

**New `ScenarioConfig` field `ercot_energy_online_capability_cap`
(default False; path override `ercot_energy_online_capability_cap_path`).**
ERCOT-only, backcast-mode only (see forward story below). Requires
`energy_reserve_coopt` + `ercot_multiproduct_as_coopt` (hard error otherwise —
the fast/all tier split is the identified structure) and is mutually exclusive
with every `online_capacity_envelope` variant flag (they set the same
`ReserveDesign.online_capacity_cap` field; rule 19 one-owner).

**LP form (existing infrastructure, no new row family):** the mechanism
populates `ReserveDesign.online_capacity_cap` — the already-built,
already-vectorized `(n_hr, T)` block in `model/lp/reserve_rows.py` that bounds
per headroom tier `Σ P(eligible) + Σ R(tier products) ≤ cap[h,t]` — with:

* row 0 (fast tier: eligibility = responsive & ~quick = {gas_cc, gas_st,
  coal, nuclear}; products RegUp/RRS/ECRS): the conditional envelope
  `CAP(cell(t))` below;
* row 1 (all tier): the uncapped sentinel (always slack; NonSpin and
  quick-start capability keep their existing bounds — the reserve-supply-cap
  tier at RTOLCAP+RTOFFCAP and the availability headroom).

**The ceiling (frozen derived artifact,
`data/raw/_validation-source/ercot_energy_online_capability_condbinned.json`,
`scripts/data/derive_ercot_energy_online_capability.py`):** per year block,
per cell `(season, hour_block, net_load_bin)`, the **maximum** attained value
of the measured fast-tier capability object

    OLC(t) = Σ online HSL over slow-start fossil SCED types
             (CCGT90/CCLE90/CLLIG/CLLIM/GSREH/GSNONR/GSSUP)
           + Σ online HSL over NUC
           + Σ online (HSL − Base Point) over quick-start types
             (SCGT90/SCLE90/RECIP/DSL)   [quick online HEADROOM]

hourly-meaned from SCED intervals on the fixed-CST 8760 clock (the ERCOT-155
census taxonomy and clock, verbatim: online states ON/ONREG/ONFFRRRS/FRRSUP/
ONRGL/ONOS). The quick-headroom term is there because reality holds part of
its spinning AS on online CTs, capability the LP's fast products cannot reach
(fast-tier eligibility excludes quick units); crediting it keeps the two sides
of the row commensurable. Quick-start ENERGY never enters either side (netted
by Base Point on the measured side, excluded from row-0 eligibility on the
model side).

**Grain (the ERCOT-89 §6 conditional-object standard, verbatim admissible
form):** season ∈ {DJF, MAM, JJAS, ON} × hour-block ∈ {0-5, 6-9, 10-13,
14-16, 17-21, 22-23} × net-load bin on the year's own percentile edges at
deciles 10..90 plus 92/94/96/98 (14 bins — the extreme-tail resolution the
ercot43 rejection identified as mandatory). Net load = system demand − wind −
solar generation, the exact quantity `pipeline/year.py` already threads into
the reserve spec; at solve time the bin is assigned by within-run percentile
rank (self-normalizing, so a forecast year's bins regenerate — the
`_ercot_rtolcap_fwd_decile` pattern). A cell with no measured hours returns
the uncapped sentinel (no envelope evidence → no constraint).

**Statistic (a-priori, not swept):** the per-cell MAX. The mechanism's
semantics are a capability ENVELOPE — "more than this was never mustered at
these conditions" — and the envelope statistic for an attained-capability
bound is the attained maximum. Percentile trims (p95/p98) were computed in
Phase 0 for disclosure (§5) but are rejected a priori as arbitrary trims of
an envelope; hourly means of ~12 SCED intervals already suppress telemetry
spikes. No deliverability coefficient, no margin, no offset exists in the
construction (rule 20).

**Year scoping (by measured coverage, the `ercot_shoulder_online_span`
precedent):** the artifact carries a 2023 block only — the full-year corpus
(315 shards, all 365 delivery days, ERCOT-157) exists for delivery-2023 alone;
2024/2025 have 47 event/control sample day-files, structurally insufficient
for a 336-cell envelope (and their bins would be event-biased). Absent years →
sentinel rows → **byte-inert**. Extension to 2024/2025 requires the item-8a
full-span corpus intake (owner-authorized data work), never a pooled fallback.
The 2024/2025 sample days are used as VALIDATION of the 2023-derived
construction's cross-year stability (reported in the artifact provenance, not
gating).

**Forward story (rule 13 regeneration test):** the mode-aware G4 seam of
`ercot_rtolcap_supply_cap_mw`, exactly: in forecast mode the provider returns
None (uncapped) until a forward-share formula is derived in the forecast lane
(the artifact records, per cell, the envelope's share of the fleet's
availability-derated fast-tier capability alongside the absolute MW, so the
forward formula is derivable without touching this identification). The
matrix row stays mode `B`. The admissibility of the same-year measured
conduct series in backcast follows the wall/pool/DAM-availability precedents:
a conditional distributional object built from measured conduct, keyed on
drivers that regenerate, never the raw hour series (the rule-13 bright line —
Phase 0 measured the raw hour-pin at 3,838 binding hours: the forbidden form
is also the broken form).

## 3. Rule-19 reconciliation (mandatory per the item-9 charter; enumerated BEFORE the seam is written)

One phenomenon per mechanism, explicit precedence, no stacked layer:

* **The DAM availability lane (`ercot_thermal_dam_availability*`, ERCOT-148/149
  event caps) owns OUTAGES** — per-unit availability derates on the generator
  bounds and headroom RHS. This cap owns ONLINE STATE. They cannot
  double-count by construction: the envelope is the max ATTAINED online
  capability at a cell — on outage-depleted days the per-unit availability
  bounds bind BELOW the envelope (the envelope never tightens because of an
  outage; the availability lane never loosens because of the envelope).
  Precedence: both installed; the physically tighter binds.
* **The commitment bridges (`ercot_gas_commitment_bridge`, keeper-armed) own
  the LOWER bound** (min-gen floors detected from the P0 run pattern). This
  cap is their upper-bound counterpart at the P0→P1 seam's other end: P0
  solves WITH the cap, so the bridge detects run patterns from
  capability-consistent dispatch — composition through the existing seam, not
  a stacked floor. Floor totals sit far below the envelope by construction
  (floors ≈ 0.574 × committed-CC ≤ attained dispatch ≤ attained capability ≤
  envelope), so no floor/cap infeasibility exists; VOLL slack remains the LP's
  escape in any pathological hour and is guarded in §6.
* **The reserve supply cap (`ercot_reserve_supply_cap`, keeper-armed) owns the
  RESERVE side** — Σ R ≤ measured RTOLCAP (fast tier) / RTOLCAP+RTOFFCAP (all
  tier). This cap bounds the fast tier's TOTAL capability use (P + R). The two
  are the physically nested pair ERCOT itself operates (procured AS ≤ online
  responsive capability; output + headroom ≤ online HSL) — nesting, not
  stacking: on the reserve-only margin the RTOLCAP cap is the binding
  instrument; on the energy+reserve margin this cap is. Neither replaces the
  other and neither is derived from the other.
* **The fast-start pool (`ercot_faststart_pool_offer`, keeper-armed,
  ERCOT-158) owns the offline-quick PRICE route.** This cap closes the
  phantom slow-online QUANTITY route. Composition is the designed price
  formation: when the cap binds, displaced energy takes the CT route — first
  online-basis CT capability at marginal cost, then the pool's start-inclusive
  measured ladder — and past the CT fleet the squeezed fast reserve families
  price through their reserve-VOLL/ORDC curves. ERCOT-158 measured the pool
  ENGAGED-but-INERT because the un-capped cushion kept it off the margin; this
  is the mechanism that removes the cushion. No row is priced by two
  mechanisms; no quantity is bounded by two mechanisms.
* **The ECRS conservative-deployment mechanism** (keeper-armed, correctly
  dated) is untouched; the ERCOT-155 finding predicts its 1–3 GW withdrawal
  starts moving duals once the 15 GW cushion is capped — an interaction
  through the LP's own arithmetic, not a new coupling.
* **The ORDC total-reserve family** (`ercot_ordc_total`, all-class) is the
  escape valve, not a victim: its coverage can rebuild on NonSpin over
  quick/offline headroom (tier 2, uncapped by this mechanism), so the
  ercot41/43 arithmetic — the total span forced into shortage inside the cap —
  cannot recur.

## 4. Rules 13/20/23 statement

* **Rule 13:** the per-hour telemetered online series is an operational
  OUTCOME; it BUILDS and VALIDATES the conditional object and never ships raw
  (ERCOT-89 §6 bright line, quoted in §2). The conditional object regenerates:
  cells from calendar + within-run net-load percentiles; the backcast levels
  are the measured envelope for the solved year; the forward branch is the G4
  seam (uncapped until its own derivation).
* **Rule 20:** zero fitted scalars. Design choices (max statistic, 4×6×14
  grain, quick-headroom augmentation) are fixed a priori in this document with
  their rationales, before any solve; the Phase-0 variant table is disclosed
  in full (§5) — no variant was selected on a price residual, and no
  post-solve re-selection is permitted: the A/B runs exactly the §2
  construction, and its outcome is adjudicated by §6-§7 as-is.
* **Rule 23:** the derive freezes against residuals; it re-derives only when
  its source data updates (the SCED corpus, the ERCOT-155 census taxonomy
  inputs). Re-derivation commits must cite the data change.
* **Rule 5/24 (registry):** the flag + path are `ScenarioConfig` fields,
  serialized into `run_config.json`; the matrix row def is updated in the same
  PR (rule 28(c) — row exists at `U`).

## 5. Phase-0 census (measured before chartering; the ex-ante bistability check)

On the ercot158 keeper's own committed 2023 sidecars (no LP): model fast-tier
point = P(CC_REGULAR+CC_CHP+COAL_PRB+COAL_LIGNITE+ST_GAS+ST_CHP) + P(nuclear)
+ held(RegUp+RRS+ECRS); measured object per §2. Missed set = the ERCOT-158
Phase-0 split re-derived on the keeper's own prices (91 hours: actual > $300,
model < $200).

| ceiling | binds | ordinary (<$150) | of 181 >$200 | of 91 missed | miss depth p50/p90 GW | ord depth p50/p90 GW |
|---|---|---|---|---|---|---|
| raw hourly series (forbidden form) | 3,838 | 3,615 | 181 | 91 | — | — |
| raw augmented | 3,705 | 3,482 | 181 | 91 | — | — |
| p95 / dec10 grain | 1,002 | 845 | 134 | 67 | 2.65 / 4.37 | 1.29 / 3.33 |
| aug p95 / dec10 | 871 | 723 | 126 | 65 | 2.31 / 4.08 | 1.22 / 3.15 |
| aug p98 / dec10 | 711 | 568 | 125 | 64 | 2.06 / 3.77 | 1.22 / 3.07 |
| aug max / dec10 | 560 | 427 | 116 | 60 | 1.82 / 3.29 | 1.22 / 3.21 |
| **aug max / dec14 (CHOSEN §2)** | **667** | **523** | **122** | **66** | **1.84 / 3.47** | **1.10 / 3.06** |
| aug max / dec14 + weekday | 865 | 715 | 127 | 69 | 1.97 / 3.92 | 1.24 / 3.54 |
| aug p98 / dec14 + n-floor 24 | 844 | 692 | 128 | 67 | 1.96 / 3.78 | 1.10 / 2.95 |

Readings that shape the design (all measured, none fitted):

1. **The raw hour series is the bistable trap** (3,615 ordinary binding
   hours) — the rule-13-forbidden form is also the mechanically broken form.
   The conditional envelope removes ~86 % of ordinary binds while keeping
   ~73 % of the missed tail.
2. **Membership does not fully separate; DEPTH does.** Missed-tail binds run
   ~2× deeper than ordinary binds. The price consequence is graded by the
   model's own supply structure: ordinary binds (p50 1.1 GW) are absorbed by
   the online-basis CT buffer at marginal cost (CT_PEAKER dispatch at
   actual<$150 hours: p50 0.0, p90 2.35 GW — 5-10 GW of mc-priced room);
   missed-hour binds (p50 1.8, p90 3.5 GW) land where the CT fleet is already
   at 4.7-5.2 GW, the pool ladder and the reserve-VOLL families price the
   displacement. A shallow ordinary-hour lift is also structurally faithful:
   the real 2023 carries frequent small RTORPA adders the model never forms
   (model reserve price > $1 in only 54 h).
3. **2023 direction is favorable by construction, not by tuning:** C3a-2023
   sits at −24.5 % (analyzer basis) — capability-tightness repricing moves it
   toward actual from below. The 2024/2025 blocks are byte-inert (§2), so the
   +10.2 % / −0.7 % years carry zero exposure — pre-registered as a
   BIT-IDENTITY expectation, and any 2024/2025 delta is a wiring bug that
   stops the session.
4. Weekday and n-floor variants worsen without a-priori justification
   (thinner cells lower the envelope — the ercot43 collapse direction);
   rejected on that ground, disclosed here.

## 6. Pre-declared gates (scored Run A → Run B, per year, no exceptions)

The four standing ERCOT-89 analyzer gates
(`scripts/probes/_ercot89_span_check.py` semantics, imported not re-coded):

| gate | threshold (per year) |
|---|---|
| C3a level guard | \|resid_B\| ≤ \|resid_A\| + 1.0 pp (annual demand-weighted) |
| Zero-spurious | Δ(hours model ∈ [$150,$500) & actual < $150) ≤ 0 |
| Tail-count not-away | \|h>$200_B − h>$200_act\| ≤ \|h>$200_A − h>$200_act\| |
| NRMSE (C3b proxy) | NRMSE_B ≤ NRMSE_A + 0.005 |

Plus the ERCOT-159-specific pre-registrations (this is a QUANTITY-side
mechanism — D-2/D-4 exposure is NOT vacuous, unlike ERCOT-158):

* **2024/2025 bit-identity:** the artifact has no 2024/2025 block; those
  years' prices and dispatch must be bit-identical A→B. Any delta = wiring
  bug = stop-the-line (no registration of B until resolved).
* **Matched-hour C3c anatomy (2023):** the 91 missed / 53 hit split
  re-derived on Run A's own prices; report missed-set model mean/p50 A→B,
  flips to ≥$300, and `new_tail_outside_actual_KILL` (any new model->$300
  hour whose actual < $300 is a kill).
* **Scorecard holds:** zero PASS→FAIL at criterion grain and at
  per-(criterion, year, key) row grain (captured full verdicts).
* **C1 16/16 and C2 must hold** (the cap shifts class MWh CC→CT within 2023;
  C1/C2 bound how far).
* **C7-2023 legs must not regress** (profile_r / cv_ratio per class-leg —
  the open lignite cv-leg may not worsen, no new leg failures); C7-2024/25
  trivially held by bit-identity.
* **Slack/dump guard:** Σ slack MWh and Σ dump MWh per year, A→B delta within
  +0.1 % of demand (the new upper-bound row must not shed load; 2023 keeper
  baseline slack 3,478.9 MWh).
* **D-2 attribution plan:** the cap introduces NO floor and NO forced energy,
  so no new D-2 mechanism id may appear; the existing
  `gas_commitment_bridge` rows may shift (the bridge detects from capped P0)
  — report the D-2 delta table; forced-TWh deltas > 0.05 TWh on any existing
  mechanism escalate to analysis before registration. D-4: no new windowed
  mechanism is added; the cap has no window to declare (it is an upper bound
  active wherever measured cells exist — its "window" is the artifact's cell
  coverage, disclosed in provenance).

## 7. Decision rule and registration (pre-declared)

* **R (rejected)** if any kill gate fires: C3a/zero-spurious/tail/NRMSE
  breach in 2023, any 2024/2025 non-identity traced to the mechanism (after
  the wiring-bug stop), scorecard PASS→FAIL, C1/C2 break, slack/dump breach,
  or a new-tail-outside-actual hour.
* **I (inert)** if all gates hold and the 2023 missed-set movement is nil
  (missed-set mean delta < $1 and 0 flips — the ERCOT-158 outcome shape).
* **K (keeper-candidate)** if all gates hold and the 2023 tail moves
  materially toward actual: missed-set model mean delta ≥ +$10 or ≥ 5 flips
  to ≥$300, with C3c counts moving toward 181/53/31 and no gate cost beyond
  the stated graces. Promotion itself follows the owner's standing standard
  (structural-integrity-first); the session surfaces the recommendation and
  executes the keeper lane if earned (shard + build_status --iso ERCOT +
  keeper-auditor + matrix header re-stamp; ERCOT holds no `complete` marker —
  no re-key duty).
* **LOYO (rule 24):** genuinely zero fitted parameters (§4), so the per-year
  guard table stands in for leave-one-year-out (the ERCOT-158 precedent);
  2024/2025 are additionally bit-inert by construction.
* Matrix cell `energy_online_capability_cap` (ERCOT) updated with the tested
  verdict + citation in the same session (rule 28(b)); the §5.1 item-9 stale
  corpus clause ("2024/2025 only — no 2023 corpus") corrected to record the
  ERCOT-157 delivery-2023 landing. Log entry `ercot-159` in
  `docs/calibration-log/ercot.md`. Both bundles + sidecars + registry +
  payloads committed and pushed per rule 15.

## 8. Expectation management (stated before any number is seen — rule 1)

The honest uncertainty is the magnitude of 2023 tail formation: the cap
covers 66/91 missed hours at p50 1.8 GW depth; whether the displaced energy
prices at $60 (CT mc), $150-500 (pool ladder), or $1000+ (reserve-VOLL)
depends on the LP's joint state at those hours, and no number here was
computed from a solve. The structurally possible outcomes are: partial tail
closure (K-shaped), engaged-but-shallow (I-shaped — binding but priced at the
CT buffer), or a guard breach from ordinary-hour over-fire (R-shaped — the
bistable failure recurring despite the envelope statistic). All three are
registered outcomes; none licenses a post-hoc re-grain (rule 20; a re-grain
is a new owner-authorized round with new evidence).
